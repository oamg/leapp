# Best Practises

## Content Organization

### Repository Directory Layout

```
 .leapp/                            # Repository information. Do not edit it manually.
 actors/                            # All actors are stored here in subdirectories.
    actor-name/                     # An actor directory.
        actor.py                    # The actual actor code. The file name actor.py is required.
        Makefile                    # Optional makefile with target install-deps to install
                                    # actor's dependencies
        tests/                      # Required tests for the actors are stored here.
            test_actor_name.py
        libraries/                  # Private libraries for the actors only.
            private.py              # These can be modules
            actorpkg/               # or packages.
                __init__.py
        tools/                      # The path of this directory gets injected in the actors PATH
                                    # environment variable before their execution. These tools are private to
                                    # the actor.

        files/                      # Files that are private to the actor only.

 files/                             # Files that are shared with all actors (common files).

 libraries/                         # Libraries that are shared with all actors.
    common.py                       # These can be modules
    sharedpkg/                      # or packages.
        __init__.py

 models/                            # All models describing the message payload format are stored here.
    model.py

 tags/                              # All tags for this repository are stored here.
    tag.py

 tools/                             # The path of this directory gets injected in the PATH environment
                                    # variable before actors execution. These tools are shared with all actors.

 topics/                            # All topics for this repository are stored here.
    topic.py

 workflows/                         # Workflows are stored here.
    workflow.py
```

## Guidelines

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




