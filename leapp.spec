Name:		leapp
Version:	0.3
Release:	1%{?dist}
Summary:	Leapp is an OS & Application modernization framework

License:	ASL 2.0
URL:		https://leapp-to.github.io
Source0:	

BuildRequires:	
Requires:	

%description


%prep
%setup -q


%build
%configure
make %{?_smp_mflags}


%install
%make_install


%files
%doc



%changelog

