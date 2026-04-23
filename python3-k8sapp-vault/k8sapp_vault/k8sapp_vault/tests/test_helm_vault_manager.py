#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for k8sapp_vault VaultManagerHelm overrides."""

import unittest
from unittest import mock

from k8sapp_vault.common import constants as app_constants


class TestVaultManagerHelmOverrides(unittest.TestCase):
    """Tests for VaultManagerHelm.get_overrides"""

    def setUp(self):
        from k8sapp_vault.helm import vault_manager
        self.mod = vault_manager
        self.cls = vault_manager.VaultManagerHelm
        self.obj = vault_manager.VaultManagerHelm.__new__(
            vault_manager.VaultManagerHelm)
        self._dbapi_patcher = mock.patch.object(
            type(self.obj), 'dbapi',
            new_callable=mock.PropertyMock,
            return_value=mock.MagicMock())
        self.mock_dbapi_prop = self._dbapi_patcher.start()

    def tearDown(self):
        self._dbapi_patcher.stop()

    @mock.patch('k8sapp_vault.helm.vault_manager.dbapi')
    def test_get_overrides_ha(self, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1, 2], [1, 2]
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        result = self.obj.get_overrides(
            namespace=self.mod.common.HELM_NS_VAULT)
        self.assertEqual(
            result['server']['ha']['replicas'], 3)

    @mock.patch('k8sapp_vault.helm.vault_manager.dbapi')
    def test_get_overrides_single(self, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        result = self.obj.get_overrides(
            namespace=self.mod.common.HELM_NS_VAULT)
        self.assertEqual(
            result['server']['ha']['replicas'], 1)

    @mock.patch('k8sapp_vault.helm.vault_manager.dbapi')
    def test_get_overrides_invalid_ns(self, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        self.assertRaises(
            self.mod.exception.InvalidHelmNamespace,
            self.obj.get_overrides, namespace='bad')

    @mock.patch('k8sapp_vault.helm.vault_manager.dbapi')
    def test_get_overrides_no_ns(self, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        result = self.obj.get_overrides(namespace=None)
        self.assertIn(self.mod.common.HELM_NS_VAULT, result)

    @mock.patch('k8sapp_vault.helm.vault_manager.dbapi')
    def test_get_overrides_affinity_application(self, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        overrides = {
            app_constants.HELM_CHART_COMPONENT_LABEL: 'application'
        }
        db.helm_override_get.return_value = {
            'user_overrides': overrides
        }
        result = self.obj.get_overrides(
            namespace=self.mod.common.HELM_NS_VAULT)
        label = app_constants.HELM_CHART_COMPONENT_LABEL
        self.assertEqual(
            result['manager']['extraLabels'][label],
            'application')

    def test_get_namespaces(self):
        result = self.obj.get_namespaces()
        self.assertIn(self.mod.common.HELM_NS_VAULT, result)

    def test_chart_constant(self):
        self.assertEqual(self.cls.CHART,
                         app_constants.HELM_CHART_VAULT_MANAGER)

    def test_execute_kustomize_updates_disabled(self):
        operator = mock.MagicMock()
        with mock.patch.object(
            self.obj, '_is_enabled', return_value=False
        ):
            self.obj.execute_kustomize_updates(operator)
            operator.helm_release_resource_delete.assert_called_once()

    def test_execute_kustomize_updates_enabled(self):
        operator = mock.MagicMock()
        with mock.patch.object(
            self.obj, '_is_enabled', return_value=True
        ):
            self.obj.execute_kustomize_updates(operator)
            operator.helm_release_resource_delete.assert_not_called()


class TestVaultManagerGetHelmOverrides(unittest.TestCase):
    """Tests for VaultManagerHelm._get_helm_overrides"""

    def test_get_helm_overrides_not_found(self):
        from k8sapp_vault.helm import vault_manager
        db = mock.MagicMock()
        app = mock.MagicMock()
        app.id = 1
        db.helm_override_get.side_effect = \
            vault_manager.exception.HelmOverrideNotFound(
                name='chart', namespace='ns')
        result = vault_manager.VaultManagerHelm._get_helm_overrides(
            db, app, 'chart', 'ns', 'user_overrides')
        self.assertEqual(result, {})
