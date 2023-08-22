# Deprecated functionality in the el7toel8 repository

Deprecated functionality is listed under the first version that the functionality
is deprecated in. Note that functionality may be deprecated in later versions
but are not listed again.
The dates in brackets correspond to the end of the deprecation protection period,
after which the related functionality can be removed at any time.

*Note* The lists cover just the functionality provided inside the el7toel8
repository only. For the functionality deprecated in the leapp
framework, see [List of deprecated functionality in leapp](../deprecation.html#list-of-deprecated-functionality-in-leapp)

## current upstream development <span style="font-size:0.5em; font-weight:normal">(till the next release + 6months)</span>

- nothing yet...

## v0.19.0 <span style="font-size:0.5em; font-weight:normal">(till March 2024)</span>

- Models
  - **InstalledTargetKernelVersion** - Deprecated as the new solution has been designed to be able to handle new changes in RHEL 9.3+ system. Use the `InstalledTargetKernelInfo` message instead.
  - **GrubInfo.orig_device_name** - The `GrubInfo` message is still valid, but the `orig_device_name` field has been deprecated as multiple devices can exist on a system. Use `GrubInfo.orig_devices` instead.
- Shared libraries
  - **leapp.libraries.common.config.version.is_rhel_realtime()** - The function has been deprecated as the information cannot be easily determined based on the information inside `IPUConfig`. Use data in the `KernelInfo` message instead, the field `type`.
  - **leapp.libraries.common.grub.get_grub_device()** - The function has been deprecated as multiple grub devices can exists on a system. Use the `leapp.libraries.common.grub.get_grub_devices()` function instead.

## v0.16.0 <span style="font-size:0.5em; font-weight:normal">(till September 2022)</span>

- Shared libraries
    - **`leapp.libraries.common.utils.apply_yum_workaround`** - The `apply_yum_workaround` function has been deprecated, use `DNFWorkaround` message as used in the successing `RegisterYumAdjustment` actor.

## v0.15.0 <span style="font-size:0.5em; font-weight:normal">(till April 2022)</span>
- Models
  - **RequiredTargetUserspacePackages** - Deprecated because the new solution has been designed. Use the `TargetUserspacePreupgradeTasks` instead (see the `install_rpms` field).
  - **RequiredUpgradeInitramPackages** - Deprecated because the new solution around the upgrade initramfs has been designed. Use the `TargetUserspaceUpgradeTasks` instead (see the `install_rpms` field).
  - **UpgradeDracutModule** - Replaced by `UpgradeInitramfsTasks` (see the `include_dracut_modules` field).
  - **InitrdIncludes** - Deprecated because the new solution around the target initramfs (read: initramfs created for the upgraded system) has been designed. Use the `TargetInitramfsTasks` instead (see the `include_files` field).

## v0.12.0  <span style="font-size:0.5em; font-weight:normal">(till April  2021)</span>
- Models
   - **GrubDevice** - Deprecated because the current implementation is not reliable. GRUB device detection is now in the shared grub library. Use the `leapp.libraries.common.grub.get_grub_device()` function instead.
   - **UpdateGrub** - Deprecated because the current implementation is not reliable. GRUB device detection is now in the shared grub library. Use the `leapp.libraries.common.grub.get_grub_device()` function instead.
- Shared libraries
   - **`leapp.libraries.common.testutils.logger_mocked.warn()`** - The logging.warn method has been deprecated in Python since version  3.3. Use the warning method instead.

## v0.11.0 <span style="font-size:0.5em; font-weight:normal">(till April  2021)</span>
- Models
   - **TMPTargetRepositoriesFacts** - Deprecated because this model was not intended for customer use.


