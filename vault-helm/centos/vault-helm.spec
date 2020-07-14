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

BuildRequires: helm

%description
StarlingX Vault Helm Charts

%prep
%setup -n helm-charts-vault

%build
# initialize helm and build the toolkit
# helm init --client-only does not work if there is no networking
# The following commands do essentially the same as: helm init
%define helm_home  %{getenv:HOME}/.helm
mkdir  %{helm_home}
mkdir  %{helm_home}/repository
mkdir  %{helm_home}/repository/cache
mkdir  %{helm_home}/repository/local
mkdir  %{helm_home}/plugins
mkdir  %{helm_home}/starters
mkdir  %{helm_home}/cache
mkdir  %{helm_home}/cache/archive

# Stage a repository file that only has a local repo
cp %{SOURCE1} %{helm_home}/repository/repositories.yaml

# Stage a local repo index that can be updated by the build
cp %{SOURCE2} %{helm_home}/repository/local/index.yaml

# Host a server for the charts
helm serve --repo-path . &
helm repo rm local
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
