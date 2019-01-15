# Installing Leapp 

Leapp is currently installable from RPM packages prepared for [Fedora](#fedora) 26, 27, and 28, [CentOS 7](#centos-7), and [Red Hat Enterprise Linux 7](#rhel-7).

If you are using a different distribution, or you want to build and install Leapp on your own, follow these [instructions](http://leapp.readthedocs.io/en/latest/devenv-install.html).

## Fedora

Enable the Leapp Copr repository. Then, install Leapp.

```shell
sudo dnf install -y dnf-plugins-core
sudo dnf copr enable -y @leapp/leapp-devel
sudo dnf install -y leapp
```

## CentOS 7

Add the Leapp Copr repository and install Leapp.

```shell
sudo yum install -y yum-plugins-copr
sudo yum copr enable -y @leapp/leapp-devel
sudo yum install -y leapp
```

## Red Hat Enterprise Linux 7

Add the Leapp Copr repository and install Leapp.

```shell
sudo curl https://copr.fedorainfracloud.org/coprs/g/leapp/leapp-devel/repo/epel-7/group_leapp-leapp-devel-epel-7.repo -o /etc/yum.repos.d/group_leapp-leapp-devel-epel-7.repo
sudo yum install -y leapp
```

# The leapp tool

The `leapp` tool is an end-user application designed to run specific workflows. To run custom workflows or create actors, use the `snactor` utility. To learn how to create your own actors and workflows, see the [tutorial](http://leapp.readthedocs.io/en/latest/tutorials.html).

We are currently providing a workflow for upgrading systems:

```shell
leapp upgrade
```

Some phases of an upgrade workflow will reboot the system, and you will need to resume the leapp tool.

```shell
leapp upgrade --resume
```


For more information about the Leapp project, see the [documentation](http://leapp.readthedocs.io/en/latest/index.html).

