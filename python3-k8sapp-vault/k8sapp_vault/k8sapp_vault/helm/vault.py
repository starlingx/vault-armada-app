#
# Copyright (c) 2020-2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from k8sapp_vault.common import constants as app_constants

from oslo_log import log as logging

from sysinv.common import constants
from sysinv.common import exception

from sysinv.helm import base
from sysinv.helm import common

from sysinv.db import api as dbapi

import yaml

LOG = logging.getLogger(__name__)


class VaultHelm(base.BaseHelm):
    """Class to encapsulate helm operations for the vault chart"""

    class PodNames():
        """Class containing the default pod names"""
        SERVER = app_constants.HELM_VAULT_SERVER_POD
        MANAGER = app_constants.HELM_VAULT_MANAGER_POD
        INJECTOR = app_constants.HELM_VAULT_INJECTOR_POD

    SUPPORTED_NAMESPACES = base.BaseHelm.SUPPORTED_NAMESPACES + \
                           [common.HELM_NS_VAULT]

    SUPPORTED_APP_NAMESPACES = {
        constants.HELM_APP_VAULT:
            base.BaseHelm.SUPPORTED_NAMESPACES + [common.HELM_NS_VAULT],
    }

    SUPPORTED_COMPONENT_OVERRIDES = ['application','platform']
    DEFAULT_AFFINITY = 'platform'
    LABEL_PARAMETER = 'extraLabels'

    def get_namespaces(self):
        return self.SUPPORTED_NAMESPACES

    def get_master_worker_host_count(self):
        controller=len(self.dbapi.ihost_get_by_personality(constants.CONTROLLER))
        worker=len(self.dbapi.ihost_get_by_personality(constants.WORKER))
        return controller+worker

    def get_overrides(self, namespace=None):

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
                self.PodNames.SERVER: {
                    'ha': {
                        'replicas': ha_replicas,
                    },
                    self.LABEL_PARAMETER: {
                        app_constants.HELM_CHART_COMPONENT_LABEL: affinity
                    }
                },
                self.PodNames.INJECTOR: {
                    self.LABEL_PARAMETER: {
                        app_constants.HELM_CHART_COMPONENT_LABEL: affinity
                    }
                },
                self.PodNames.MANAGER: {
                    self.LABEL_PARAMETER: {
                        app_constants.HELM_CHART_COMPONENT_LABEL: affinity
                    }
                },
            }
        }

        if namespace in self.SUPPORTED_NAMESPACES:
            return overrides[namespace]
        elif namespace:
            raise exception.InvalidHelmNamespace(chart=self.CHART,
                                                 namespace=namespace)
        else:
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

            if type(helm_overrides) == str:
                helm_overrides = yaml.safe_load(helm_overrides)
        except exception.HelmOverrideNotFound:
            LOG.debug("Overrides for this chart not found, nothing to be done.")
        return helm_overrides
