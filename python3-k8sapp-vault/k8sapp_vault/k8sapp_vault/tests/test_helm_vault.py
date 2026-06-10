#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for k8sapp_vault VaultHelm overrides."""

import unittest
from unittest import mock

from k8sapp_vault.common import constants as app_constants


class TestVaultHelmGetOverrides(unittest.TestCase):
    """Tests for VaultHelm.get_overrides"""

    def setUp(self):
        from k8sapp_vault.helm import vault
        self.mod = vault
        self.cls = vault.VaultHelm
        self.obj = vault.VaultHelm.__new__(vault.VaultHelm)
        self._dbapi_patcher = mock.patch.object(
            type(self.obj), 'dbapi',
            new_callable=mock.PropertyMock,
            return_value=mock.MagicMock())
        self.mock_dbapi_prop = self._dbapi_patcher.start()

    def tearDown(self):
        self._dbapi_patcher.stop()

    @mock.patch('k8sapp_vault.helm.vault.dbapi')
    @mock.patch('k8sapp_vault.helm.vault.kubernetes')
    def test_get_overrides_ha(self, mock_k8s, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1, 2], [1, 2]
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        mock_k8s.KubeOperator.return_value.kube_get_kubernetes_version\
            .return_value = "v1.24.0"
        result = self.obj.get_overrides(
            namespace=self.mod.common.HELM_NS_VAULT)
        self.assertEqual(
            result['server']['ha']['replicas'], 3)

    @mock.patch('k8sapp_vault.helm.vault.dbapi')
    @mock.patch('k8sapp_vault.helm.vault.kubernetes')
    def test_get_overrides_single(self, mock_k8s, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        mock_k8s.KubeOperator.return_value.kube_get_kubernetes_version\
            .return_value = "v1.24.0"
        result = self.obj.get_overrides(
            namespace=self.mod.common.HELM_NS_VAULT)
        self.assertEqual(
            result['server']['ha']['replicas'], 1)

    @mock.patch('k8sapp_vault.helm.vault.dbapi')
    @mock.patch('k8sapp_vault.helm.vault.kubernetes')
    def test_get_overrides_psp_disable(self, mock_k8s, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        overrides = {
            'global': {'psp': {'enable': True}},
            app_constants.HELM_CHART_COMPONENT_LABEL: 'platform'
        }
        db.helm_override_get.return_value = {
            'user_overrides': overrides
        }
        mock_k8s.KubeOperator.return_value.kube_get_kubernetes_version\
            .return_value = "v1.25.1"
        self.obj.get_overrides(
            namespace=self.mod.common.HELM_NS_VAULT)
        self.assertFalse(
            overrides['global']['psp']['enable'])

    @mock.patch('k8sapp_vault.helm.vault.dbapi')
    @mock.patch('k8sapp_vault.helm.vault.kubernetes')
    def test_get_overrides_kube_not_configured(
            self, mock_k8s, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        mock_k8s.KubeOperator.side_effect = \
            self.mod.exception.KubeNotConfigured()
        result = self.obj.get_overrides(
            namespace=self.mod.common.HELM_NS_VAULT)
        self.assertIn('server', result)

    @mock.patch('k8sapp_vault.helm.vault.dbapi')
    @mock.patch('k8sapp_vault.helm.vault.kubernetes')
    def test_get_overrides_invalid_namespace(
            self, mock_k8s, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        mock_k8s.KubeOperator.return_value.kube_get_kubernetes_version\
            .return_value = "v1.24.0"
        self.assertRaises(
            self.mod.exception.InvalidHelmNamespace,
            self.obj.get_overrides, namespace='bad-ns')

    @mock.patch('k8sapp_vault.helm.vault.dbapi')
    @mock.patch('k8sapp_vault.helm.vault.kubernetes')
    def test_get_overrides_no_namespace(
            self, mock_k8s, mock_dbapi):
        self.obj.dbapi.ihost_get_by_personality.side_effect = [
            [1], []
        ]
        mock_dbapi.get_instance.return_value = mock.MagicMock()
        db = mock_dbapi.get_instance.return_value
        db.kube_app_get.return_value = mock.MagicMock()
        db.helm_override_get.return_value = {
            'user_overrides': None
        }
        mock_k8s.KubeOperator.return_value.kube_get_kubernetes_version\
            .return_value = "v1.24.0"
        result = self.obj.get_overrides(namespace=None)
        self.assertIn(self.mod.common.HELM_NS_VAULT, result)

    @mock.patch('k8sapp_vault.helm.vault.dbapi')
    @mock.patch('k8sapp_vault.helm.vault.kubernetes')
    def test_get_overrides_affinity_application(
            self, mock_k8s, mock_dbapi):
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
        mock_k8s.KubeOperator.return_value.kube_get_kubernetes_version\
            .return_value = "v1.24.0"
        result = self.obj.get_overrides(
            namespace=self.mod.common.HELM_NS_VAULT)
        label = app_constants.HELM_CHART_COMPONENT_LABEL
        self.assertEqual(
            result['injector']['extraLabels'][label],
            'application')

    def test_get_namespaces(self):
        result = self.obj.get_namespaces()
        self.assertIn(self.mod.common.HELM_NS_VAULT, result)

    def test_chart_constant(self):
        self.assertEqual(self.cls.CHART,
                         app_constants.HELM_CHART_VAULT)

    def test_helm_release_constant(self):
        self.assertEqual(self.cls.HELM_RELEASE,
                         app_constants.HELM_RELEASE_VAULT)


class TestHelmOverrideHelpers(unittest.TestCase):
    """Tests for static _get_helm_overrides and _update_helm_overrides"""

    def test_get_helm_overrides_success(self):
        from k8sapp_vault.helm import vault
        db = mock.MagicMock()
        app = mock.MagicMock()
        app.id = 1
        db.helm_override_get.return_value = {
            'user_overrides': {'key': 'val'}
        }
        result = vault.VaultHelm._get_helm_overrides(
            db, app, 'chart', 'ns', 'user_overrides')
        self.assertEqual(result, {'key': 'val'})

    def test_get_helm_overrides_string(self):
        from k8sapp_vault.helm import vault
        db = mock.MagicMock()
        app = mock.MagicMock()
        app.id = 1
        db.helm_override_get.return_value = {
            'user_overrides': 'key: val'
        }
        result = vault.VaultHelm._get_helm_overrides(
            db, app, 'chart', 'ns', 'user_overrides')
        self.assertEqual(result, {'key': 'val'})

    def test_get_helm_overrides_not_found(self):
        from k8sapp_vault.helm import vault
        db = mock.MagicMock()
        app = mock.MagicMock()
        app.id = 1
        db.helm_override_get.side_effect = \
            vault.exception.HelmOverrideNotFound(
                name='chart', namespace='ns')
        result = vault.VaultHelm._get_helm_overrides(
            db, app, 'chart', 'ns', 'user_overrides')
        self.assertEqual(result, {})

    def test_update_helm_overrides(self):
        from k8sapp_vault.helm import vault
        db = mock.MagicMock()
        app = mock.MagicMock()
        app.id = 1
        vault.VaultHelm._update_helm_overrides(
            db, app, 'chart', 'ns', 'user_overrides',
            {'key': 'val'})
        db.helm_override_update.assert_called_once()
