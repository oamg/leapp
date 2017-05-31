oVirt Engine Setup
==================

Generate answerfile and run engine-setup with it.

Target Systems
--------------

* engine

Requirements
------------

Preinstalled clean environment with configured repositories.

Role Variables
--------------

By default engine-setup uses answer file specific for version of oVirt,
based on ``ovirt_engine_version`` parameter. You can specify own answer file
as ``ovirt_engine_answer_file_path``.

```yaml
---
ovirt_engine_type: Type of product 'ovirt-engine' - for installing oVirt product
ovirt_engine_version: Allowed version: [3.6, 4.0, 4.1]
ovirt_engine_dwh: Bool value for installing local DWH (default: true)
# ovirt_engine_answer_file_path: /path/to/custom/answerfile

ovirt_engine_db_host: IP or hostname of PostgreSQL server for engine database (default: 'localhost')
ovirt_engine_db_port: Server listening port (default 5432)
ovirt_engine_db_name: DB name for ovirt-engine (default: 'engine')
ovirt_engine_db_user: DB user which can access ovirt-engine DB (default: 'engine')
ovirt_engine_db_password: password for user of ovirt-engine DB

ovirt_engine_dwh_db_host: IP or hostname of PostgreSQL server for DWH database (default: 'localhost')
ovirt_engine_dwh_db_port: Server listening port (default 5432)
ovirt_engine_dwh_db_name: DB name for ovirt-engine-dwh (default: 'ovirt_engine_history')
ovirt_engine_dwh_db_user: DB user which can access ovirt-engine-dwh DB (default: 'ovirt_engine_history')
ovirt_engine_dwh_db_password: password for user of ovirt-engine DB

# ISO domain related options
ovirt_engine_configure_iso_domain: Whether to confiure ISO domain on engine (default False)
ovirt_engine_iso_domain_path: Create local ISO domain on engine machine (default: /var/lib/exports/iso)
ovirt_engine_iso_domain_name: Name of ISO domain (default: 'ISO_DOMAIN')
ovirt_engine_iso_domain_acl: ACL permissions for ISO domain mount point (default: '0.0.0.0/0.0.0.0(rw)')

# Configure firewall
ovirt_engine_firewall_manager: |
  In case you want to configure firewall, select the firewall manager
  'firewalld', 'iptables' (default='firewalld'), or put null otherwise.
```

Dependencies
------------

* ovirt-engine-install-packages

Example Playbook
----------------

```yaml
---
- hosts: engine
  vars:
    ovirt_engine_type: 'ovirt-engine'
    ovirt_engine_version: '4.1'
    ovirt_engine_organization: 'of.ovirt.engine.com'
    ovirt_engine_admin_password: 'secret'
  roles:
    - ovirt-engine-setup
```

Author Information
------------------

Petr Kubica
pkubica@redhat.com
