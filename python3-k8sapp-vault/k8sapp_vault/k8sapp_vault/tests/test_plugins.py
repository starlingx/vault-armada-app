#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from sysinv.common import constants
from sysinv.tests.db import base as dbbase


class K8SAppVaultAppMixin(object):
    app_name = constants.HELM_APP_VAULT
    path_name = app_name + '.tgz'

    def setUp(self):
        super(K8SAppVaultAppMixin, self).setUp()


# Test Configuration:
# - Controller
# - IPv6
# - Ceph Storage
# - vault app
class K8sAppVaultControllerTestCase(K8SAppVaultAppMixin,
                                    dbbase.BaseIPv6Mixin,
                                    dbbase.BaseCephStorageBackendMixin,
                                    dbbase.ControllerHostTestCase):
    pass


# Test Configuration:
# - AIO
# - IPv4
# - Ceph Storage
# - vault app
class K8SAppVaultAIOTestCase(K8SAppVaultAppMixin,
                             dbbase.BaseCephStorageBackendMixin,
                             dbbase.AIOSimplexHostTestCase):
    pass
