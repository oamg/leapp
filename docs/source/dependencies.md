# How to deal with dependencies

RPM dependencies of Leapp packages can be grouped into two groups:

1. *inner dependencies* between Leapp-related packages
1. *outer dependencies* on packages not related to Leapp (e.g. python)

The first group is a standard RPM dependency management. But the
*outer dependencies* are really tricky. When a Leapp-related package needs such
a dependency, it has to depend on a special capability (below) and the required
dependency has to be set in a special metapackage which provides this
capability. At this point, the metapackage installed together with leapp
packages is named **leapp-deps**.

The capability (in case of the leapp tool, leapp framework, and snactor) is
called **leapp-framework-dependencies**. Every time the *outer* dependencies are
changed, the value of the capability has to be incremented by one - so the
information about the change is provided to other leapp-related packages.

This metapackage can be simply replaced by a metapackage that would handle
outer dependencies of the target system. That means, that the metapackage
with dependencies for the target system is not part of this git repository
and the actors of the leapp-repository are responsible for providing
such package in case it is needed.

## Why do I need to have a special way to define a dependency

One possible use of the Leapp framework is to do the in-place upgrade (IPU).
In that case, it is necessary to execute Leapp on two different
versions of the system - it starts with the source system and then continues
with the target (upgraded) system. It is quite common that some packages are
renamed between those two systems (or in case of leapp-repository, you would
like to use technology on the new system that is not provided on the original
one).
In such cases, it is hard to satisfy dependencies on both systems - when you
want to proceed with the upgrade process with the same Leapp packages.

As a solution, we are using the metapackage that contains those dependencies.

## What to do when dependencies needs to be changed

It's easy to change *outer dependencies* for Leapp. Open the
[packaging/leapp.spec](https://github.com/oamg/leapp/blob/master/packaging/leapp.spec) file and change the dependencies as needed under
`%package deps`. The right place is pretty highlighted (you cannot miss it):

```spec
##################################################
# Real requirements for the leapp HERE
##################################################
...
Requires: findutils
Requires: your-dependency
```

And do not forget to increment value of `leapp-framework-dependencies`:

```spec
# IMPORTANT: everytime the requirements are changed, increment number by one
# - same for Provides in deps subpackage
Requires: leapp-framework-dependencies = 1
```

**IMPORTANT** Do the same thing for all `Requires` and `Provides` of the
`leapp-framework-dependencies` capability in the SPEC file. Ensure that value
is consistent across the SPEC file.

### Some more unusual steps

There is an official
[Leapp repository](https://github.com/oamg/leapp-repository) that we manage
and it is already affected by such change. If you modify the
*outer dependencies*, inform the repository developers about the change (e.g.
[issue](https://github.com/oamg/leapp-repository/issues/new))
or even better, continue by following instructions in the
[doc](dependencies-leapp-repository.html)
to reflect the change.
