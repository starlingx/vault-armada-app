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
Name: vault-helm
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown

Source0: helm-charts-vault-0-6-0.tar.gz
Source1: repositories.yaml
Source2: index.yaml
Source3: Makefile
Source4: metadata.yaml
Source5: vault-init.yaml
Source6: vault-certificates.yaml
Source7: _helpers-CA.tpl

BuildArch: noarch

Patch01: 0001-Add-vault-manager-repository-to-values.yaml.patch

BuildRequires: helm
BuildRequires: chartmuseum

%description
StarlingX Vault Helm Charts

%prep
%setup -n helm-charts-vault

%patch01 -p1

%build
chartmuseum --debug --port=8879 --context-path='/charts' --storage="local" --storage-local-rootdir="." &
sleep 2

helm repo add local http://localhost:8879/charts

# Create the tgz file
cp %{SOURCE3} ./
mkdir ./vault
cp ./Chart.yaml ./vault
mv ./values.yaml ./vault
cp %{SOURCE5} ./templates
cp %{SOURCE6} ./templates
cat %{SOURCE7} >> ./templates/_helpers.tpl
mv ./templates ./vault/templates

make vault
cd -

# Terminate helm server (the last backgrounded task)
kill %1

# Create a chart tarball compliant with sysinv kube-app.py
#%define app_staging %{_builddir}/staging
#%define app_tarball %{app_name}-%{version}-%{tis_patch_ver}.tgz

# Setup staging
mkdir -p %{app_staging}
cp %{SOURCE4} %{app_staging}
mkdir -p %{app_staging}/charts
cp ./helm-charts-vault/*.tgz %{app_staging}/charts
cd %{app_staging}

# package it up
find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
tar -zcf %{_builddir}/%{app_tarball} -C %{app_staging}/ .

# Cleanup staging
#rm -fr %{app_staging}


%install
install -d -m 755 ${RPM_BUILD_ROOT}%{helm_folder}
install -p -D -m 755 %{app_staging}/charts/*.tgz ${RPM_BUILD_ROOT}%{helm_folder}


%files
%defattr(-,root,root,-)
%{helm_folder}/*
