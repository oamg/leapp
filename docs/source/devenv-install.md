# Installing development environment

## RPM packages installation

If you don't want to modify the framework itself you should install it from
rpm's provided by [Copr](https://copr.fedorainfracloud.org/coprs/g/leapp/leapp-devel/)
build system, which automatically builds on every commit merged into master.
Packages are built for Epel and Fedora.

```shell
    yum install -y yum-utils
    yum-config-manager --add-repo https://copr.fedorainfracloud.org/coprs/g/leapp/leapp-devel/repo/epel-7/group_leapp-leapp-devel-epel-7.repo
```

For actor development install `leapp` and `snactor`. This will pull in also
`leapp-repository` with actors.


```shell
    yum install snactor leapp
```

For snactor development install `snactor` (and if you want to use actors also `leapp-repository`).

```shell
    yum install snactor leapp-repository
```

## Virtualenv installation

However if you want to hack the framework itself or keep your envronment clean
the best way is to use a virtualenv.

First, create a new virtual environment called "tut" and activate it:
```shell
	$ cd ~/devel
	$ virtualenv -p /usr/bin/python2.7 tut
	$ . tut/bin/activate
```

Then, install the framework by using the pip package management system:
```shell
	$ pip install git+https://github.com/leapp-to/leapp
```

Once the framework is installed in your virtual environment, you can start using the snactor tool.
```shell
	$ snactor -h
	Usage: snactor [OPTIONS] COMMAND [ARGS]...

	  This tool is designed to get quickly started with leapp actor development

	Options:
	  --debug / --no-debug
	  --version             Show the version and exit.
	  -h, --help            Show this message and exit.

	Commands:
	  discover
	  dump
	  new
	  new-actor
	  new-topic
	  new-model
	  new-project
	  new-tag
	  run
	  runx
	  workflow
```

### A screen cast of the steps above

<asciinema-player src="_static/screencasts/install.json"></ascinema-player>
