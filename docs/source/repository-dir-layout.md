# Repository Directory Layout

```
 .leapp/                                        # Repository information. Do not edit it manually.
 actors/                                        # All actors are stored here in subdirectories.
    actorname/                                  # An actor directory.
        actor.py                                # The actual actor code. The file name actor.py is required.
        Makefile                                # Optional makefile with target install-deps to install
                                                # actor's dependencies for tests execution.
        tests/                                  # Unit and component tests for the actors are to be stored here.
            unit_test_actorname.py              # should contain the actor name
            component_test_actorname.py         # should contain the actor name
            files/                              # If tests need to use some mocked files, they should be placed here
                                                # and referenced from the tests using path 'tests/files'.
        libraries/                              # Private libraries for the actors only.
            private_actorname.py                # These can be modules. Name should contain actor name
            actorpkg/                           # or packages.
                __init__.py
        tools/                                  # The path of this directory gets injected in the actors PATH
                                                # environment variable before their execution. These tools are private to
                                                # the actor.

        files/                                  # Files that are private to the actor only.

 files/                                         # Files that are shared with all actors (common files).

 libraries/                                     # Libraries that are shared with all actors.
    common.py                                   # These can be modules
    tests/                                      # with tests stored here.
        files/                                  # If tests need to use some mocked files, they should be placed here
                                                # and refenreced from the tests using path 'tests/files'.
        test_common.py
    sharedpkg/                                  # Or they can be packages
        __init__.py
        tests/                                  # with tests stored here.
            test_sharedpkg.py
            files/                              # If tests need to use some mocked files, they should be placed here
                                                # and refenreced from the tests using path 'sharedpkg/tests/files'.

 models/                                        # All models describing the message payload format are stored here.
    model.py

 tags/                                          # All tags for this repository are stored here.
    tag.py

 tools/                                         # The path of this directory gets injected in the PATH environment
                                                # variable before actors execution. These tools are shared with all actors.

 topics/                                        # All topics for this repository are stored here.
    topic.py

 workflows/                                     # Workflows are stored here.
    workflow.py
```
