from debian:stable-slim

ENV KUBE_LATEST_VERSION="v1.24.4"
ENV KUBECTL_DL_URL="https://storage.googleapis.com/kubernetes-release/release/${KUBE_LATEST_VERSION}/bin/linux/amd64/kubectl"

RUN set -ex; \
    PKG_LIST="mawk bash coreutils curl grep sed jq"; \
    apt-get update && apt-get install -y $PKG_LIST \
    && apt-get clean && rm -r /var/lib/apt/lists/* \
    && curl -L "$KUBECTL_DL_URL" -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl

CMD ["bash"]
