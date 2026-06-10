#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for k8sapp_vault common/constants.py"""

import unittest

from k8sapp_vault.common import constants as app_constants


class TestConstants(unittest.TestCase):
    """Tests for common/constants.py"""

    def test_helm_app_vault(self):
        self.assertEqual(app_constants.HELM_APP_VAULT, 'vault')

    def test_helm_chart_vault(self):
        self.assertEqual(app_constants.HELM_CHART_VAULT, 'vault')

    def test_helm_release_vault(self):
        self.assertEqual(app_constants.HELM_RELEASE_VAULT, 'sva-vault')

    def test_helm_chart_vault_manager(self):
        self.assertEqual(app_constants.HELM_CHART_VAULT_MANAGER,
                         'vault-manager')

    def test_helm_release_vault_manager(self):
        self.assertEqual(app_constants.HELM_RELEASE_VAULT_MANAGER,
                         'sva-vault-manager')

    def test_helm_chart_ns_vault(self):
        self.assertEqual(app_constants.HELM_CHART_NS_VAULT, 'vault')

    def test_helm_server_pod(self):
        self.assertEqual(app_constants.HELM_VAULT_SERVER_POD, 'server')

    def test_helm_manager_pod(self):
        self.assertEqual(app_constants.HELM_VAULT_MANAGER_POD, 'manager')

    def test_helm_injector_pod(self):
        self.assertEqual(app_constants.HELM_VAULT_INJECTOR_POD, 'injector')

    def test_component_label(self):
        self.assertEqual(app_constants.HELM_CHART_COMPONENT_LABEL,
                         'app.starlingx.io/component')

    def test_keyshards(self):
        self.assertEqual(app_constants.KEYSHARDS, 5)
