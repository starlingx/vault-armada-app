# Application tunables (maps to metadata)
%global app_name vault
%global helm_repo stx-platform

%global armada_folder  /usr/lib/armada

# Install location
%global app_folder /usr/local/share/applications/helm

# Build variables
%global helm_folder /usr/lib/helm
%global toolkit_version 0.1.0

Summary: StarlingX Vault Armada Helm Charts
Name: stx-vault-helm
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown

# External helm chart source
Source0: helm-charts-vault-0-6-0.tar.gz

# psp-rolebinding source from stx/helm-charts/psp-rolebinding
# plugins source from stx/vault-armada-app/python-k8sapp-vault

BuildArch: noarch

BuildRequires: helm
BuildRequires: chartmuseum
BuildRequires: vault-helm
BuildRequires: python-k8sapp-vault
BuildRequires: python-k8sapp-vault-wheels

%description
StarlingX Vault Helm Charts

%package fluxcd
Summary: StarlingX Vault Application FluxCD Helm Charts
Group: base
License: Apache-2.0

%description fluxcd
StarlingX Vault Application FluxCD Helm Charts

%prep
%setup -n helm-charts-vault-0-6-0-1.0.0

%build
chartmuseum --debug --port=8879 --context-path='/charts' --storage="local" --storage-local-rootdir="." &
sleep 2

helm repo add local http://localhost:8879/charts

# psp-rolebinding source is copied by the function of build_srpm.data
# COPY_LIST_TO_TAR
cd helm-charts
make psp-rolebinding

# switch back to source root
cd -

# Terminate helm server (the last backgrounded task)
kill %1

# Create a chart tarball compliant with sysinv kube-app.py
%define app_staging %{_builddir}/staging
%define app_tarball_armada %{app_name}-%{version}-%{tis_patch_ver}.tgz
%define app_tarball_fluxcd %{app_name}-fluxcd-%{version}-%{tis_patch_ver}.tgz

# Setup staging
mkdir -p %{app_staging}
cp files/metadata.yaml %{app_staging}
cp manifests/vault_manifest.yaml %{app_staging}
mkdir -p %{app_staging}/charts

# copy psp-rolebinding tar
cp helm-charts/*.tgz %{app_staging}/charts

# copy vault tar built by vault-helm/centos/vault-helm.spec
cp %{helm_folder}/vault*.tgz %{app_staging}/charts

# Populate metadata
cd %{app_staging}
sed -i 's/@APP_NAME@/%{app_name}/g' %{app_staging}/metadata.yaml
sed -i 's/@APP_VERSION@/%{version}-%{tis_patch_ver}/g' %{app_staging}/metadata.yaml
sed -i 's/@HELM_REPO@/%{helm_repo}/g' %{app_staging}/metadata.yaml

# Copy the plugins: installed in the buildroot
# built by python-k8sapp-vault/centos/python-k8sapp-vault.spec
mkdir -p %{app_staging}/plugins
cp /plugins/%{app_name}/*.whl %{app_staging}/plugins

# calculate checksum of all files in app_staging
find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
# package armada
tar -zcf %{_builddir}/%{app_tarball_armada} -C %{app_staging}/ .

# switch back to source root
cd -

# Prepare app_staging for fluxcd package
rm -f %{app_staging}/vault_manifest.yaml

cp -R fluxcd-manifests %{app_staging}/

# calculate checksum of all files in app_staging
cd %{app_staging}
find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
# package fluxcd app
tar -zcf %{_builddir}/%{app_tarball_fluxcd} -C %{app_staging}/ .

# switch back to source root
cd -

# Cleanup staging
rm -fr %{app_staging}

%install
install -d -m 755 %{buildroot}/%{app_folder}
install -p -D -m 755 %{_builddir}/%{app_tarball_armada} %{buildroot}/%{app_folder}
install -p -D -m 755 %{_builddir}/%{app_tarball_fluxcd} %{buildroot}/%{app_folder}

%files
%defattr(-,root,root,-)
%{app_folder}/%{app_tarball_armada}

%files fluxcd
%defattr(-,root,root,-)
%{app_folder}/%{app_tarball_fluxcd}
