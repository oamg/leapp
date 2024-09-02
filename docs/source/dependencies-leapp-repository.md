# How to deal with dependencies in leapp-repository

First, read this
[document](dependencies)
to better understand the difficulties related to package dependencies in the
Leapp project.

When talking about RHEL 7 to RHEL 8 upgrade, the goal is to cover dependencies
of all Leapp project-related packages, including the leapp-repository packages,
for both RHEL 7 and RHEL 8. Since the situation with dependencies of the leapp
packages is similar to the situation with the leapp-repository dependencies,
this document focuses on the leapp-repository specifics only.

Currently there are two SPEC files for leapp-repository:

- The
[leapp-repository.spec](https://github.com/oamg/leapp-repository/blob/main/packaging/leapp-repository.spec)
file is used to build leapp-repository packages and their dependency
metapackage _leapp-repository-deps_ **for RHEL 7**.
- The
[leapp-el7toel8-deps.spec](https://github.com/oamg/leapp-repository/blob/main/packaging/leapp-el7toel8-deps.spec)
file is used to build dependency metapackages _leapp-deps-el8_ and
_leapp-repository-deps-el8_ **for RHEL 8** whose purpose is to replace the
RHEL 7 dependency metapackages _leapp-deps_ and _leapp-repository-deps_ during
the upgrade.

## What to do in leapp-repository when dependencies of leapp change?

Go to the section below the line `%package -n %{ldname}` in the
[leapp-el7toel8-deps.spec](https://github.com/oamg/leapp-repository/blob/main/packaging/leapp-el7toel8-deps.spec).
This section creates the RHEL 8 _leapp-deps-el8_ metapackage that replaces the
RHEL7 _leapp-deps_ metapackage. So when the leapp package dependencies change
in the [leapp.spec](https://github.com/oamg/leapp/blob/main/packaging/leapp.spec)
together with incrementing version of the **leapp-framework-dependencies**
capability, it's necessary to:

- provide the same **leapp-framework-dependencies** capability version
   by _leapp-deps-el8_

- decide if this dependency change also applies to RHEL 8 and if so, update
   the dependencies of the _leapp-deps-el8_ metapackage accordingly.

There can be another case when we need to modify dependencies of leapp on
RHEL 8, e.g. when a RHEL 7 package is renamed or split on RHEL 8. In such case
we don't need to modify the capability value, just update dependencies of the
_leapp-deps-el8_ metapackage, commenting it properly. Nothing else.

## What to do when leapp-repository dependencies need to change?

When you want to modify *outer dependencies* of leapp-repository packages, do
that similarly to instructions related to Leapp packages, following the same
rules. Just take care of the **leapp-repository-dependencies** capability
instead of the *leapp-framework-dependencies* capability. Everything else is
the same. Interesting parts of the SPEC files are highlighted in the same way
as described in the
[leapp dependencies document](dependencies).
