# Environment variables for el7toel8 repository

Actors in the el7toel8 repository use environment variables specified below.
All these envars use the suggested prefixes specified in
[the best practices document](../best-practices#use-the-leapp-and-leapp-devel-prefixes-for-new-envars)
for the leapp project to distinguish their purpose: *production* or *devel* use.

If the argument for envars below is not specified, it is expected to set `0`
(false) or `1` (true).

## LEAPP_NO_RHSM

Do not use Red Hat Subscription Management for the upgrade. Using it has the
same effect as using the `--no-rhsm` leapp option.

## LEAPP_OVL_SIZE

For any partition that uses XFS with the ftype option set to 0, Leapp is
creating a file of a specific size in order to proceed with the upgrade.
By default, the size of that file is 2048 MB. In case the size needs to be
increased, Leapp informs you in the pre-upgrade report that the environment
variable needs to be specified.


## LEAPP_DEBUG

Enables debug logging. Equivalent to `--debug`, which takes precedence.


## LEAPP_VERBOSE

Enables debug logging. Equivalent to `--verbose`, which takes precedence.


## LEAPP_CONFIG

Overrides the default location of `leapp.conf`. If not specified,
`leapp/leapp.conf` is used when the command is executed inside a leapp
repository, otherwise the default `/etc/leapp/leapp.conf` is used.


## LEAPP_LOGGER_CONFIG

Overrides the default location of `logger.conf`. If not specified, the default
`/etc/leapp/logger.conf` is used.


## LEAPP_UNSUPPORTED

Necessary to use in case you use any envar with the LEAPP_DEVEL prefix
(see the list below). And in case you use the --whitelist-experimental option
for the Leapp tool.


## LEAPP_DEVEL_RPMS_ALL_SIGNED

Leapp will consider all installed pkgs to be signed by RH - that affects
the upgrade process as by default Leapp upgrades only pkgs signed by RH.
Leapp takes care of the RPM transaction (and behaviour of applications)
related to only pkgs signed by Red Hat. What happens with the non-RH signed
RPMs is undefined.


## LEAPP_DEVEL_TARGET_RELEASE

Change the default target RHEL 8 minor version.


## LEAPP_DEVEL_SKIP_CHECK_OS_RELEASE

Do not check whether the source RHEL 7 version is the supported one.
E.g. right now Leapp does not allow you to proceed with the upgrade
when you’re not on RHEL 7.6.


## LEAPP_DEVEL_DM_DISABLE_UDEV

Setting the environment variable provides a more convenient
way of disabling udev support in libdevmapper, dmsetup and LVM2 tools globally
without a need to modify any existing configuration settings.
This is mostly useful if the system environment does not use udev.


## LEAPP_DEVEL_SOURCE_PRODUCT_TYPE

By default the upgrade is processed from the GA (general availability) system
using GA repositories. In case you need to do the in-place upgrade from
Beta or HTB system, use the variable to tell which of those you would like
to use. It's case insesitive. The `ga` value is the default.
Expected values: `ga`, `beta`, `htb`.


## LEAPP_DEVEL_TARGET_PRODUCT_TYPE

Analogy to the LEAPP_DEVEL_SOURCE_PRODUCT_TYPE envar, just for the target
system this time. Again, `ga` is the default.
