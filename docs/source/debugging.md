## Debugging

The snactor tool is the perfect tool to debug your actors, you can execute an actor
and save their output so it can be fed into another actor. 
[Click here for more](messaging.html#storing-messages-in-the-project-data-for-reuse)

One can configure for example PyCharm to debug by pointing it to where snactor is the python
file and pass the arguments on the command line.

The pycharm debugger is able to easily follow the child processes that are created by
snactor to execute the actor in a kind of sandboxed environment.

The snactor tool has also the --debug parameter and checks fo the environment variable
`LEAPP_DEBUG` if it set to '1'
In that case it will enable the debug logging. So any actor that logs to self.log.debug
will get its output printed on the commandline.

