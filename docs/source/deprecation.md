# Deprecation

The deprecation process is here to make (your) life of developers easier.
It's not possible to write perfect solution for everything and as the project
is evolving, it happens that some functionality needs to be changed, replaced
or dropped completely. Such situations are inevitable. To reduce negative
impact on your code, we introduce the deprecation process described below.

## List of the deprecated functionality in leapp

The following lists cover deprecated functionality in the leapp utility, snactor,
the leapp standard library, etc. But don't cover deprecated functionalities
from particular leapp repositories (e.g. the [elt7toel8](https://github.com/oamg/leapp-repository/tree/master/repos/system_upgrade/el7toel8) leapp repository). For
such information, see [Deprecated functionality in the el7toel8 repository](../el7toel8/deprecation.md#deprecated-functionality-in-the-el7toel8-repository).

### current upstream development <span style="font-size:0.5em; font-weight:normal">(till the next release + 6months)</span>

- nothing yet...

### v0.15.0 <span style="font-size:0.5em; font-weight:normal">(till Mar 2023)</span>

- Reporting primitives
    - **`leapp.reporting.Flags`** - The `Flags` report primitive has been deprecated in favor of the more general `Groups` one.
    - **`leapp.reporting.Tags`** - The `Tags` report primitive has been deprecated in favor of the more general `Groups` one.

## What is covered by deprecation process in leapp?

In short, leapp entities that are supposed to be used by other developers.
That means e.g.:

1. Models
1. Shared library classes and functions in leapp repository
1. Public APIs
1. Actors providing functionality that could be used by any developer (produce
   or consume messages)

In other words, private classes, private functions or anything in private
libraries, may be modified or removed without the deprecation process. As well,
it's possible we will need to change something (e.g. a behaviour of a function)
that will not be possible to cover reasonably by the deprecation process (e.g.
change output of the function...). We'll try our best to prevent it, but it may
happen. To limit such problems, we recommend people to use APIs as much
as possible.

## What does it mean that something is deprecated?

When you deprecate something, the only thing that changes is that the
deprecated entity is marked in the code as deprecated which can have
additional impact, like messages produced on the user's terminal,
in the report, ... But the rest of the functionality is the same as before,
until the entity is removed completely.

## What is the deprecation process for leapp?


In case a leapp entity covered by the deprecation process is to be removed for
any reason, it needs to be marked as deprecated before the removal (if
possible). The deprecation will be applied only for leapp entities that have
been introduced in an official release in RHEL (IOW, a functionality
that has been merged into the upstream, but has been removed before the release
or was marked as experimental all the time, is going to be removed without
the deprecation state). The time period during which the deprecated entity
won't be removed is at least 6 months. That doesn't mean we will remove
everything deprecated immediately after the 6 months, but it's to be expected
that it will be dropped anytime between 6 and 12 months since the deprecation.

In case of issues, deprecated entities are not going to be fixed since
they are deprecated (unless they are fixed e.g. as a side-effect of another
problem fix).

## How do I find out what is deprecated?

Mainly via release notes and changelogs. In the official leapp related projects
(especially leapp and leapp-repository) the OAMG team takes care of release
notes to ensure they inform about the dropped and deprecated functionality.

Additionally, when using leapp or snactor, user is notified via messages about
deprecated entities in **limited cases** (see below). In case of the leapp
utility, such messages are presented inside the generated reports. In case
of the snactor utility, the information message is printed in the console
output at the end of the snactor execution. See examples in this page for
detail.

Please note, that the Deprecation warning is emitted only if:
- the deprecated class is instantiated
- the deprecated function is called
