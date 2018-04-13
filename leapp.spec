%global debug_package %{nil}
%global gittag master
%global dist %{nil}

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
Version:    0.3
Release:    1%{?dist}
Summary:    Leapp is an OS & Application modernization framework

License:    ASL 2.0
URL:        https://leapp-to.github.io
Source0:    https://github.com/leapp-to/%{name}/archive/%{gittag}/%{name}-%{version}.tar.gz

BuildArch:  noarch
%if %{with python2}
Requires: python2-%{name}%{?_isa} = %{version}-%{release}
%else
Requires: python3{name}%{?_isa} = %{version}-%{release}
%endif

%description
Leapp tool for handling upgrades


##################################################
# snactor package
##################################################
%package -n snactor
Summary:        %{sum}
%if %{with python2}
Requires: python2-%{name}%{?_isa} = %{version}-%{release}
%else
Requires: python3{name}%{?_isa} = %{version}-%{release}
%endif

%description -n snactor
Leapp's snactor tool - Actor development environment utility for creating and managing actor projects.

##################################################
# Python 2 library package
##################################################
%if %{with python2}

%package -n python2-%{name}

Summary:        %{sum}
%{?python_provide:%python_provide python2-%{name}}

%if 0%{?rhel} && 0%{?rhel} == 7
# RHEL 7
BuildRequires:  python-devel
BuildRequires:  python-setuptools
%else
# else
BuildRequires:  python2-devel

%if 0%{?fedora}
# Fedora
BuildRequires:  python2-pytest-cov
# BuildRequires:  python2-pytest-flake8

%endif

BuildRequires:  python2-setuptools

%endif

%description -n python2-%{name}
Python 2 leapp framework libraries

%endif


##################################################
# Python 3 library package
##################################################
%if %{with python3}

%package -n python3-%{name}
Summary:        %{sum}
%{?system_python_abi}
%{?python_provide:%python_provide python3-%{name}}

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

%if 0%{?fedora}
# Fedora
BuildRequires:  python3-pytest-cov
# BuildRequires:  python3-pytest-flake8

%endif



%description -n python3-%{name}
Python 3 leapp framework libraries

%endif

##################################################
# Prep
##################################################
%prep
%autosetup -n %{name}-%{gittag}

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

%if %{with python2}
%py2_install
%endif

%if %{with python3}
%py3_install
%endif

##################################################
# leapp files
##################################################
%files
%doc README.md
%license COPYING
%{_bindir}/leapp


##################################################
# snactor files
##################################################
%files -n snactor
%{_bindir}/snactor


##################################################
# python2-leapp files
##################################################
%if %{with python2}

%files -n python2-%{name}
%{python2_sitelib}/*

%endif

##################################################
# python3-leapp files
##################################################
%if %{with python3}
%files -n python3-%{name}
%{python3_sitelib}/*

%endif

%changelog

