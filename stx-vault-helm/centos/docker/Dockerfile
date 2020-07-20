ARG BASE
FROM ${BASE}

ARG STX_REPO_FILE=/etc/yum.repos.d/stx.repo

ENV KUBE_LATEST_VERSION="v1.18.3"

RUN set -ex ;\
    yum install --disablerepo=* \
        $(grep '^name=' ${STX_REPO_FILE} | awk -F '=' '{printf "--enablerepo=" $2 " "}') \
        -y \
        curl jq \
        && curl -L https://storage.googleapis.com/kubernetes-release/release/${KUBE_LATEST_VERSION}/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
        && chmod +x /usr/local/bin/kubectl

CMD ["bash"]
