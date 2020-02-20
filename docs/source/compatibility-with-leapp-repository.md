# Compatibility between leapp and leapp repositories

There is a hidden dragon in the split of leapp framework and leapp repositories
projects. The development of features and incompatible changes has different
speed in both projects. We want to release our projects using semantic
versioning and, at the same time, we do not want to release a new version of
the project after each merge of a new feature or incompatible change.
We rather prefer releasing new versions with changelogs and everything
when we agree it's worthwhile.

But we need a mechanism to be able to synchronize with other projects, when we
provide new functionality in the upstream (master) branch without the need
of immadiate release of the new version of leapp. For these purposes the
`leapp-framework` capability is provided in the framework (python[23]-leapp) rpms.

## When and how change the capability

The `leapp-framework` capability has to be changed in case of any change of
provided API (e.g. change in the leapp standard library) or functionality that
could affect actors in leapp repositories. That includes new features as well
as an actor may depend on that in future, and the leapp-repository package
should be able to specify correct framework version that is needed.

The `leapp-framework` capability uses just `X.Y` versioning:

- In case of a change breaking previous functionality (e.g. changed a name of a function) provided by the framework, bump `X` and set `Y` to 0.
- In case of a new feature (e.g. new function in stdlib), which doesn't affect already existing actors, bump `Y`

The value of the capability should be bumped per PR providing all changes.
IOW, when a PR implements two compatible/incompatible changes in several
commits, the value should be bumped only once!

As well it is recommended to mentioned the value of the capability
(when changed) in the commit msg, so it the tracking is easy.

## Suggested dependency in leapp-repository rpms
We suggest to set dependency on the `leapp-framework` capability in any rpm
that contains leapp repositories in this way:

```spec
Requires:       leapp-framework >= 1.2, leapp-framework < 2
```

Which means, that you want to install framework of version at least 1.2 but
lower than 2 (e.g. 1.99).

### Possible issue
There is unfortunately one issue with the above solution. As far as there is just
one rpm providing that capability, it's ok. The problem occurs on systems where
there will be more rpms (of different name) providing the capability.
So in case you are able to install e.g. python2-leapp and python3-leapp rpms
on the system, you could end up with:

- python2-leapp providing leapp-framework 1.0, and
- python3-leapp providing leapp-framework 3.0

which both are broken for leapp repository and the dependency from the point of
rpms is satisfied. This should happen rarely. We suggest you to ensure that you
use such repositories where only one of those rpms exists.
