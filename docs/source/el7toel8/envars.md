# Environment variables for the el7toel8 repository

Actors in the el7toel8 repository use environment variables specified below.
All these envars use the suggested prefixes specified in
[the best practices document](../best-practices#use-the-leapp-and-leapp-devel-prefixes-for-new-envars)
for the leapp project to distinguish their purpose: _production_ or _devel_ use.

If the argument for envars below is not specified, it is expected to set `0`
(false) or `1` (true).

## LEAPP_GRUB_DEVICE

Overrides the automatically detected storage device with GRUB core (e.g.
/dev/sda).

## LEAPP_NO_RHSM

If set to 1, Leapp does not use Red Hat Subscription Management for the upgrade.
It's equivalent to the `--no-rhsm` leapp option.


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

## LEAPP_ENABLE_REPOS

Specify repositories (repoids) split by comma, that should be used during the
in-place upgrade to the target system. It's overwritten automatically in case
the `--enablerepo` option of the leapp utility is used. It's recommended to use
the `--enablerepo` option instead of the envar.

## LEAPP_SERVICE_HOST

Overrides the host of the service to which leapp connects to fetch necessary
data files in case they are missing. The used protocol (`http://` or
`https://`) must be specified. Defaults to `https://cert.cloud.redhat.com`.

## LEAPP_PROXY_HOST

If set, leapp will use this proxy to fetch necessary data files in case they
are missing. The used protocol (`http://` or `https://`) must be specified.

## LEAPP_TARGET_PRODUCT_CHANNEL

The alternative to the `--channel` leapp option. As a parameter accepts
a channel acronym. E.g. `eus` or `e4s`. For more info, see the
`leapp preupgrade --help`.
In case the beta channel is required, use the LEAPP_DEVEL_TARGET_PRODUCT_TYPE
envar instead.

## LEAPP_NO_NETWORK_RENAMING

If set to 1, the actor responsible to handle NICs names ends without doing
anything. The actor usually creates UDEV rules to preserve original NICs in
case they are changed. However, in some cases it's not wanted and it leads
in malfunction network configuration (e.g. in case the bonding is configured
on the system). It's expected that NICs have to be handled manually if needed.

## LEAPP_DATABASE_FORCE_SYNC_ON

If set to 1, Leapp will explicitly enable synchronization on the SQLite database.
Enabling the synchronization has negative impact on the performance
(sometimes very negative). However, it is more reliable in case of extreme
situations (e.g. lost power).
Note the synchronization is nowadays switched off by default only during the phases
executed before the reboot of the system to the upgrade environment, which we consider
safe. As a result, we do not expect that someone would want to use this option now.

## LEAPP_NO_INSIGHTS_REGISTER

If set to 1, Leapp does not register the system into Red Hat Insights automatically.
It's equivalent to the `--no-insights-register` leapp option.

## LEAPP_NO_RHSM_FACTS
If set to 1, Leapp does not store migration information using Red Hat Subscription Manager.
It's equivalent to the `--no-rhsm-facts` leapp option.

## LEAPP_NOGPGCHECK
Set to 1 to disable RPM GPG checks (same as yum/dnf --nogpgckeck option).
It's equivalent to the `--nogpgcheck` leapp option.

## LEAPP_TARGET_ISO
Set the path to the target OS ISO image that should be used for the IPU.
It's equivalent to the `--iso` leapp option.


## LEAPP_UNSUPPORTED

Necessary to use in case you use any envar with the LEAPP_DEVEL prefix
(see the list below). And in case you use the --whitelist-experimental option
for the Leapp tool.

# Development environment variables for the el7toel8 repository

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
when you’re not on RHEL 7.9.

## LEAPP_DEVEL_DM_DISABLE_UDEV

Setting the environment variable provides a more convenient
way of disabling udev support in libdevmapper, dmsetup and LVM2 tools globally
without a need to modify any existing configuration settings.
This is mostly useful if the system environment does not use udev.

## LEAPP_DEVEL_SOURCE_PRODUCT_TYPE

By default the upgrade is processed from the GA (general availability) system
using GA repositories. In case you need to do the in-place upgrade from
a Beta system, use the variable to tell which of those you would like
to use. The value is case insensitive and the default value is `ga`.
Expected values: `ga`, `beta`.

## LEAPP_DEVEL_TARGET_PRODUCT_TYPE

`LEAPP_DEVEL_TARGET_PRODUCT_TYPE` is an analogy to
`LEAPP_DEVEL_SOURCE_PRODUCT_TYPE` for the target system and an extension to
`LEAPP_TARGET_PRODUCT_CHANNEL`. If used, it replaces any value set via the
`--channel` option or through the `LEAPP_TARGET_PRODUCT_CHANNEL` environment
variable . It consumes the same set of values as the `--channel` option, and
can be extended with the value `beta`. This is the only way how to perform the
inplace upgrade to a beta version of the target system using the
subscription-manager.

## LEAPP_DEVEL_USE_PERSISTENT_PACKAGE_CACHE

Caches downloaded packages when equal to 1. This will reduce the time needed
by leapp, when executed multiple times, because it will not have to download
already downloaded packages. However, this can lead to a random issues in case
the data is not fresh or changes of settings and repositories. The environment
variable is meant to be used only for the part before the reboot and has no
effect or use otherwise.

## LEAPP_DEVEL_DATABASE_SYNC_OFF

If set to 1, leapp will disable explicit synchronization on the SQLite
database. The positive effect is significant speed up of the leapp execution,
however it comes at the cost of risking a corrupted database, so it is
currently used for testing / development purposes, only.

## LEAPP_DEVEL_INITRAM_NETWORK
You can specify one of the following values: 'network-manager', 'scripts'.
The 'scripts' value is used for a legacy dracut module when the network is not
handled by NetworkManager.
Using the option allows experimental upgrades, bringing up the networking inside
the upgrade initramfs environment (upgrade phases after the first reboot).
It also allows the upgrade e.g. when a network based storage is used
on the system. Currently it works only for the most simple configurations
(e.g. when only 1 NIC is present, no rdma, no bonding, ...). Network based
storage is not handled anyhow during the upgrade, so it's possible that the network
based storage will not be correctly initialized and usable as expected).

