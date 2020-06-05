## Deprecation

To help with the deprecation process of entities in leapp, the leapp framework introduced a decorator `deprecated`
which can be imported from `leapp.utils.deprecation`.

This decorator will mark items as being deprecated and ensures that a deprecation warning is displayed if this item
is being used.

### Warning message display behaviour

Warning messages are always shown after `snactor` executions via `snactor run` or `snactor workflow run`.
At the end of executions of `leapp upgrade` or `leapp preupgrade` the warnings are added as report entries with a
developer audience. If the deprecation is less than 6 months old the severity is set to 'MEDIUM' if it is older than
6 months the severity is set to 'HIGH'

#### snactor warning message example

```
============================================================
                 USE OF DEPRECATED ENTITIES
============================================================

Usage of deprecated function "deprecated_function" @ /Users/vfeenstr/devel/work/leapp/leapp/tests/data/deprecation-tests/actors/deprecationtests/actor.py:19
Near:         deprecated_function()

Reason: This function is no longer supported.
------------------------------------------------------------
Usage of deprecated Model "DeprecatedModel" @ /Users/vfeenstr/devel/work/leapp/leapp/tests/data/deprecation-tests/actors/deprecationtests/actor.py:20
Near:         self.produce(DeprecatedModel())

Reason: This model is deprecated - Please do not use it anymore
------------------------------------------------------------
Usage of deprecated class "DeprecatedNoInit" @ /Users/vfeenstr/devel/work/leapp/leapp/tests/data/deprecation-tests/actors/deprecationtests/actor.py:21
Near:         DeprecatedNoInit()

Reason: Deprecated class without __init__
------------------------------------------------------------
Usage of deprecated class "DeprecatedBaseNoInit" @ /Users/vfeenstr/devel/work/leapp/leapp/tests/data/deprecation-tests/actors/deprecationtests/actor.py:22
Near:         DeprecatedNoInitDerived()

Reason: Deprecated base class without __init__
------------------------------------------------------------
Usage of deprecated class "DeprecatedWithInit" @ /Users/vfeenstr/devel/work/leapp/leapp/tests/data/deprecation-tests/actors/deprecationtests/actor.py:23
Near:         DeprecatedWithInit()

Reason: Deprecated class with __init__
------------------------------------------------------------

============================================================
             END OF USE OF DEPRECATED ENTITIES
============================================================
```

#### leapp report example entries

```
----------------------------------------
Risk Factor: medium
Title: Usage of deprecated class "IsolatedActions" at /usr/share/leapp-repository/repositories/system_upgrade/el7toel8/libraries/repofileutils.py:38
Summary: IsolatedActions are deprecated
Since: 2020-01-02
Location: /usr/share/leapp-repository/repositories/system_upgrade/el7toel8/libraries/repofileutils.py:38
Near: def get_parsed_repofiles(context=mounting.NotIsolatedActions(base_dir='/')):

----------------------------------------
Risk Factor: medium
Title: Usage of deprecated class "IsolatedActions" at /usr/share/leapp-repository/repositories/system_upgrade/el7toel8/actors/scansubscriptionmanagerinfo/libraries/scanrhsm.py:8
Summary: IsolatedActions are deprecated
Since: 2020-01-02
Location: /usr/share/leapp-repository/repositories/system_upgrade/el7toel8/actors/scansubscriptionmanagerinfo/libraries/scanrhsm.py:8
Near:     context = NotIsolatedActions(base_dir='/')

----------------------------------------
Risk Factor: medium
Title: Usage of deprecated function "deprecated_method" at /usr/share/leapp-repository/repositories/system_upgrade/el7toel8/actors/deprecationdemo/actor.py:21
Summary: Deprecated for Demo!
Since: 2020-06-17
Location: /usr/share/leapp-repository/repositories/system_upgrade/el7toel8/actors/deprecationdemo/actor.py:21
Near:         self.deprecated_method()

----------------------------------------
```

## Usage examples of @deprecated

### Functions

```python
...
from leapp.utils.deprecation import deprecated


@deprecated(since='2020-06-20', message='This function has been deprecated!')
def some_deprecated_function(a, b, c):
    pass
```

### Models

```python
...
from leapp.utils.deprecation import deprecated


@deprecated(since='2020-06-20', message='This model has been deprecated!')
class MyModel(Model):
    topic = SomeTopic
    some_field = fields.String()
```

### Classes

```python
...
from leapp.utils.deprecation import deprecated


@deprecated(since='2020-06-20', message='This class has been deprecated!')
class MyClass(object):
    pass


# NOTE: Here we need to offset the stacklevel to get the report of the usage not in the derived class constructor
# but where the derived class has been created.
# How many levels you need, you will have to test, it depends on if you use the builtin __init__ methods or not,
# however it gives you the ability to go up the stack until you reach the position you need to.
@deprecated(since='2020-06-20', message='This class has been deprecated!', stack_level_offset=1)
class ABaseClass(object):
    def __init__(self):
        pass


class ADerivedClass(ABaseClass)
    def __init__(self):
        super(ADerivedClass, self).__init__()
```
