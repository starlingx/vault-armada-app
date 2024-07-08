FROM debian:stable-slim

USER root

# Support versions of kubernetes back two releases of starlingx
# Versions older than 1.26 can be listed from:
# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.22.md
# Otherwise the latest minor releases are listed here:
# https://kubernetes.io/releases/

ENV KUBE_LATEST_VERSION="v1.29.6"
ENV KUBE_VERSIONS="v1.29.6 v1.28.11 v1.27.15 v1.26.15 v1.25.16 v1.24.17"
ENV KUBECTL_DL_URL="https://storage.googleapis.com/kubernetes-release/release/${KUBE_LATEST_VERSION}/bin/linux/amd64/kubectl"
ENV KUBECTL_INSTALL_PATH="/usr/local/bin"

# install vault-manager's required packages
RUN set -ex; \
    PKG_LIST="mawk bash coreutils curl grep sed jq uuid-runtime"; \
    apt-get update && apt-get install -y $PKG_LIST \
    && apt-get clean && rm -r /var/lib/apt/lists/*

# install all of the versions of kubectl
RUN set -ex; \
    mkdir -p $KUBECTL_INSTALL_PATH; \
    for ver in $KUBE_VERSIONS; do \
        fpath=${KUBECTL_INSTALL_PATH}/kubectl.${ver%.*}; \
        url="https://storage.googleapis.com/kubernetes-release/release/${ver}/bin/linux/amd64/kubectl"; \
        curl -L "$url" -o ${fpath} \
        && chmod +x ${fpath}; \
    done

# link the latest version as default
RUN set -ex; \
    ln -s ${KUBECTL_INSTALL_PATH}/kubectl.${KUBE_LATEST_VERSION%.*} \
        ${KUBECTL_INSTALL_PATH}/kubectl

# create a non-root user/group for vault-manager
RUN groupadd --gid 1000 manager \
    && adduser --uid 1000 --gid 1000 manager \
        --home /workdir --shell /bin/bash

USER manager

CMD ["bash"]
