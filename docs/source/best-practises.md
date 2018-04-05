# Best Practises

## Content Organziation

### Repository Directory Layout

```
 .leapp/                            # Repository information - DO NOT EDIT MANUALLY 
 actors/                            # Here are all actors stored within sub directories
    actor-name/                     # An actor's directory
        actor.py                    # The actual actor code - actor.py is by convention is not optional        
        tests/                      # Required tests for the actor are stored here
            test_actor_name.py
        libraries/                  # Private libraries for the actor only
            private.py              # Can be modules
            actorpkg/               # or packages
                __init__.py
        tools/                      # The path of this directory gets injected in the actors PATH
                                    # environment variable before execution these tools are private to
                                    # the actor

        files/                      # Files that are private to the actor only

 files/                             # Files that are shared with all actors (common files)

 libraries/                         # Libraries that are shared with all actors
    common.py                       # Can be modules
    sharedpkg/                      # or packages
        __init__.py

 models/                            # Here we store all models describing the message payload format
    model.py                        

 tags/                              # Here we store all tags for this repository
    tag.py

 tools/                             # The path of this directory gets injected in the PATH environment
                                    # variable before execution these tools are shared with all actors

 topics/                            # Here we store all topics for this repository
    topic.py

 workflows/                         # Workflows are stored here
    workflow.py
```

## Guidelines

### Actors are written Python

Actors are written in Python and should be written as such that they can run with Python 2.7 and Python 3.
For this we depend on the six package to help with some of the percularities. And it can be safely imported
on module level.

### Avoid running code on module level

Actors are completely written in Python code however are loaded before hand to get all information from the actor.
To avoid slow downs we ask actor writers not to execute any code that is not absolutely necessary on module level.

### Avoid global non leapp imports 

Avoid importing system or bundled libraries on module level. This again has to do with slow down, but also to avoid
unnecessary complications for our tests automation which needs to inspect the actors before hand.

### Follow the Leapp Python Coding Guidlines

See the [Python Coding Guidelines](python-coding-guidelines)

### Use the snactor tool

Using the snactor tool will provide you with all minimally necessary layouts of the repository and creates
things like topics and tags completely for you.

It can help you with debugging and is able to execute individual actors and discovers all the actors around.

### Avoid writing generic actors (TBD)

Generic actors that are too abstract are usually a sign for code that should be a shared library instead.
This will reduce the complexity of the system and the amount of actors that have to be scheduled and run.


