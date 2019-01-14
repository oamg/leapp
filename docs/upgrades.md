# In-place upgrade workflow

---

[Click here to open diagram of the phases](img/phases.png)

---

## Facts Collection
- Operating System Version Detection, IP, Hostname, RPMs, Services, Augeas run

## Checks
- ### Preupgrade Checks
 - Inhibitors - Blockers, Shared Objects, Binaries, Languages, Packages, Load Balance Support, User Management, Version Control Systems, FreeRADIUS, IPA Bind Dyndb LDAP, SSSD, NTP, OpenLDAP, YPSERV, Network, Databases, SELinux, Storage, System

- ### Services
 - HTTPD, OpenSSH, Postfix, SQUID, DoveCot, Bind9 Configuration

- ### Backup
 - Untracked Files

- ### Others
 - RSYSLOG

## Report
- Provide user with the result of the checks
- Let user interactively decide on multiple-choice solution for specific upgrade issues

## Attach package repositories
- Make sure the repositories of the new system are available

## Planning
- RPM Install transaction (feasibility checks)

## Download
- Download of all things needed (RPMs, Kernel images, Anaconda image (very big maybe), etc.)

## Upgrade RamDisk Preparation
- Preparation of initial ramdisk (if required)
- Setup bootloaderGrub

## Upgrade RamDisk Start (Actual reboot)
- Reboot into the next system therefore not a real step, however the before and post parts are interesting to have for hooking

## Network
- Bring up the network

## Storage
- Mount all storage points

## Late Tests
- Tests that need to be executed later

## Preparation
- YUM Configurations
- Backup not upgradable configurations (No Verify Configs)

## RPM Upgrade
- Upgrade RPMs
- Check all files are installed (troubles with handling dirs/symlinks), includes reinstallation of affected packages

## Application Upgrade
- Application of changes on configuration files, move various directores, etc.

## Third Party Applications
- A place for custom actors for third party applications to be upgraded

## Finalization
- Plan SELinux relabeling
- Labels Bootloader settings

## Reboot
- Reboot into the new system

## First Boot
