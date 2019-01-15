# In-place upgrade workflow

---

[Click here to open a diagram  the phases](img/phases.png)

---

## FactsCollection
- Get information (facts) about the system (e.g. installed packages, configuration, ...). No decision should be done in this phase. Scan the system to get information you need and provide
it to other actors in the following phases.

## Checks
- Check upgradability of the system, produce user question if needed and produce output for the report. Check whether it is possible to upgrade the system and detect potential risks. It is not expected to get additional information about the system in this phase, but rather work with data provided by the actors from the FactsCollection. When a potential risk is detected for upgrade, produce messages for the Reports phase.

## Reports
- Provide user with the result of the checks.

## Download
- Download data needed for the upgrade and prepare RPM transaction for the upgrade.

## InterimPreparation
- Prepare an initial RAM file system (if required). Setup bootloader.

_(Reboot happens here between the phases)_

## InitRamStart
- Boot into the upgrade initramfs, mount disks, etc.

## LateTests
- Last tests before the RPM upgrade that have to be done with the new kernel and systemd.

## Preparation
- Prepare the environment to ascertain success of the RPM upgrade transaction.

## RPMUpgrade
- Perform the RPM transaction, i.e. upgrade the RPMs.

## Applications
- Perform the neccessary steps to finish upgrade of applications provided by Red Hat. This may include moving/renaming of configuration files, modifying configuration of applications to be able to run correctly and with as similar behaviour to the original as possible.

## ThirdPartyApplications
- Analogy to the Applications phase, but for third party and custom applications.

## Finalization
- Additional actions that should be done before rebooting into the upgraded system. For example SELinux relabeling.

_(Reboot happens here between the phases)_

## First Boot
- Actions to be done right after booting into the upgraded system.
