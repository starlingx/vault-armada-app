#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for k8sapp_vault lifecycle actions."""

import json
import unittest
from base64 import b64encode
from unittest import mock


class TestValidateDocument(unittest.TestCase):
    """Tests for VaultAppLifecycleOperator.validate_document"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.mod = lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    def _valid_doc(self):
        return {
            'keys': ['k1', 'k2', 'k3', 'k4', 'k5'],
            'keys_base64': ['b1', 'b2', 'b3', 'b4', 'b5'],
            'root_token': 'tok123'
        }

    def test_valid_document(self):
        self.assertTrue(self.op.validate_document(self._valid_doc()))

    def test_not_dict(self):
        self.assertFalse(self.op.validate_document("string"))

    def test_wrong_length(self):
        doc = self._valid_doc()
        doc['extra'] = 'field'
        self.assertFalse(self.op.validate_document(doc))

    def test_missing_keys(self):
        doc = self._valid_doc()
        del doc['keys']
        self.assertFalse(self.op.validate_document(doc))

    def test_keys_not_list(self):
        doc = self._valid_doc()
        doc['keys'] = 'notlist'
        self.assertFalse(self.op.validate_document(doc))

    def test_keys_wrong_count(self):
        doc = self._valid_doc()
        doc['keys'] = ['k1', 'k2']
        self.assertFalse(self.op.validate_document(doc))

    def test_missing_keys_base64(self):
        doc = self._valid_doc()
        del doc['keys_base64']
        self.assertFalse(self.op.validate_document(doc))

    def test_keys_base64_not_list(self):
        doc = self._valid_doc()
        doc['keys_base64'] = 'notlist'
        self.assertFalse(self.op.validate_document(doc))

    def test_keys_base64_wrong_count(self):
        doc = self._valid_doc()
        doc['keys_base64'] = ['b1']
        self.assertFalse(self.op.validate_document(doc))

    def test_missing_root_token(self):
        doc = self._valid_doc()
        del doc['root_token']
        self.assertFalse(self.op.validate_document(doc))

    def test_root_token_not_str(self):
        doc = self._valid_doc()
        doc['root_token'] = 123
        self.assertFalse(self.op.validate_document(doc))


class TestNsExists(unittest.TestCase):
    """Tests for VaultAppLifecycleOperator.ns_exists"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.mod = lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_ns_exists_true(self, mock_cutils):
        mock_cutils.trycmd.return_value = ('default kube-system vault', '')
        self.assertTrue(self.op.ns_exists())

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_ns_exists_false_not_listed(self, mock_cutils):
        mock_cutils.trycmd.return_value = ('default kube-system', '')
        self.assertFalse(self.op.ns_exists())

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_ns_exists_no_stdout(self, mock_cutils):
        mock_cutils.trycmd.return_value = ('', 'error')
        self.assertFalse(self.op.ns_exists())


class TestGetPodList(unittest.TestCase):
    """Tests for VaultAppLifecycleOperator.get_pod_list"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.mod = lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_pod_list_success(self, mock_cutils):
        mock_cutils.trycmd.return_value = (
            'default kube-system vault', '')
        # ns_exists needs to return True first
        with mock.patch.object(self.op, 'ns_exists', return_value=True):
            mock_cutils.trycmd.return_value = ('pod1 pod2', '')
            result = self.op.get_pod_list()
            self.assertEqual(result, ['pod1', 'pod2'])

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_pod_list_no_ns(self, mock_cutils):
        with mock.patch.object(self.op, 'ns_exists', return_value=False):
            result = self.op.get_pod_list()
            self.assertEqual(result, [])

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_pod_list_no_pods(self, mock_cutils):
        with mock.patch.object(self.op, 'ns_exists', return_value=True):
            mock_cutils.trycmd.return_value = ('', 'no pods')
            result = self.op.get_pod_list()
            self.assertEqual(result, [])


class TestGetManagerPods(unittest.TestCase):
    """Tests for get_manager_pods"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    def test_get_manager_pods_found(self):
        with mock.patch.object(
            self.op, 'get_pod_list',
            return_value=['sva-vault-manager-abc', 'sva-vault-0']
        ):
            result = self.op.get_manager_pods()
            self.assertEqual(result, ['sva-vault-manager-abc'])

    def test_get_manager_pods_none(self):
        with mock.patch.object(
            self.op, 'get_pod_list', return_value=['sva-vault-0']
        ):
            result = self.op.get_manager_pods()
            self.assertEqual(result, [])


