#
# Copyright (c) 2020-2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

"""Constants values for vault helm"""

# Helm: Supported charts:
# These values match the names in the chart package's Chart.yaml
HELM_APP_VAULT = 'vault'
HELM_RELEASE_VAULT = 'sva-vault'
HELM_CHART_VAULT = 'vault'
HELM_RELEASE_VAULT_MANAGER = 'sva-vault-manager'
HELM_CHART_VAULT_MANAGER = 'vault-manager'
HELM_CHART_NS_VAULT = 'vault'
HELM_VAULT_SERVER_POD = 'server'
HELM_VAULT_MANAGER_POD = 'manager'
HELM_VAULT_INJECTOR_POD = 'injector'

HELM_CHART_COMPONENT_LABEL = 'app.starlingx.io/component'

KEYSHARDS = 5
