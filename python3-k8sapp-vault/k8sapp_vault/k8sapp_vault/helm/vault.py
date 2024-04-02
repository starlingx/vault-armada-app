#
# Copyright (c) 2020-2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

"""Application helm class"""

from k8sapp_vault.common import constants as app_constants

from oslo_log import log as logging

from sysinv.common import constants
from sysinv.common import exception
from sysinv.common import kubernetes

from sysinv.helm import base
from sysinv.helm import common

from sysinv.db import api as dbapi

import yaml

LOG = logging.getLogger(__name__)


class VaultHelm(base.FluxCDBaseHelm):
    """Class to encapsulate helm operations for the vault chart"""

    SUPPORTED_NAMESPACES = base.BaseHelm.SUPPORTED_NAMESPACES + \
        [common.HELM_NS_VAULT]

    SUPPORTED_APP_NAMESPACES = {
        constants.HELM_APP_VAULT:
            base.BaseHelm.SUPPORTED_NAMESPACES + [common.HELM_NS_VAULT],
    }

    SUPPORTED_COMPONENT_OVERRIDES = ['application', 'platform']
    DEFAULT_AFFINITY = 'platform'
    LABEL_PARAMETER = 'extraLabels'

    CHART = app_constants.HELM_CHART_VAULT
    HELM_RELEASE = app_constants.HELM_RELEASE_VAULT

    def get_namespaces(self):
        """Return the list of supported namespaces"""
        return self.SUPPORTED_NAMESPACES

    def get_master_worker_host_count(self):
        """Read the number of nodes with worker function"""
        controller = len(self.dbapi.ihost_get_by_personality(constants.CONTROLLER))
        worker = len(self.dbapi.ihost_get_by_personality(constants.WORKER))
        return controller + worker

    def get_overrides(self, namespace=None):
        """Return the system overrides"""
        if self.get_master_worker_host_count() >= 3:
            ha_replicas = 3
        else:
            ha_replicas = 1

        dbapi_instance = dbapi.get_instance()

        db_app = dbapi_instance.kube_app_get(app_constants.HELM_APP_VAULT)

        # User chart overrides
        new_chart_overrides = self._get_helm_overrides(
            dbapi_instance,
            db_app,
            app_constants.HELM_CHART_VAULT,
            app_constants.HELM_CHART_NS_VAULT,
            'user_overrides')

        k8s_version = ""

        try:
            kube = kubernetes.KubeOperator()
            k8s_version = kube.kube_get_kubernetes_version()
        except exception.KubeNotConfigured:
            # Do not check for psp override if kubernetes is not configured yet
            pass

        if (k8s_version >= "v1.25.1"
                and new_chart_overrides
                and "global" in new_chart_overrides.keys()
                and "psp" in new_chart_overrides["global"].keys()
                and "enable" in new_chart_overrides["global"]["psp"].keys()
                and new_chart_overrides["global"]["psp"]["enable"] is True):
            LOG.info("PSP must be disabled for kubernetes version 1.25 and onwards, "
                        "as the feature is depreciated. User helm override will be changed "
                        "so that global.psp.enabled is false")
            new_chart_overrides["global"]["psp"]["enable"] = False
            self._update_helm_overrides(
                dbapi_instance,
                db_app,
                app_constants.HELM_CHART_VAULT,
                app_constants.HELM_CHART_NS_VAULT,
                'user_overrides',
                new_chart_overrides
            )

        user_chosen_affinity = new_chart_overrides.get(
            app_constants.HELM_CHART_COMPONENT_LABEL) \
            if new_chart_overrides else None

        if user_chosen_affinity in self.SUPPORTED_COMPONENT_OVERRIDES:
            affinity = user_chosen_affinity
        else:
            affinity = self.DEFAULT_AFFINITY
            LOG.warn((f'User override for core affinity {user_chosen_affinity} '
                      f'is invalid, using default of {self.DEFAULT_AFFINITY}'))

        overrides = {
            common.HELM_NS_VAULT: {
                app_constants.HELM_VAULT_SERVER_POD: {
                    'ha': {
                        'replicas': ha_replicas,
                    },
                    self.LABEL_PARAMETER: {
                        app_constants.HELM_CHART_COMPONENT_LABEL: affinity
                    }
                },
                app_constants.HELM_VAULT_INJECTOR_POD: {
                    self.LABEL_PARAMETER: {
                        app_constants.HELM_CHART_COMPONENT_LABEL: affinity
                    }
                },
            }
        }

        if namespace in self.SUPPORTED_NAMESPACES:
            return overrides[namespace]
        if namespace:
            raise exception.InvalidHelmNamespace(chart=self.CHART,
                                                 namespace=namespace)
        return overrides

    @staticmethod
    def _get_helm_overrides(dbapi_instance, app, chart, namespace,
                            type_of_overrides):
        """Helper function for querying helm overrides from db."""
        helm_overrides = {}
        try:
            helm_overrides = dbapi_instance.helm_override_get(
                app_id=app.id,
                name=chart,
                namespace=namespace,
            )[type_of_overrides]

            if isinstance(helm_overrides, str):
                helm_overrides = yaml.safe_load(helm_overrides)
        except exception.HelmOverrideNotFound:
            LOG.debug("Overrides for this chart not found, nothing to be done.")
        return helm_overrides

    @staticmethod
    def _update_helm_overrides(dbapi_instance, app, chart, namespace,
                            type_of_overrides, value):
        """Helper function for updating helm overrides to db."""
        helm_overrides = {type_of_overrides: yaml.safe_dump(value)}
        dbapi_instance.helm_override_update(
            app_id=app.id,
            name=chart,
            namespace=namespace,
            values=helm_overrides
        )
