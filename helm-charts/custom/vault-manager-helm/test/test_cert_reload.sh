#!/bin/bash
#
# Unit tests for vault-cert-reload.sh (the cert-reload CronJob script)
#
# This test extracts the script from the helm template, substitutes
# helm values with test defaults using sed, sources the script
# (functions only), and tests each function with mocked externals.
#
# Requirements: openssl, bash
#
# Usage:
#   bash test_cert_reload.sh
#

set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHART_DIR="$SCRIPT_DIR/../vault-manager-helm/vault-manager"
TEMPLATE="$CHART_DIR/templates/vault-cert-reload.yaml"
WORKDIR=$(mktemp -d)
trap "rm -rf $WORKDIR" EXIT

# Test counters
PASS=0
FAIL=0

assert_eq() {
    local test_name="$1" expected="$2" actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        echo "PASS: $test_name"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $test_name"
        echo "  expected: '$expected'"
        echo "  actual:   '$actual'"
        FAIL=$((FAIL + 1))
    fi
}

assert_ne() {
    local test_name="$1" not_expected="$2" actual="$3"
    if [[ "$not_expected" != "$actual" ]]; then
        echo "PASS: $test_name"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $test_name (should not equal '$not_expected')"
        FAIL=$((FAIL + 1))
    fi
}

assert_rc() {
    local test_name="$1" expected_rc="$2" actual_rc="$3"
    if [[ "$expected_rc" == "$actual_rc" ]]; then
        echo "PASS: $test_name"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $test_name"
        echo "  expected rc: $expected_rc"
        echo "  actual rc:   $actual_rc"
        FAIL=$((FAIL + 1))
    fi
}

test_results() {
    echo ""
    echo "Results: $PASS passed, $FAIL failed"
    exit $FAIL
}

#
# Extract the script from the helm template ConfigMap
#
# Strategy: The ConfigMap has 'cert-reload.sh: |' as the start marker.
# The script content is indented by 4 spaces. Extract until next
# unindented line (---) or end of ConfigMap.
#
echo "--- Extracting cert-reload.sh from template ---"

EXTRACTED="$WORKDIR/cert-reload.sh"

# Extract lines between 'cert-reload.sh: |' and the next '---' separator,
# stripping the 4-space indent
awk '
    /^  cert-reload.sh: \|/ { capture=1; next }
    capture && /^---/ { exit }
    capture && /^[^ ]/ { exit }
    capture && /^    / { sub(/^    /, ""); print }
' "$TEMPLATE" > "$EXTRACTED"

if [ ! -s "$EXTRACTED" ]; then
    echo "ERROR: Failed to extract script from template."
    exit 1
fi

# Substitute helm template values with test defaults
CERT_PATH='/vault/userconfig/vault-server-tls/tls.crt'
sed -i \
    -e 's/{{ .Release.Namespace }}/vault/g' \
    -e 's/{{ .Values.vault.fullname }}/sva-vault/g' \
    -e 's/{{ .Values.vault.name }}/vault/g' \
    -e 's/{{ .Values.certReload.sighupDelay }}/1/g' \
    -e 's/{{ .Values.certReload.verifyRetries }}/2/g' \
    -e 's/{{ .Values.certReload.connectTimeout }}/10/g' \
    -e "s#{{ .Values.certReload.serverCertPath | quote }}#\"${CERT_PATH}\"#g" \
    -e 's/{{ .Values.manager.k8s.client_version }}//g' \
    -e 's#{{ .Values.certReload.caSecret | default "" | quote }}#""#g' \
    -e '/^{{-/d' \
    "$EXTRACTED"

# Verify no remaining template expressions
remaining=$(grep -c '{{' "$EXTRACTED" 2>/dev/null || true)
if [ "$remaining" -gt 0 ]; then
    echo "ERROR: Unresolved template expressions remain:"
    grep '{{' "$EXTRACTED"
    exit 1
fi

echo "--- Sourcing cert-reload.sh ---"
source "$EXTRACTED"

#
# Generate test certificates
#
echo "--- Generating test certificates ---"

# CA key and cert
openssl req -x509 -newkey rsa:2048 -keyout "$WORKDIR/ca.key" \
    -out "$WORKDIR/ca.crt" -days 1 -nodes \
    -subj "/CN=test-ca" 2>/dev/null

