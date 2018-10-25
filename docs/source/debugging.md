## Debugging

The snactor tool is used to debug your actors. You can execute actors
and save their output, so that it can be consumed by other actors. 
See [Storing messages in the repository data for reuse](messaging.html#storing-messages-in-the-repository-data-for-reuse).

For example, you can configure PyCharm to debug by pointing it to where the path to snactor is the Python
file, and pass the arguments on the command line.

The PyCharm debugger also follows the child processes that are created by the
snactor tool to execute the actor in a sandboxed environment.

The snactor tool checks for the `LEAPP_DEBUG` environment variable and has also
the --debug parameter which sets the environment variable to '1' when it is
used. In that case, it enables the debug logging, so that any actor that logs
to self.log.debug gets its output printed on the commandline.
