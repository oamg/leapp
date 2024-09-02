# Naming schema of Leapp-related packages

All projects under the OAMG should use the same schema for names of RPM builds,
to be able to simply and fast find specific builds. The schema itself looks
like that (NVR without %{dist}):

- for builds made from the main branch:
```
<name>-<version>-100.<timestamp>.<short-hash>.<branch>
```
- for builds made from pull-request:
```
<name>-<version>-0.<timestamp>.<short-hash>.<branch>.PR<number>
```

Where:
- **name** is name of the project
- **version** is current version of the application
- **timestamp** in format: `+%Y%m%d%H%MZ`, e.g. "201812211407Z"
- **short-hash** is shortened hash of the commit from which the build has been
  created
- **branch** is name of the branch from which the builds has been created;
  in case the name of the branch contains dashes (`-`), these are automatically
  replaced by underscore (`_`) because dash is used as a separator in the name
  of a (S)RPM file; so it is suggested (not required) to to avoid dashes
  in names of branches
- **number** is number of a pull-request (alternatively merge-request) to which
  builds are related
