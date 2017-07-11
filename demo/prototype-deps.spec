Name:       leapp-deps
Version:    0.1
Release:    1%{?dist}
Summary:    This rpm isn't for real usage and meant to contain only dependencies
URL:        https://github.com/leapp-to/leapp
License:    SeeProject

BuildRequires: ansible
BuildRequires: gcc
BuildRequires: libvirt-client
BuildRequires: libvirt-devel
BuildRequires: nmap
BuildRequires: openssl-devel
BuildRequires: pipsi
BuildRequires: python2-devel
BuildRequires: python2-pip
BuildRequires: redhat-rpm-config
BuildRequires: rubygem-hitimes
BuildRequires: rubygem-nio4r
BuildRequires: vagrant-libvirt

%description
This rpm isn't for real usage and meant to contain only BuildRequires

%changelog
* Tue Apr 18 2017 Vinzenz Feenstra <evilissimo@redhat.com> - 0.1-1
- SPEC creation
