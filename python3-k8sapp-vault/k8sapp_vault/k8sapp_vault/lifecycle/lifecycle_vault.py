#
# Copyright (c) 2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# All Rights Reserved.
#

""" System inventory App lifecycle operator."""

from base64 import b64encode
import json
from k8sapp_vault.common import constants as app_constants
from oslo_log import log as logging
from sysinv.common import constants
from sysinv.common import kubernetes
from sysinv.common import utils as cutils
from sysinv.helm import lifecycle_base as base
from sysinv.helm.lifecycle_constants import LifecycleConstants
import time

LOG = logging.getLogger(__name__)

CONF = kubernetes.KUBERNETES_ADMIN_CONF
NS = app_constants.HELM_CHART_NS_VAULT

# wait parameters for kubernetes secret creation
WAIT_INTERVAL = 1  # seconds
WAIT_COUNT = 10


class VaultAppLifecycleOperator(base.AppLifecycleOperator):
    """Lifecycle operator for vault application"""

    def app_lifecycle_actions(self, context, conductor_obj, app_op, app, hook_info):
        """Perform lifecycle actions for an operation

        :param context: request context, can be None
        :param conductor_obj: conductor object, can be None
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        :param hook_info: LifecycleHookInfo object

        """
        if (hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE
                and hook_info.operation == constants.APP_APPLY_OP
                and hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE):
            try:
                self.read_pvc_secret(app_op._kube._get_kubernetesclient_core())
            except Exception:  # nosec # pylint: disable=broad-exception-caught
                # omit printing all exceptions in case any may
                # contain secret data
                pass

        super().app_lifecycle_actions(context, conductor_obj, app_op,
                                      app, hook_info)

    def validate_document(self, jdoc):
        """Check whether the keyshards json is expected"""
        error = False

        if not isinstance(jdoc, dict):
            LOG.error("document is not dict type")
            return False
        if not len(jdoc) == 3:
            LOG.error("document is not length 3")
            error = True

        if 'keys' not in jdoc.keys():
            LOG.error("keys not in document")
            error = True
        elif not isinstance(jdoc['keys'], list):
            LOG.error("keys is not list type")
            error = True
        elif not len(jdoc['keys']) == app_constants.KEYSHARDS:
            LOG.error("len(keys) not expected")
            error = True

        if 'keys_base64' not in jdoc.keys():
            LOG.error("keys_base64 not in document")
            error = True
        elif not isinstance(jdoc['keys_base64'], list):
            LOG.error("keys_base64 is not list type")
            error = True
        elif not len(jdoc['keys_base64']) == app_constants.KEYSHARDS:
            LOG.error("len(keys_base64) not expected")
            error = True

        if 'root_token' not in jdoc.keys():
            LOG.error("root_token not in document")
            error = True
        elif not isinstance(jdoc['root_token'], str):
            LOG.error("root_token not str type")
            error = True

        return not error

    def ns_exists(self):
        """check if vault is listed in namespaces"""
        jsonpath = '{.items[*].metadata.name}'
        cmd = ['kubectl', '--kubeconfig', CONF,
               'get', 'ns', '-o', 'jsonpath=' + jsonpath]
        stdout, stderr = cutils.trycmd(*cmd)
        if not stdout:
            LOG.info('Failed to get namespaces [%s]', stderr)
            return False
        if NS not in stdout.split():
            LOG.info('No vault namespace')
            return False
        return True

    def get_pod_list(self):
        """Get all pods in vault ns"""

        if not self.ns_exists():
            return []

        jsonpath = '{.items[*].metadata.name}'
        cmd = ['kubectl', '--kubeconfig', CONF,
               'get', 'pods', '-n', NS,
               '-o', 'jsonpath=' + jsonpath]
        stdout, stderr = cutils.trycmd(*cmd)
        if not stdout:
            LOG.info('No pods in vault namespace: [%s]', stderr)
            return []

        return stdout.split()

    def get_manager_pods(self):
        """Get all pods named sva-vault-manager"""

        managers = []
        pods = self.get_pod_list()
        for pod in pods:
            if pod.startswith('sva-vault-manager'):
                managers.append(pod)
        if not managers:
            LOG.info('failed to get vault-manager pod')
            return []
        return managers

    def get_manager_pod(self):
        """Return pod name if it has PVC mounted"""
        pods = self.get_manager_pods()

        # assert that the vault-manager pod has PVC mounted
        managerpod = ''
        cspec = ".spec.containers[?(@.name=='manager')]"
        vspec = "volumeMounts[?(@.name=='manager-pvc')].name"
        jsonpath = "{%s.%s}" % (cspec, vspec)
        for pod in pods:
            cmd = ['kubectl', '--kubeconfig', CONF,
                   'get', 'pods', '-n', NS, pod, '-o',
                   'jsonpath=' + jsonpath]
            stdout, stderr = cutils.trycmd(*cmd)
            if stderr or not stdout:
                LOG.debug('vault-manager pod without PVC mounted'
                          '[%s]', stderr)
                continue
            if managerpod:
                LOG.info('More than one vault-manager pod with PVC mounted'
                         '[%s] and [%s]', managerpod, pod)
            managerpod = pod
            LOG.info('vault-manager pod with PVC mounted:'
                     '[%s]', managerpod)
        return managerpod

    def get_key_shards(self, podname):
        """Read the key shards from vault-manager pod"""

        cmd = ['kubectl', 'exec', '-n', NS, podname,
               '--kubeconfig', CONF,
               '--', 'cat', '/mnt/data/cluster_keys.json']
        stdout, stderr = cutils.trycmd(*cmd)
        if stderr or not stdout:
            LOG.info('cluster keys missing from PVC storage')
            return ''
        return stdout.strip()

    def create_secret(self, client, shards):
        """create a secret from shards text"""
        metadata = {'name': 'cluster-key-bootstrap'}
        data = {'strdata': shards}
        body = {'apiVersion': 'v1',
                'metadata': metadata,
                'data': data,
                'kind': 'Secret'}
        try:
            api_response = client.create_namespaced_secret(NS, body)
        except kubernetes.client.exceptions.ApiException:
            # omitting printing the exception text in case it may
            # contain the secrets content
            LOG.error('Failed to create bootstrap secret '
                      '(ApiException)')
            return False

        # verify that the api response contains the secret
        if ('data' in dir(api_response)
                and 'strdata' in api_response.data
                and api_response.data['strdata'] == shards):
            LOG.info('API response includes correct data')
        else:
            LOG.error('Failed to verify kubernetes api response')

        # Ignore the above verification and continue
        return True

    def read_pvc_secret(self, client):
        """Retrieve key shards from a running vault-manager pod

        The key shards are stored into k8s secrete
        'cluster-key-bootstrap', to be consumed by the new vault-manager
        pod.  The vault-manager will also delete the PVC resource after
        successful validations.

        Do nothing if:
         - no vault-manager pod is running with PVC attached (i.e.: no
           namespace, no pod. no vault-manager or no PVC attached)
         - PVC does not contain the expected key shards file
         - key shards data is not in an expected format (data structure,
           number of key shards

        Print only soft errors if the validation of stored k8s secret
        is not successful.
        """

        podname = self.get_manager_pod()
        if not podname:
            LOG.info('No vault-manager with PVC mounted')
            return

        keyshards = self.get_key_shards(podname)
        if not keyshards:
            # an error is printed
            return

        # using encode()/decode() because b64encode requires bytes, but
        # kubernetes api requires str
        b64_keyshards = b64encode(keyshards.encode()).decode()

        # assert that it's a json document with expected keys
        try:
            document = json.loads(keyshards)
        except json.decoder.JSONDecodeError:
            LOG.error("Failed to parse json document")
            return

        if self.validate_document(document):
            LOG.info("Successfully retrieved %s key shards",
                     len(document['keys']))
        else:
            LOG.error('The data appears invalid')
            return

        if not self.create_secret(client, b64_keyshards):
            # an error is already printed
            return

        # read the secret back
        LOG.info('Wait for the secret to be created')
        count = WAIT_COUNT
        while count > 0:
            # read the secret back
            jsonpath = "{.data.strdata}"
            cmd = ['kubectl', '--kubeconfig', CONF,
                   'get', 'secrets', '-n', NS, 'cluster-key-bootstrap',
                   '-o', 'jsonpath=' + jsonpath]
            stdout, stderr = cutils.trycmd(*cmd)
            if stdout and b64_keyshards == stdout:
                break
            LOG.debug('Result kubectl get secret '
                      'cluster-key-bootstrap: [%s]', stderr)
            count -= 1
            time.sleep(WAIT_INTERVAL)

        if b64_keyshards == stdout:
            LOG.info('Validation of stored key shards successful')
        else:
            LOG.error('Validation of stored key shards failed')