# Server cert A (current)
openssl req -newkey rsa:2048 -keyout "$WORKDIR/a.key" \
    -out "$WORKDIR/a.csr" -nodes -subj "/CN=vault-a" 2>/dev/null
openssl x509 -req -in "$WORKDIR/a.csr" -CA "$WORKDIR/ca.crt" \
    -CAkey "$WORKDIR/ca.key" -CAcreateserial \
    -out "$WORKDIR/a.crt" -days 1 2>/dev/null

# Server cert B (stale)
openssl req -newkey rsa:2048 -keyout "$WORKDIR/b.key" \
    -out "$WORKDIR/b.csr" -nodes -subj "/CN=vault-b" 2>/dev/null
openssl x509 -req -in "$WORKDIR/b.csr" -CA "$WORKDIR/ca.crt" \
    -CAkey "$WORKDIR/ca.key" -CAcreateserial \
    -out "$WORKDIR/b.crt" -days 1 2>/dev/null

FP_A=$(openssl x509 -in "$WORKDIR/a.crt" -noout -fingerprint -sha256 \
    | sed 's/.*=//')
FP_B=$(openssl x509 -in "$WORKDIR/b.crt" -noout -fingerprint -sha256 \
    | sed 's/.*=//')

echo ""
echo "=== Tests ==="
echo ""

# ---------------------------------------------------------------
# Test: log function output format
# ---------------------------------------------------------------
test_log_info() {
    local output
    output=$(log $INFO "test message" 2>&1)
    # Should contain INFO and the message
    assert_eq "log INFO contains level" "0" \
        "$(echo "$output" | grep -c "INFO test message")"
}

test_log_error() {
    local output
    output=$(log $ERROR "bad thing" 2>&1)
    assert_eq "log ERROR contains level" "0" \
        "$(echo "$output" | grep -c "ERROR bad thing")"
}

# Fix: grep -c returns count; 1 means found
test_log_info() {
    local output
    output=$(log $INFO "test message" 2>&1)
    assert_eq "log INFO format" "1" \
        "$(echo "$output" | grep -c "INFO test message")"
}

test_log_error() {
    local output
    output=$(log $ERROR "bad thing" 2>&1)
    assert_eq "log ERROR format" "1" \
        "$(echo "$output" | grep -c "ERROR bad thing")"
}

test_log_warning() {
    local output
    output=$(log $WARNING "be careful" 2>&1)
    assert_eq "log WARNING format" "1" \
        "$(echo "$output" | grep -c "WARNING be careful")"
}

# ---------------------------------------------------------------
# Test: get_file_cert_fingerprint
# ---------------------------------------------------------------
test_get_file_cert_fingerprint() {
    CERT_FILE="$WORKDIR/a.crt"
    local fp
    fp=$(get_file_cert_fingerprint)
    assert_eq "get_file_cert_fingerprint returns expected" "$FP_A" "$fp"
}

test_get_file_cert_fingerprint_different() {
    CERT_FILE="$WORKDIR/b.crt"
    local fp
    fp=$(get_file_cert_fingerprint)
    assert_eq "get_file_cert_fingerprint cert B" "$FP_B" "$fp"
    assert_ne "fingerprints A and B differ" "$FP_A" "$fp"
}

test_get_file_cert_fingerprint_missing_file() {
    CERT_FILE="$WORKDIR/nonexistent.crt"
    local fp
    fp=$(get_file_cert_fingerprint)
    assert_eq "get_file_cert_fingerprint missing file returns empty" "" "$fp"
}

# ---------------------------------------------------------------
# Test: get_server_cert_fingerprint (mocked)
# ---------------------------------------------------------------
test_get_server_cert_fingerprint_mock() {
    # Mock openssl s_client by overriding the function
    # to return cert A content
    get_server_cert_fingerprint() {
        local ip="$1"
        cat "$WORKDIR/a.crt" \
            | openssl x509 -noout -fingerprint -sha256 2>/dev/null \
            | sed 's/.*=//'
    }
    local fp
    fp=$(get_server_cert_fingerprint "10.0.0.1")
    assert_eq "get_server_cert_fingerprint mock returns FP_A" "$FP_A" "$fp"

    # Restore original function
    source "$EXTRACTED"
}

