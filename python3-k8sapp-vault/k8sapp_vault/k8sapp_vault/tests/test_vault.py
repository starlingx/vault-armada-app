# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
from k8sapp_vault.common import constants as app_constants
from k8sapp_vault.tests import test_plugins

from sysinv.db import api as dbapi
from sysinv.helm import common

from sysinv.tests.db import base as dbbase
from sysinv.tests.db import utils as dbutils
from sysinv.tests.helm import base


class VaultTestCase(test_plugins.K8SAppVaultAppMixin,
                          base.HelmTestCaseMixin):

    def setUp(self):
        super(VaultTestCase, self).setUp()
        self.app = dbutils.create_test_app(name='vault')
        self.dbapi = dbapi.get_instance()


class VaultIPv4ControllerHostTestCase(VaultTestCase,
                                            dbbase.ProvisionedControllerHostTestCase):

    def test_replicas(self):
        overrides = self.operator.get_helm_chart_overrides(
            app_constants.HELM_CHART_VAULT,
            cnamespace=common.HELM_NS_VAULT)

        self.assertOverridesParameters(overrides, {
            'server': {'ha': {'replicas': 1}}
        })


class VaultIPv6AIODuplexSystemTestCase(VaultTestCase,
                                             dbbase.BaseIPv6Mixin,
                                             dbbase.ProvisionedAIODuplexSystemTestCase):

    def test_replicas(self):
        overrides = self.operator.get_helm_chart_overrides(
            app_constants.HELM_CHART_VAULT,
            cnamespace=common.HELM_NS_VAULT)

        self.assertOverridesParameters(overrides, {
            'server': {'ha': {'replicas': 1}}
        })
