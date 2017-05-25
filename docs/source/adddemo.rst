Create new demo
===============


Adding new vagrant box 
^^^^^^^^^^^^^^^^^^^^^^

To add a new demo add a new folder with following structure. ::

    vmdefs/enabled/centos6-drools-guest/
    ├── ansible.cfg
    ├── playbook.yml
    └── Vagrantfile

Enabling boxes 
^^^^^^^^^^^^^^

Create symlink of a box from ./available to ./enabled e.g.
to enable drools app one would do following, note the '../'.
Make sure you are inside ./prototype/vmdefs while creating symlink, 
since symlink path is relative to the symlink location. ::

    cd ./vmdefs/
    ln -s ../available/centos6-drools-guest/ ./enabled/

Controlling boxes 
^^^^^^^^^^^^^^^^^

All the actions are done using vmctl.sh script

**usage:** 
    ./vmctl.sh [ stop|start|provision|destroy]

*e.g.  starting new boxes* ::

    cd demo
    ./vmctl.sh provision

*e.g. remove all boxes* ::

    cd demo
    ./vmctl.sh destroy