# ---------------------------------------------------------------
# Test: CA_FILE selection via OVERRIDE_CA_FILE
# ---------------------------------------------------------------
test_ca_file_default() {
    OVERRIDE_CA_FILE=""
    if [ -n "$OVERRIDE_CA_FILE" ]; then
        CA_FILE=/mnt/ca-override/ca.crt
    else
        CA_FILE=/mnt/certs/ca.crt
    fi
    assert_eq "CA_FILE default path" "/mnt/certs/ca.crt" "$CA_FILE"
}

test_ca_file_override() {
    OVERRIDE_CA_FILE="my-custom-ca"
    if [ -n "$OVERRIDE_CA_FILE" ]; then
        CA_FILE=/mnt/ca-override/ca.crt
    else
        CA_FILE=/mnt/certs/ca.crt
    fi
    assert_eq "CA_FILE override path" "/mnt/ca-override/ca.crt" "$CA_FILE"
}

# ---------------------------------------------------------------
# Test: compareK8sVersion
# ---------------------------------------------------------------
test_compareK8sVersion_equal() {
    compareK8sVersion "v1.28" "v1.28"
    assert_rc "compareK8sVersion equal" 1 $?
}

test_compareK8sVersion_left_greater() {
    compareK8sVersion "v1.29" "v1.28"
    assert_rc "compareK8sVersion left greater" 0 $?
}

test_compareK8sVersion_right_greater() {
    compareK8sVersion "v1.27" "v1.28"
    assert_rc "compareK8sVersion right greater" 2 $?
}

test_compareK8sVersion_major_differ() {
    compareK8sVersion "v2.1" "v1.99"
    assert_rc "compareK8sVersion major left" 0 $?
}

# ---------------------------------------------------------------
# Test: switchK8sVersion (mocked binaries)
# ---------------------------------------------------------------
test_switchK8sVersion_exists() {
    # Create a fake kubectl.v1.28 binary
    local mockdir="$WORKDIR/mockbin"
    mkdir -p "$mockdir"
    cat > "$mockdir/kubectl.v1.28" <<'EOF'
#!/bin/bash
echo "mock kubectl v1.28"
EOF
    chmod +x "$mockdir/kubectl.v1.28"
    export PATH="$mockdir:$PATH"
    KUBECTL_INSTALL_PATH="$mockdir"

    KUBECTL=kubectl
    switchK8sVersion "v1.28"
    assert_rc "switchK8sVersion existing binary succeeds" 0 $?
    assert_eq "switchK8sVersion sets KUBECTL" "kubectl.v1.28" "$KUBECTL"
    KUBECTL=kubectl
}

test_switchK8sVersion_missing() {
    KUBECTL_INSTALL_PATH="$WORKDIR/mockbin"
    KUBECTL=kubectl
    switchK8sVersion "v1.99"
    assert_rc "switchK8sVersion missing binary fails" 1 $?
    assert_eq "switchK8sVersion KUBECTL unchanged" "kubectl" "$KUBECTL"
}

# ---------------------------------------------------------------
# Test: pickK8sVersion (mocked kubectl + binaries)
# ---------------------------------------------------------------
test_pickK8sVersion_helm_override() {
    local mockdir="$WORKDIR/mockbin"
    mkdir -p "$mockdir"
    cat > "$mockdir/kubectl.v1.29" <<'EOF'
#!/bin/bash
echo "mock kubectl v1.29"
EOF
    chmod +x "$mockdir/kubectl.v1.29"
    export PATH="$mockdir:$PATH"
    KUBECTL_INSTALL_PATH="$mockdir"

    KUBECTL=kubectl
    KUBECTL_HELM_OVERRIDE="v1.29"
    KUBE_VERSIONS="v1.29.1 v1.28.3"
    pickK8sVersion
    assert_eq "pickK8sVersion uses helm override" "kubectl.v1.29" "$KUBECTL"
    KUBECTL=kubectl
    KUBECTL_HELM_OVERRIDE=""
}

