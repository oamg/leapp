%global debug_package %{nil}
Name:       leapp
Version:    0.3
Release:    1%{?dist}
Summary:    Utility for VM migration to a container(s) and upgrade tool

Group:      Unspecified
License:    ASL 2.0
URL:        https://github.com/leapp-to/leapp
Source0:    leapp-build.tar.gz

# leapp-go
BuildRequires:   golang
BuildRequires:   make
BuildRequires:   git
BuildRequires:   golang-github-gorilla-mux-devel
BuildRequires:   golang-github-pkg-errors-devel
BuildRequires:   golang-github-mattn-go-sqlite3-devel

# snactor
BuildRequires:   python2-devel
BuildRequires:   PyYAML
BuildRequires:   python2-jsl
BuildRequires:   python2-jsonschema
%if 0%{?rhel} && 0%{?rhel} <= 7
BuildRequires:   python-setuptools
BuildRequires:   epel-rpm-macros
%else
%if 0%{?fedora} > 25
BuildRequires:   python2-pytest-cov
BuildRequires:   python2-pytest-flake8
%endif
BuildRequires:   python2-setuptools
BuildRequires:   python-rpm-macros
%endif

Requires:       ansible
Requires:       PyYAML
Requires:       python2-jsl
Requires:       python2-jsonschema
%if 0%{?rhel} && 0%{?rhel} <= 7
Requires:       python-six
BuildRequires:       python-six
%else
Requires:       python2-six
BuildRequires:       python-six
%endif

%description

%prep
%autosetup -n leapp-build

%build
pushd snactor
%py2_build
popd
pushd leappctl
%py2_build
popd

pushd leapp-actors
make build
popd

pushd leapp-go
mkdir -p TMP_BUILD/src/github.com/leapp-to/
ln -s $PWD TMP_BUILD/src/github.com/leapp-to/leapp-go
export GOPATH=$PWD/TMP_BUILD
export GOBIN=$GOPATH/bin
cd $GOPATH/src/github.com/leapp-to/leapp-go
make install-deps
make build
popd

%install
pushd snactor
%py2_install
echo Starting to copy data from: $PWD
install -dm 0755 %{buildroot}%{_datadir}/%{name}
cp -r examples/* %{buildroot}%{_datadir}/%{name}/
install -dm 0755 %{buildroot}%{_libexecdir}/%{name}/
mv %{buildroot}%{_bindir}/snactor_runner %{buildroot}%{_libexecdir}/%{name}/snactor_runner
popd

pushd leappctl
%py2_install
popd

pushd leapp-actors
make install ROOT_PATH=%{buildroot}/usr/share/leapp
popd

pushd leapp-go
make install PREFIX=%{buildroot}
popd

%check
pushd snactor
%if 0%{?fedora} <= 25 || (0%{?rhel} && 0%{?rhel} <= 7)
echo 'Skipping tests due to missing dependencies'
%else
make test
%endif
popd


%files
%doc snactor/README.md snactor/LICENSE
%{python2_sitelib}/*
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/scripts/*
%{_datadir}/%{name}/actors/*
%{_datadir}/%{name}/schemas/*
%{_datadir}/%{name}/playbooks/*
%{_libexecdir}/%{name}/leapp-daemon
%{_libexecdir}/%{name}/actor-stdout
%{_libexecdir}/%{name}/snactor_runner
%{_bindir}/leappctl

%changelog
* Tue Jan 23 2018 Jozef Zigmund <jzigmund@redhat.com> 0.3-1
- initial RPM package

