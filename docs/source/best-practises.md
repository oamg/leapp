# Best Practises


### Actors are written Python

Actors are written in Python, and should be written as such to be able to run with Python 2.7 or Python 3.
For this, we depend on the six library to help with some of the differences between Python versions. And it can be safely imported
on module level.

### Avoid running the code on a module level

Actors are completely written in Python, however, they are loaded beforehand to get all the meta-information from the actors.
To avoid slow downs we ask actor writers not to execute any code that is not absolutely necessary on a module level.

### Avoid global non Leapp imports

Avoid importing system or bundled libraries on a module level. This again has to do with slow down, and also to avoid
unnecessary complications for our tests automation which needs to inspect the actors beforehand.

### Follow the Leapp Python Coding Guidelines

See the [Python Coding Guidelines](python-coding-guidelines).

### Use the snactor tool

Using the snactor tool provides you with all minimally necessary layouts of the repository, and creates
things like topics and tags.

It helps you with debugging, and it is able to execute individual actors. The snactor tool has also the ability to discover all the entities in your current project repository,
such as actors, models, tags, topics, and workflows.

### Avoid writing generic actors (TBD)

Generic actors that are too abstract are usually a sign for code that should be a shared library instead.
Shared libraries help to reduce the complexity of the system, and the amount of actors that have to be scheduled and run.




