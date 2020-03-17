# IMPORTANT:
# Please read the documentation on how to deal with dependencies before adding a new one.
# https://github.com/oamg/leapp/blob/master/docs/source/dependencies.md

%global debug_package %{nil}
%global gittag master

# IMPORTANT: this is for the leapp-framework capability (it's not the real
# version of the leapp). The capability reflects changes in api and whatever
# functionality important from the point of repository. In case of
# incompatible changes, bump the major number and zero minor one. Otherwise
# bump the minor one.
# This is kind of help for more flexible development of leapp repository,
# so people do not have to wait for new official release of leapp to ensure
# it is installed/used the compatible one.
%global framework_version 1.1

# IMPORTANT: everytime the requirements are changed, increment number by one
# - same for Provides in deps subpackage
%global framework_dependencies 3

# Do not build bindings for python3 for RHEL == 7
%if 0%{?rhel} && 0%{?rhel} == 7
%define with_python2 1
%else
%if 0%{?rhel} && 0%{?rhel} > 7
%bcond_with python2
%else
%bcond_without python2
%endif
%bcond_without python3
%endif

Name:       leapp
Version:    0.9.0
Release:    1%{?dist}
Summary:    OS & Application modernization framework

License:    ASL 2.0
URL:        https://oamg.github.io/leapp/
Source0:    https://github.com/oamg/%{name}/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildArch:  noarch

%if !0%{?fedora}
%if %{with python3}
Requires: python3-%{name} = %{version}-%{release}
%else
Requires: python2-%{name} = %{version}-%{release}
%endif

# Just ensure the leapp repository will be installed as well. Compatibility
# should be specified by the leapp-repository itself
Requires: leapp-repository
%endif # !fedora

%description
Leapp tool for handling upgrades.


##################################################
# snactor package
##################################################
%package -n snactor
Summary: %{summary}
%if %{with python3}
Requires: python3-%{name} = %{version}-%{release}
%else
Requires: python2-%{name} = %{version}-%{release}
%endif

%description -n snactor
Leapp's snactor tool - actor development environment utility for creating and
managing actor projects.

##################################################
# Python 2 library package
##################################################
%if %{with python2}

%package -n python2-%{name}

Summary: %{summary}
%{?python_provide:%python_provide python2-%{name}}

%if 0%{?rhel} && 0%{?rhel} == 7
# RHEL 7
BuildRequires:  python-devel
BuildRequires:  python-setuptools
%else # rhel <> 7 or fedora
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools

%if 0%{?fedora}
BuildRequires:  python2-pytest-cov
# BuildRequires:  python2-pytest-flake8
%endif # fedora
%endif # rhel <> 7

Provides: leapp-framework = %{framework_version}
Requires: leapp-framework-dependencies = %{framework_dependencies}

%description -n python2-%{name}
Python 2 leapp framework libraries.

%endif # with python2

# FIXME:
# this subpackages should be used by python2-%%{name} - so it makes sense to
# improve name and dependencies inside - do same subpackage for python3-%%{name}
%package deps
Summary:    Meta-package with system dependencies of %{name} package

# IMPORTANT: everytime the requirements are changed, increment number by one
# same for requiremenrs in main package above
Provides: leapp-framework-dependencies = %{framework_dependencies}
##################################################
# Real requirements for the leapp HERE
##################################################
# NOTE: ignore Python3 completely now
%if 0%{?rhel} && 0%{?rhel} == 7
Requires: python-six
Requires: python-setuptools
Requires: python-requests
%else
%if %{with python3}
Requires: python3-six
Requires: python3-setuptools
Requires: python3-requests
%else # with python2
Requires: python2-six
Requires: python2-setuptools
Requires: python2-requests
%endif
%endif
Requires: findutils
##################################################
# end requirements here
##################################################
%description deps
%{summary}

##################################################
# Python 3 library package
##################################################
%if %{with python3}

