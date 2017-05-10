# VM Definitions for vagrant 

## ading new box 

to add a new demo add a new folder with following structure

```
vmdefs/enabled/centos6-drools-guest/
├── ansible.cfg
├── playbook.yml
└── Vagrantfile
```

## enabling boxes 

create symlink of a box from ./available to ./enabled e.g.
to enable drools app one would do following, note the '../'
```
[vmindru@vmutil vmdefs]$ ln -s ../available/centos6-drools-guest/ ./enabled/
```
## controling boxes 


