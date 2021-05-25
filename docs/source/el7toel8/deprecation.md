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

- Models
  - **RequiredTargetUserspacePackages** - Deprecated because the new solution has been designed. Use the `TargetUserspacePreupgradeTasks` instead (see the `install_rpms` field).
  - **RequiredUpgradeInitramPackages** - Deprecated because the new solution around the upgrade initramfs has been designed. Use the `TargetUserspaceUpgradeTasks` instead (see the `install_rpms` field).
  - **UpgradeDracutModule** - Replaced by `UpgradeInitramfsTasks` (see the `include_dracut_modules` field).
  - **InitrdIncludes** - Deprecated becase the new solution around the target initramfs (read: initramfs created for the upgraded system) has been designed. Use the `TargetInitramfsTasks` instead (see the `include_files` field).

## v0.12.0  <span style="font-size:0.5em; font-weight:normal">(till April  2021)</span>
- Models
   - **GrubDevice** - Deprecated because the current implementation is not reliable. GRUB device detection is now in the shared grub library. Use the `leapp.libraries.common.grub.get_grub_device()` function instead.
   - **UpdateGrub** - Deprecated because the current implementation is not reliable. GRUB device detection is now in the shared grub library. Use the `leapp.libraries.common.grub.get_grub_device()` function instead.
- Shared libraries
   - **`leapp.libraries.common.testutils.logger_mocked.warn()`** - The logging.warn method has been deprecated in Python since version  3.3. Use the warning method instead.

## v0.11.0 <span style="font-size:0.5em; font-weight:normal">(till April  2021)</span>
- Models
   - **TMPTargetRepositoriesFacts** - Deprecated because this model was not intended for customer use.


