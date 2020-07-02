#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from k8sapp_vault.common import constants as app_constants

from sysinv.common import constants
from sysinv.common import exception

from sysinv.helm import base
from sysinv.helm import common


class VaultHelm(base.BaseHelm):
    """Class to encapsulate helm operations for the vault chart"""

    SUPPORTED_NAMESPACES = base.BaseHelm.SUPPORTED_NAMESPACES + \
        [common.HELM_NS_VAULT]
    SUPPORTED_APP_NAMESPACES = {
        constants.HELM_APP_VAULT:
            base.BaseHelm.SUPPORTED_NAMESPACES + [common.HELM_NS_VAULT],
    }

    CHART = app_constants.HELM_CHART_VAULT

    SERVICE_NAME = 'vault'

    def get_namespaces(self):
        return self.SUPPORTED_NAMESPACES

    def get_overrides(self, namespace=None):

        overrides = {
            common.HELM_NS_VAULT: {
                'server': {
                    'ha': {
                        'replicas': max(1, self._num_provisioned_controllers()),
                    },
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
