#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for k8sapp_vault kustomize operator."""

import unittest
from unittest import mock


class TestKustomizeOperator(unittest.TestCase):
    """Tests for VaultFluxCDKustomizeOperator"""

    def test_platform_mode_kustomize_updates(self):
        from k8sapp_vault.kustomize import kustomize_vault
        op = kustomize_vault.VaultFluxCDKustomizeOperator.__new__(
            kustomize_vault.VaultFluxCDKustomizeOperator
        )
        result = op.platform_mode_kustomize_updates(
            mock.MagicMock(), 'test')
        self.assertIsNone(result)

    def test_app_constant(self):
        from k8sapp_vault.kustomize import kustomize_vault
        from sysinv.common import constants
        self.assertEqual(
            kustomize_vault.VaultFluxCDKustomizeOperator.APP,
            constants.HELM_APP_VAULT)
