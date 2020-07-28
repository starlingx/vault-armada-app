#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# All Rights Reserved.
#

""" System inventory Armada manifest operator."""

from k8sapp_vault.helm.rbd_provisioner import VaultHelm
from k8sapp_vault.helm.psp_rolebinding import PSPRolebindingHelm

from sysinv.common import constants
from sysinv.helm import manifest_base as base


class VaultArmadaManifestOperator(base.ArmadaManifestOperator):

    APP = constants.HELM_APP_VAULT
    ARMADA_MANIFEST = 'armada-manifest'

    CHART_GROUP_PSP_ROLEBINDING = 'vault-psp-rolebinding'
    CHART_GROUP_VAULT = 'vault'
    CHART_GROUPS_LUT = {
        PSPRolebindingHelm.CHART: CHART_GROUP_PSP_ROLEBINDING,
        VaultHelm.CHART: CHART_GROUP_VAULT
    }

    CHARTS_LUT = {
        PSPRolebindingHelm.CHART: 'vault-psp-rolebinding',
        Vault.CHART: 'vault'
    }

    def platform_mode_manifest_updates(self, dbapi, mode):
        """ Update the application manifest based on the platform

        :param dbapi: DB api object
        :param mode: mode to control how to apply the application manifest
        """
        pass
