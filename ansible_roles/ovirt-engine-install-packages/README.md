oVirt Engine Install Packages
=============================

This role installs all necessary packages for oVirt engine deployment.

Target Systems
--------------

* engine


Requirements
------------

Preinstalled clean environment with configured repositories.

Role Variables
--------------

None

Dependencies
------------

* ovirt-common

Example Playbook
----------------

```yaml
---
- hosts: engine
  roles:
    - ovirt-engine-install-packages
```

Author Information
------------------

Petr Kubica
pkubica@redhat.com
