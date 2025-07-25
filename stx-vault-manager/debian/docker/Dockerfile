# Build vault-monitor binary & completion script

# The commit hash used as the reference openbao-monitor code to apply vault patch
ARG BAOMON_COMMIT=a5c49d8e93f7413be8aef70583abcfa71a561cf6

FROM golang:1.24.3-bullseye AS builder

USER root

WORKDIR /src

# Copy in the patch
COPY 0001-Patch-baomon-into-vaultmon.patch /src

# Checkout & extract the openbao-monitor code. Patch in the conversion to vault
RUN git clone https://opendev.org/starlingx/utilities.git \
    && cd utilities \
    && git checkout -b vaultmon-build ${BAOMON_COMMIT} \
    && git apply --reject /src/0001-Patch-baomon-into-vaultmon.patch \
    && cd - \
    && mv utilities/security/openbao-monitor/source/* /src \
    && rm -r utilities

# build the binary
RUN go mod download

RUN go mod tidy

RUN go build -o /out/vaultmon .

# create auto-completion file
RUN /out/vaultmon completion bash > /out/vaultmon.completion

FROM debian:stable-slim

USER root

# Support versions of kubernetes back two releases of starlingx
# Older versions can be listed from changelog files here:
# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/
# Otherwise the latest minor releases are listed here:
# https://kubernetes.io/releases/

ENV KUBE_LATEST_VERSION="v1.32.6"
ENV KUBE_VERSIONS="v1.32.6 v1.31.10 v1.30.14 v1.29.15"
ENV KUBECTL_DL_URL="https://dl.k8s.io/${KUBE_LATEST_VERSION}/bin/linux/amd64/kubectl"
ENV KUBECTL_INSTALL_PATH="/usr/local/bin"

# install vault-manager's required packages
RUN set -ex; \
    PKG_LIST="mawk bash coreutils curl grep sed jq uuid-runtime bash-completion"; \
    apt-get update && apt-get install -y $PKG_LIST \
    && apt-get clean && rm -r /var/lib/apt/lists/*

# install all of the versions of kubectl
RUN set -ex; \
    mkdir -p $KUBECTL_INSTALL_PATH; \
    for ver in $KUBE_VERSIONS; do \
        fpath=${KUBECTL_INSTALL_PATH}/kubectl.${ver%.*}; \
        url="https://dl.k8s.io/${ver}/bin/linux/amd64/kubectl"; \
        curl -L "$url" -o ${fpath} \
        && chmod +x ${fpath}; \
    done

# link the latest version as default
RUN set -ex; \
    ln -s ${KUBECTL_INSTALL_PATH}/kubectl.${KUBE_LATEST_VERSION%.*} \
        ${KUBECTL_INSTALL_PATH}/kubectl

# Copy over the vaultmon and the completion script
COPY --from=builder /out/vaultmon /usr/bin
COPY --from=builder /out/vaultmon.completion /usr/share/bash-completion/completions/vaultmon

# create a non-root user/group for vault-manager
RUN groupadd --gid 1000 manager \
    && adduser --uid 1000 --gid 1000 manager \
        --home /workdir --shell /bin/bash

USER manager

CMD ["bash"]
