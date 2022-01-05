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
%global framework_version 2.1

# IMPORTANT: everytime the requirements are changed, increment number by one
# - same for Provides in deps subpackage
%global framework_dependencies 4

# Do not build bindings for python3 for RHEL == 7
# # Currently Py2 is dead on Fedora and we don't have to support it. As well,
# # our current packaging is not prepared for Py2 & Py3 packages in the same
# # time. Instead of that, make Py2 and Py3 exclusive. Possibly rename macros..
%if 0%{?rhel} == 7
  %define leapp_python 2
  %define leapp_python_sitelib %{python2_sitelib}
  %define leapp_python_name python2
  %define leapp_py_build %{py2_build}
  %define leapp_py_install %{py2_install}

%else
  %define leapp_python 3
  %define leapp_python_sitelib %{python3_sitelib}
  %define leapp_python_name python3
  %define leapp_py_build %{py3_build}
  %define leapp_py_install %{py3_install}
  # we have to drop the dependency on python(abi) completely on el8+ because
  # of IPU (python abi is different between systems)
  # NOTE: however, we will set the abi deps inside the meta-package, as RHEL 8
  # could contain various python 3 versions and we can handle just one version
  # per package.
  %global __requires_exclude ^python\\(abi\\) = 3\\..+|/usr/libexec/platform-python|/usr/bin/python.*
%endif

Name:       leapp
Version:    0.13.0
Release:    1%{?dist}
Summary:    OS & Application modernization framework

License:    ASL 2.0
URL:        https://oamg.github.io/leapp/
Source0:    https://github.com/oamg/%{name}/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildArch:  noarch

Requires: %{leapp_python_name}-%{name} = %{version}-%{release}
%{?python_disable_dependency_generator}

%if 0%{?rhel} == 7
# The leapp tool doesn't require the leapp-repository anymore. However for the
# compatibility purposes, we keep it here for RHEL 7 at least for a while.
# The dependency on leapp is expected to be set by packages providing the
# final functionality (e.g. conversion of system, in-place upgrade).
# IOW, people should look for rpms like leapp-convert or leapp-upgrade
# in future.

# Just ensure the leapp repository will be installed as well. Compatibility
# should be specified by the leapp-repository itself
Requires: leapp-repository
%endif # !fedora

# FIXME(pstodulk): tha man page is not updated yet!
%description
Leapp utility provides the possibility to use the Leapp framework via CLI.
The utility itself does not define any subcommands but "help". All leapp
subcommands are expected to be provided by other packages under a specific
directory. See the man page for more details.


##################################################
# snactor package
##################################################
%package -n snactor
Summary: %{summary}
Requires: %{leapp_python_name}-%{name} = %{version}-%{release}
%{?python_disable_dependency_generator}

%description -n snactor
Leapp's snactor tool - actor development environment utility for creating and
managing actor projects.

##################################################
# the library package (the framework itself)
##################################################
%package -n %{leapp_python_name}-%{name}

Summary: %{summary}
%{?python_provide:%python_provide %{leapp_python_name}-%{name}}

%if %{leapp_python} == 2
# RHEL 7 only
BuildRequires:  python-devel
BuildRequires:  python-setuptools
Conflicts:      python3-%{name}
%else
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Conflicts:      python2-%{name}

%{?python_disable_dependency_generator}
%define __provides_exclude_from ^.*$
%endif

Provides: leapp-framework = %{framework_version}
Requires: leapp-framework-dependencies = %{framework_dependencies}

%description -n %{leapp_python_name}-%{name}
Python %{leapp_python} leapp framework libraries.


##################################################
# DEPS package for external dependencies
##################################################
%package deps
Summary:    Meta-package with system dependencies of %{name} package

# IMPORTANT: everytime the requirements are changed, increment number by one
# same for requiremenrs in main package above
Provides: leapp-framework-dependencies = %{framework_dependencies}
##################################################
# Real requirements for the leapp HERE
##################################################
%if 0%{?rhel} && 0%{?rhel} == 7
Requires: python-six
Requires: python-setuptools
Requires: python-requests
%else # <> rhel 7
# for Fedora & RHEL 8+ deliver just python3 stuff
Requires: python3-six
Requires: python3-setuptools
Requires: python3-requests
%if 0%{?rhel} == 8
# this prevents situation when someone would like to install leapp with
# python-3.8+ on RHEL 8, but does not affect any else systems nor upgrades.
Requires: python(abi) = 3.6
%else # rhel 9
Requires: python(abi) = 3.9
%endif
%endif
Requires: findutils
##################################################
# end requirements here
##################################################

%description deps
%{summary}


##################################################
# Prep
##################################################
%prep
%setup -n %{name}-%{version}


##################################################
# Build
##################################################
%build
%{leapp_py_build}


##################################################
# Install
##################################################
%install

install -m 0755 -d %{buildroot}%{_mandir}/man1
install -m 0644 -p man/snactor.1 %{buildroot}%{_mandir}/man1/

# This block of files was originally skipped for fedora. Adding now
install -m 0755 -d %{buildroot}%{_datadir}/leapp
install -m 0755 -d %{buildroot}%{_datadir}/leapp/report_schema
install -m 0644 -p report-schema-v110.json %{buildroot}%{_datadir}/leapp/report_schema/report-schema.json
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

%{leapp_py_install}


##################################################
# leapp files
##################################################

# the condition should be dropped in future
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
%dir %{_datadir}/leapp/
%dir %{_datadir}/leapp/report_schema/
%{_datadir}/leapp/report_schema
%{leapp_python_sitelib}/leapp/cli


##################################################
# snactor files
##################################################
%files -n snactor
%license COPYING
%{leapp_python_sitelib}/leapp/snactor
%{_mandir}/man1/snactor.1*
%{_bindir}/snactor


##################################################
# python[23]-leapp files
##################################################
%files -n %{leapp_python_name}-%{name}
%license COPYING
%{leapp_python_sitelib}/*
# TODO: check valid entry points for leapp & snactor
# These are delivered in other subpackages
%exclude %{leapp_python_sitelib}/leapp/cli
%exclude %{leapp_python_sitelib}/leapp/snactor


%files deps
# no files here

%changelog
* Mon Apr 16 2018 Vinzenz Feenstra <evilissimo@gmail.com> - %{version}-%{release}
- Initial rpm
