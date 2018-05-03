## Debugging

The snactor tool is used to debug your actors. You can execute actors
and save their output, so that it can be consumed by other actors. 
See [Storing messages in the project data for reuse](messaging.html#storing-messages-in-the-project-data-for-reuse).

For example, you can configure PyCharm to debug by pointing it to where the path to snactor is the Python
file, and pass the arguments on the command line.

The PyCharm debugger also follows the child processes that are created by the
snactor tool to execute the actor in a sandboxed environment.

The snactor tool has also the --debug parameter and checks for the environment variable
`LEAPP_DEBUG` if it is set to '1'.
In that case, it enables the debug logging, so that any actor that logs to self.log.debug
gets its output printed on the commandline.
