Infras Ansible Playbooks
==============================

Ansible code.

Installing/Obtaining Ansible
----------------------------
The best way to obtain ansible is through your normal package manager, yum.
Ansible is shipped in Fedora by default, and is available for RHEL6 and RHEL7
from EPEL.


Install python module dependencies
---------------------------------------

Some features implemented as plugins, or Extras modules, require the installation
of python libraries to supplement the core functions of ansible.  To make this easy to
consume, the libraries can be installed using pip.

```
pip install --user -r requirements.txt
```

Utilising this repository
-------------------------
Once you have ansible above, you can checkout this repository and initilise all submodules underneath it
Then simply run playbooks from inside the top level directory (everything must be run from here for relative path settings to work)

```
ansible-playbook playbooks/path/to/playbook.yml
```

### playbooks
This directory contains the ansible playbooks that will be run by people or automated systems (such as jenkins) to perform tasks, deployments, etc. The structure is such that directly underneat this directory there will be a directory related to each product or unique environment (for systems we don't develop, e.g. QE CI Openstack). Under each product directory, the layout is less formalised, but ideally there should be a directory for each type of environment (devel/qa/stage/production) and the playbooks and any other bits and pieces (ansible-vault encrypted vars files as an example) should live there. Some playbooks relating to all environments may live directly under the product directory. The playbooks should be descriptively named and use dashes as spaces. Playbooks may perform steps for a targetted task, or deploy an application/tool. If deploying an application or tool, the playbook is responsible for
- Defining the hosts to use
- Pulling in any variables and any other external information needed
- Applying roles to systems, overriding variables for those roles with correct values relevant for this environment



