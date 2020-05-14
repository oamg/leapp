# Tests for actors

The Leapp actors are covered by three types of tests - unit, component and e2e.

## Unit and component tests

- Both unit and component tests are to be placed in the actor's _tests_ folder.
- Unit and component tests modules should have unique names
- Tutorial on [How to write unit and component tests](unit-testing)

### Unit tests

- These tests deal with individual actor's functions/methods.
- It's not possible to unit test any method/function within the *actor.py*. You can write unit tests only for functions/methods within the actor's libraries.
- Thus, to be able to write unit tests for an actor, ideally the only thing in the _actor.py_'s _process()_ method is calling the entry-point function of the actor's library python module.
- [Example of unit tests](https://github.com/oamg/leapp-repository/blob/master/repos/system_upgrade/el7toel8/actors/checkbootavailspace/tests/unit_test_checkbootavailspace.py)

### Component tests

- These tests provide fabricated input messages for the actor, check the outputs stated in the actor's description.
- These tests should not be written based on the actor's code but rather based on the behavior stated in the actor's description. They could be written by somebody who didn't write the code.
- [Example of component tests](https://github.com/oamg/leapp-repository/blob/master/repos/system_upgrade/el7toel8/actors/checknfs/tests/test_checknfs.py)

## End to end (e2e) tests

- The Leapp QA team maintains an internal testing framework facilitating e2e tests.
- [Members of the *oamg* GitHub organization] can trigger execution of the e2e tests by adding the comment 'e2e tests' under an opened *leapp* or *leapp-repository* PR