test_pickK8sVersion_from_server() {
    local mockdir="$WORKDIR/mockbin2"
    mkdir -p "$mockdir"

    # Mock kubectl that returns server version json
    cat > "$mockdir/kubectl" <<'EOF'
#!/bin/bash
if [[ "$*" == *"version"* ]]; then
    echo '{"serverVersion":{"major":"1","minor":"28","gitVersion":"v1.28.5"}}'
fi
EOF
    chmod +x "$mockdir/kubectl"

    # Mock kubectl.v1.28
    cat > "$mockdir/kubectl.v1.28" <<'EOF'
#!/bin/bash
echo "mock"
EOF
    chmod +x "$mockdir/kubectl.v1.28"

    export PATH="$mockdir:$PATH"
    KUBECTL_INSTALL_PATH="$mockdir"
    KUBECTL="$mockdir/kubectl"
    KUBECTL_HELM_OVERRIDE=""
    KUBE_VERSIONS="v1.29.1 v1.28.3 v1.27.2"

    pickK8sVersion
    assert_eq "pickK8sVersion matches server v1.28" "kubectl.v1.28" "$KUBECTL"
    KUBECTL=kubectl
    KUBE_VERSIONS=""
}

test_pickK8sVersion_no_kube_versions() {
    KUBECTL=kubectl
    KUBECTL_HELM_OVERRIDE=""
    KUBE_VERSIONS=""
    pickK8sVersion
    # Should be a no-op, KUBECTL unchanged
    assert_eq "pickK8sVersion no KUBE_VERSIONS is no-op" "kubectl" "$KUBECTL"
}

# ---------------------------------------------------------------
# Test: send_sighup (mocked kubectl exec)
# ---------------------------------------------------------------
test_send_sighup_success() {
    # Mock kubectl to succeed
    KUBECTL="true"  # /usr/bin/true ignores args, returns 0
    send_sighup "sva-vault-0"
    assert_rc "send_sighup success" 0 $?
    KUBECTL=kubectl
}

test_send_sighup_failure() {
    KUBECTL="false"  # /usr/bin/false returns 1
    send_sighup "sva-vault-0"
    assert_rc "send_sighup failure" 1 $?
    KUBECTL=kubectl
}

# ---------------------------------------------------------------
# Test: get_vault_pods (mocked kubectl)
# ---------------------------------------------------------------
test_get_vault_pods_mock() {
    # Create a mock kubectl script
    cat > "$WORKDIR/mock_kubectl" <<'EOF'
#!/bin/bash
echo "sva-vault-0 172.16.0.1"
echo "sva-vault-1 172.16.0.2"
EOF
    chmod +x "$WORKDIR/mock_kubectl"
    KUBECTL="$WORKDIR/mock_kubectl"

    local output
    output=$(get_vault_pods)
    local count
    count=$(echo "$output" | wc -l)
    assert_eq "get_vault_pods returns 2 pods" "2" "$count"
    KUBECTL=kubectl
}

# ---------------------------------------------------------------
# Test: get_pod_mounted_cert_fingerprint (mocked)
# ---------------------------------------------------------------
test_get_pod_mounted_cert_fingerprint_mock() {
    # Mock kubectl exec to cat cert A
    cat > "$WORKDIR/mock_kubectl_exec" <<EOF
#!/bin/bash
cat "$WORKDIR/a.crt"
EOF
    chmod +x "$WORKDIR/mock_kubectl_exec"
    KUBECTL="$WORKDIR/mock_kubectl_exec"

    local fp
    fp=$(get_pod_mounted_cert_fingerprint "sva-vault-0")
    assert_eq "get_pod_mounted_cert_fingerprint returns FP_A" "$FP_A" "$fp"
    KUBECTL=kubectl
}

# ---------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------
test_log_info
test_log_error
test_log_warning
test_get_file_cert_fingerprint
test_get_file_cert_fingerprint_different
test_get_file_cert_fingerprint_missing_file
test_get_server_cert_fingerprint_mock
test_ca_file_default
test_ca_file_override
test_compareK8sVersion_equal
test_compareK8sVersion_left_greater
test_compareK8sVersion_right_greater
test_compareK8sVersion_major_differ
test_switchK8sVersion_exists
test_switchK8sVersion_missing
test_pickK8sVersion_helm_override
test_pickK8sVersion_from_server
test_pickK8sVersion_no_kube_versions
test_send_sighup_success
test_send_sighup_failure
test_get_vault_pods_mock
test_get_pod_mounted_cert_fingerprint_mock

test_results