class TestGetManagerPod(unittest.TestCase):
    """Tests for get_manager_pod"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.mod = lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_manager_pod_with_pvc(self, mock_cutils):
        with mock.patch.object(
            self.op, 'get_manager_pods',
            return_value=['sva-vault-manager-abc']
        ):
            mock_cutils.trycmd.return_value = ('manager-pvc', '')
            result = self.op.get_manager_pod()
            self.assertEqual(result, 'sva-vault-manager-abc')

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_manager_pod_no_pvc(self, mock_cutils):
        with mock.patch.object(
            self.op, 'get_manager_pods',
            return_value=['sva-vault-manager-abc']
        ):
            mock_cutils.trycmd.return_value = ('', 'err')
            result = self.op.get_manager_pod()
            self.assertEqual(result, '')

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_manager_pod_multiple_pvc(self, mock_cutils):
        with mock.patch.object(
            self.op, 'get_manager_pods',
            return_value=['sva-vault-manager-a', 'sva-vault-manager-b']
        ):
            mock_cutils.trycmd.return_value = ('manager-pvc', '')
            result = self.op.get_manager_pod()
            self.assertEqual(result, 'sva-vault-manager-b')

    def test_get_manager_pod_no_managers(self):
        with mock.patch.object(
            self.op, 'get_manager_pods', return_value=[]
        ):
            result = self.op.get_manager_pod()
            self.assertEqual(result, '')


class TestGetKeyShards(unittest.TestCase):
    """Tests for get_key_shards"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_key_shards_success(self, mock_cutils):
        mock_cutils.trycmd.return_value = ('{"keys":["a"]}  ', '')
        result = self.op.get_key_shards('pod1')
        self.assertEqual(result, '{"keys":["a"]}')

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_key_shards_missing(self, mock_cutils):
        mock_cutils.trycmd.return_value = ('', 'error')
        result = self.op.get_key_shards('pod1')
        self.assertEqual(result, '')

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    def test_get_key_shards_stderr(self, mock_cutils):
        mock_cutils.trycmd.return_value = ('', 'file not found')
        result = self.op.get_key_shards('pod1')
        self.assertEqual(result, '')


class TestCreateSecret(unittest.TestCase):
    """Tests for create_secret"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.mod = lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    def test_create_secret_success(self):
        mock_client = mock.MagicMock()
        resp = mock.MagicMock()
        resp.data = {'strdata': 'sharddata'}
        mock_client.create_namespaced_secret.return_value = resp
        result = self.op.create_secret(mock_client, 'sharddata')
        self.assertTrue(result)

    def test_create_secret_api_exception(self):
        from kubernetes.client.exceptions import ApiException
        mock_client = mock.MagicMock()
        mock_client.create_namespaced_secret.side_effect = \
            ApiException(status=500, reason="test")
        result = self.op.create_secret(mock_client, 'sharddata')
        self.assertFalse(result)

    def test_create_secret_verify_mismatch(self):
        mock_client = mock.MagicMock()
        resp = mock.MagicMock()
        resp.data = {'strdata': 'wrong'}
        mock_client.create_namespaced_secret.return_value = resp
        result = self.op.create_secret(mock_client, 'sharddata')
        self.assertTrue(result)

    def test_create_secret_no_data_attr(self):
        mock_client = mock.MagicMock()
        resp = mock.MagicMock(spec=[])
        mock_client.create_namespaced_secret.return_value = resp
        result = self.op.create_secret(mock_client, 'sharddata')
        self.assertTrue(result)


class TestReadPvcSecret(unittest.TestCase):
    """Tests for read_pvc_secret"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.mod = lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    def _valid_shards_json(self):
        return json.dumps({
            'keys': ['k1', 'k2', 'k3', 'k4', 'k5'],
            'keys_base64': ['b1', 'b2', 'b3', 'b4', 'b5'],
            'root_token': 'tok123'
        })

    def test_no_manager_pod(self):
        mock_client = mock.MagicMock()
        with mock.patch.object(
            self.op, 'get_manager_pod', return_value=''
        ):
            self.op.read_pvc_secret(mock_client)

    def test_no_keyshards(self):
        mock_client = mock.MagicMock()
        with mock.patch.object(
            self.op, 'get_manager_pod', return_value='pod1'
        ), mock.patch.object(
            self.op, 'get_key_shards', return_value=''
        ):
            self.op.read_pvc_secret(mock_client)

    def test_invalid_json(self):
        mock_client = mock.MagicMock()
        with mock.patch.object(
            self.op, 'get_manager_pod', return_value='pod1'
        ), mock.patch.object(
            self.op, 'get_key_shards', return_value='not-json{'
        ):
            self.op.read_pvc_secret(mock_client)

    def test_invalid_document(self):
        mock_client = mock.MagicMock()
        with mock.patch.object(
            self.op, 'get_manager_pod', return_value='pod1'
        ), mock.patch.object(
            self.op, 'get_key_shards', return_value='{"bad":"doc"}'
        ):
            self.op.read_pvc_secret(mock_client)

    def test_create_secret_fails(self):
        mock_client = mock.MagicMock()
        shards = self._valid_shards_json()
        with mock.patch.object(
            self.op, 'get_manager_pod', return_value='pod1'
        ), mock.patch.object(
            self.op, 'get_key_shards', return_value=shards
        ), mock.patch.object(
            self.op, 'create_secret', return_value=False
        ):
            self.op.read_pvc_secret(mock_client)

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.time')
    def test_read_pvc_secret_success(self, mock_time, mock_cutils):
        mock_client = mock.MagicMock()
        shards = self._valid_shards_json()
        b64 = b64encode(shards.encode()).decode()
        mock_cutils.trycmd.return_value = (b64, '')
        with mock.patch.object(
            self.op, 'get_manager_pod', return_value='pod1'
        ), mock.patch.object(
            self.op, 'get_key_shards', return_value=shards
        ), mock.patch.object(
            self.op, 'create_secret', return_value=True
        ):
            self.op.read_pvc_secret(mock_client)

    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.cutils')
    @mock.patch('k8sapp_vault.lifecycle.lifecycle_vault.time')
    def test_read_pvc_secret_validation_fail(self, mock_time, mock_cutils):
        mock_client = mock.MagicMock()
        shards = self._valid_shards_json()
        mock_cutils.trycmd.return_value = ('wrong', '')
        with mock.patch.object(
            self.op, 'get_manager_pod', return_value='pod1'
        ), mock.patch.object(
            self.op, 'get_key_shards', return_value=shards
        ), mock.patch.object(
            self.op, 'create_secret', return_value=True
        ):
            self.op.read_pvc_secret(mock_client)


