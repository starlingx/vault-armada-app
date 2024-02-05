from debian:stable-slim

# Support versions of kubernetes back two releases of starlingx
# Versions older than 1.26 can be listed from:
# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.22.md
# Otherwise the latest minor releases are listed here:
# https://kubernetes.io/releases/

ENV KUBE_LATEST_VERSION="v1.28.4"
ENV KUBE_VERSIONS="v1.28.6 v1.27.10 v1.26.13 v1.25.16 v1.24.17"
ENV KUBECTL_DL_URL="https://storage.googleapis.com/kubernetes-release/release/${KUBE_LATEST_VERSION}/bin/linux/amd64/kubectl"
ENV KUBECTL_INSTALL_PATH="/usr/local/bin"

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

CMD ["bash"]
