# Installing the actor development environment

This demo encourages to use virtualenv to setup the actor development environment.

First step to do so, is to create a new virtualenv called tut and activate it
```shell
	$ cd ~/devel
	$ virtualenv -p /usr/bin/python2.7 tut
	$ . tut/bin/activate
```

Next we will install the framework via pip
```shell
	$ pip install git+https://github.com/leapp-to/leapp-actors-stdlib
```

Once the framework is installed in your virtualenv environment you can start using the snactor tool.
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

## A screen cast of the steps above

<asciinema-player src="_static/screencasts/install.json"></ascinema-player>
