# Architecture overview

![Architecture overview](/_static/images/framework-arch-overview.png)

There are two tools for working with the framework, the end user application `leapp` and the development utility `snactor`. The `leapp` tool is designed to run specific workflows, while the `snactor` tool can run arbitrary workflows, but also individual actors.

A *workflow* describes what work is going to be done and when. Each workflow is made of a sequence of *phases*, which contain *actors* split into three stages - before, main, and after. Workflows, actors, and all the parts necessary for the execution are loaded from repositories.

Each actor is executed in a forked child process to prevent the modification of the application state. All messages and logs produced by the actors are stored in the *audit database*.

For more information about each part of the architecture, check the [terminology](terminology).

### How is this different from Ansible?

Leapp is message-driven. The execution of actors is dependent on the data produced by other actors running before them. This data is passed around in the form of *messages*.
This is in a contrast with Ansible where everything has to be specified up front.