%package -n python3-%{name}
Summary: %{summary}
%{?system_python_abi}
%{?python_provide:%python_provide python3-%{name}}

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

%if 0%{?fedora}
# Fedora
BuildRequires:  python3-pytest-cov
%endif

Requires: leapp-framework-dependencies = %{framework_dependencies}

# FIXME: avoiding problems with dependencies on virtual capabilities, see:
#    https://serverfault.com/questions/411444/rpm-set-required-somepackage-0-5-0-and-somepackage-0-6-0
# Currently, we do not use this rpm, so commenting the provides for now, until
# we come up with reliable solution. E.g. avoid possibility to install both
# version of frameworks - for Py2 and Py3 in the same time. Or rename the 
# capability; e.g.: leapp-framework-py3
# Provides: leapp-framework = %{framework_version}

%description -n python3-%{name}
Python 3 leapp framework libraries.

%endif # with python3

##################################################
# Prep
##################################################
%prep
%autosetup -n %{name}-%{version}

##################################################
# Build
##################################################
%build

%if %{with python2}
%py2_build
%endif

%if %{with python3}
%py3_build
%endif


##################################################
# Install
##################################################
%install

install -m 0755 -d %{buildroot}%{_mandir}/man1
install -m 0644 -p man/snactor.1 %{buildroot}%{_mandir}/man1/

%if !0%{?fedora}
install -m 0755 -d %{buildroot}%{_sharedstatedir}/leapp
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp/repos.d
install -m 0600 -d %{buildroot}%{_sysconfdir}/leapp/answers
# standard directory should have permission set to 0755, however this directory
# could contain sensitive data, hence permission for root only
install -m 0700 -d %{buildroot}%{_sysconfdir}/leapp/answers
# same for this dir; we need it for the frontend in cockpit
install -m 0700 -d %{buildroot}%{_localstatedir}/log/leapp
install -m 0644 etc/leapp/*.conf %{buildroot}%{_sysconfdir}/leapp
install -m 0644 -p man/leapp.1 %{buildroot}%{_mandir}/man1/
%endif # !fedora

%if %{with python2}
%py2_install
%endif

%if %{with python3}
%py3_install
%endif

%if 0%{?fedora}
rm -f %{buildroot}/%{_bindir}/leapp
%endif


##################################################
# leapp files
##################################################

%if !0%{?fedora}
%files
%doc README.md
%license COPYING
%{_mandir}/man1/leapp.1*
%config(noreplace) %{_sysconfdir}/leapp/leapp.conf
%config(noreplace) %{_sysconfdir}/leapp/logger.conf
%dir %{_sysconfdir}/leapp
%dir %{_sysconfdir}/leapp/answers
%dir %{_sysconfdir}/leapp/repos.d
%{_bindir}/leapp
%dir %{_sharedstatedir}/leapp
%dir %{_localstatedir}/log/leapp
%{python2_sitelib}/leapp/cli
%endif



##################################################
# snactor files
##################################################
%files -n snactor
%license COPYING
%{python2_sitelib}/leapp/snactor
%{_mandir}/man1/snactor.1*
%{_bindir}/snactor


##################################################
# python2-leapp files
##################################################
%if %{with python2}

%files -n python2-%{name}
%license COPYING
%{python2_sitelib}/*
# this one is related only to leapp tool
%exclude %{python2_sitelib}/leapp/cli
%exclude %{python2_sitelib}/leapp/snactor

%endif

##################################################
# python3-leapp files
##################################################
%if %{with python3}

%files -n python3-%{name}
%license COPYING
%{python3_sitelib}/*
#TODO: ignoring leapp and snactor in separate rpms now as we do not provide
# entrypoints for Py3 in those subpackages anyway

%endif

%files deps
# no files here

%changelog
* Mon Apr 16 2018 Vinzenz Feenstra <evilissimo@gmail.com> - %{version}-%{release}
- Initial rpm