class TestAppLifecycleActions(unittest.TestCase):
    """Tests for app_lifecycle_actions"""

    def setUp(self):
        with mock.patch(
            'k8sapp_vault.lifecycle.lifecycle_vault.kubernetes'
        ):
            from k8sapp_vault.lifecycle import lifecycle_vault
            self.mod = lifecycle_vault
            self.op = lifecycle_vault.VaultAppLifecycleOperator.__new__(
                lifecycle_vault.VaultAppLifecycleOperator
            )

    def test_lifecycle_pre_apply(self):
        hook_info = mock.MagicMock()
        hook_info.lifecycle_type = \
            self.mod.LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE
        hook_info.operation = self.mod.constants.APP_APPLY_OP
        hook_info.relative_timing = \
            self.mod.LifecycleConstants.APP_LIFECYCLE_TIMING_PRE
        app_op = mock.MagicMock()
        with mock.patch.object(
            self.op, 'read_pvc_secret'
        ) as mock_read, mock.patch.object(
            self.mod.base.AppLifecycleOperator,
            'app_lifecycle_actions'
        ):
            self.op.app_lifecycle_actions(
                None, None, app_op, mock.MagicMock(), hook_info)
            mock_read.assert_called_once()

    def test_lifecycle_pre_apply_exception(self):
        hook_info = mock.MagicMock()
        hook_info.lifecycle_type = \
            self.mod.LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE
        hook_info.operation = self.mod.constants.APP_APPLY_OP
        hook_info.relative_timing = \
            self.mod.LifecycleConstants.APP_LIFECYCLE_TIMING_PRE
        app_op = mock.MagicMock()
        with mock.patch.object(
            self.op, 'read_pvc_secret',
            side_effect=Exception("test")
        ), mock.patch.object(
            self.mod.base.AppLifecycleOperator,
            'app_lifecycle_actions'
        ):
            self.op.app_lifecycle_actions(
                None, None, app_op, mock.MagicMock(), hook_info)

    def test_lifecycle_other_hook(self):
        hook_info = mock.MagicMock()
        hook_info.lifecycle_type = 'other'
        hook_info.operation = 'other'
        hook_info.relative_timing = 'other'
        with mock.patch.object(
            self.mod.base.AppLifecycleOperator,
            'app_lifecycle_actions'
        ):
            self.op.app_lifecycle_actions(
                None, None, mock.MagicMock(),
                mock.MagicMock(), hook_info)
