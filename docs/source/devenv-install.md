# Installing the actor development environment

This demo uses the virtualenv tool to set up the actor development environment.

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

## A screen cast of the steps above

<asciinema-player src="_static/screencasts/install.json"></ascinema-player>
