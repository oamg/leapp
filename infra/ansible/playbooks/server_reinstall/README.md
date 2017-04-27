# Redeploy leapp servers


## Install latest version of server-reinstall role 

```
ansible-galaxy install -r roles_file.yml -p ./roles/
```

## make sure you have the secrets repo at the same level with prototype repo

```
[vmindru@vmutil server_reinstall]$ ls -la ../../../../../
total 20
drwxrwxr-x.  5 vmindru vmindru 4096 Apr 10 08:35 .
drwxrwxr-x. 52 vmindru vmindru 4096 Apr 10 04:15 ..
drwxrwxr-x.  2 vmindru vmindru 4096 Apr 10 04:35 infra
drwxrwxr-x.  5 vmindru vmindru 4096 Apr 10 08:26 le-app-housekeeping
drwxrwxr-x. 11 vmindru vmindru 4096 Apr 10 07:05 prototype
[vmindru@vmutil server_reinstall]$
```

## execute the playbook against desired server. WARNING THIS WILL COMPLETLY REINSTALL THE TARGET MACHINE!!!!

note the comma after the FQDN, this is needed by ansible dyn inventory format


```
ansible-playbook -i le-app-02-server, playbooks/server_reinstall/server_reinstall.yml -u root
```
