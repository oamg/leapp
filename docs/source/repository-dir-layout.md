# Repository Directory Layout

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