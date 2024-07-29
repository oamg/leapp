## Debugging actors

### Snactor

The snactor tool is used to debug your actors. You can execute actors
and save their output, so that it can be consumed by other actors.
See [Storing messages in the repository data for reuse](messaging.md#storing-messages-in-the-repository-data-for-reuse).

Snactor checks for the `LEAPP_DEBUG` environment variable and has also
the --debug parameter which sets the environment variable to '1' when it is
used. In that case, it enables the debug logging, so that any actor that logs
to self.log.debug gets its output printed on the commandline.

### PyCharm / rpdb

You can configure PyCharm to debug by pointing it to the snactor path and passing the arguments on the command line.
The PyCharm debugger will also follow the child processes that are created by the snactor tool to execute the actor
in a sandboxed environment.

Not everywhere you'll have PyCharm at hand but vim/nc lightweight tandem is already in place in majority of cases.
It's possible to go minimal and debug actor execution with remote debugger like
[rpdb](https://pypi.org/project/rpdb/). The setup is as simple as:

1. Add breakpoint at the desired place in actor's code `import rpdb; rpdb.set_trace()`
2. Run snactor and wait till breakpoint is hit.
3. In a separate console connect to the debugger via network utility of your choice. The default port is 4444.

```nc localhost 4444```
