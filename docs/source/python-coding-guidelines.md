Coding Guidelines for the Leapp project
=======================================

While code stylistics (naming, whitespace, structure) is mostly handled by the famous PEP8 - https://www.python.org/dev/peps/pep-0008/
there's still much to be defined and codified in terms of code semantics, which is equally important as the overall style.
Purpose of these guidelines is to reduce the *cognitive load* necessary to read through & understand the code base.

### 1. Avoid Inheriting from Multiple Classes

Python uses something called C3 Linearization (https://en.wikipedia.org/wiki/C3_linearization)
to figure out the method resolution order and, as you can see, the logic behind the algorithm is non-trivial - dragging
that context in your head all the time is, costly and unnecessary, given the particularly *little benefit* of using
multiple inheritance in the first place.

### 2. Avoid Operator Overloading

With the exception of mathematics there's usually very little reason for succumbing to the mysterious and
arcane arts of operator overloading. Why is math OK? Because operator overloading makes it consistent
with how *everybody* assumes the given operator works given how it works in math itself.
There's little benefit in operator overloading otherwise, because different people have different assumptions
and while you think that it's pretty clear that invalid state should make the object equal to `None`, well, pretty
much everyone else is going to find this behavior confusing (http://stackoverflow.com/questions/371266/checking-c-sharp-new-initialisation-for-null/371286),
because it's just not how the rest of the ecosystem works. Going back to math, for the same reason you wouldn't like `3 + 3 = 7` because
someone decided that the symbols for addition now should return `a + b + 1`, don't put such constructs in code.
The situation is much worse because Python isn't statically typed, so even if you knew that `SomeCrazyClass` overloads
some particular operator, you might have no idea that `some_var` even *is* an instance of `SomeCrazyClass`.

### 3. Avoid 'In-Your-Face' error/exception messages

Exceptions or terminal error messages should *always* give you enough context to either fix the problem on the OS level, if applicable, or
know the exact location and reason why the error was raised, given you need to fix it in code.
Even some shady corners of Python base library will sometimes simply tell you `Permission denied` when you're trying to access
a resource for which you don't have sufficient permission, which makes the message exceptionally unhelpful in case your application
manages multiple resources in a loop. All you end up doing is catch and re-raise the exception with more helpful message.

#### 3.1. Type Your Exceptions

Raise `ValueError` or `TypeError` when validating input parameters. Use custom exception hierarchy with `Exception` at its root for
raising errors related to application logic itself. Callers of your code then have fine grained control over various
failure modes, which will always help at making the code more robust.

### 4. Avoid `**kwargs` like a plague

Probably apart from function decorators, there's no legitimate reason for including `**kwargs` in your function signatures, ever.
Think of function signatures in terms of binding contracts between *caller* and *callee*, the caller knows how to invoke
the particular function (callee) simply by looking at the signature. In the context of contracts, `**kwargs` essentially
feels like "whatever, dude", because in the best case scenario the valid kwargs are documented in the function's doc string
(which is still going to stop code completion tools to a grinding halt), in the worst case you are going on a chase and will need
to inspect the code of at least one function body - granted the `**kwargs` are not passed around like a hot potato, in which case
your best bet is to resurrect the long forgotten art of "printf debugging" and sprinkle the code with a bunch of `print` calls
here and there.

### 5. Import things the right way

Avoid wildcard * imports. So called "Star" imports import every module member that's name doesn't start with `_` into the current scope,
which can quickly lead to name clashes and funny errors.

Do not make relative imports.

Imported modules should be divided into 3 groups stdlib/third-party/project in the following order separated
by a single newline; each group should be sorted alphabetically by full module/object name.

If you need to use plenty of members from some module, use the `import module` syntax rather than `from module import foo`.
Always use `import module` syntax for python standard library, specifically instead of `from os.path import join` use `import os`.

Sort imported modules as well as all imported functions by name, alphabetically. Our brains are very good at bi-secting names
in alphabetical order.

Unless you have a really good reason, don't make local imports in function body.

### 6. Avoid Using Assertions For Control Flow & Mutating Operations

Assertions are, idiomatically, used to verify very basic assumptions about the code. It is assumed that once the code has been
stressed enough without triggering any assertion errors the code should be just fine. In C, for example, assertions are not
evaluated in non-debug builds. In Python, assertions are ignored if you execute your code with `-O` flag.
This also means that if the right-hand side of the assertion mutates certain state, the action *is not* carried out.

### 7. Avoid Map, Reduce and Too Complex Comprehensions

While one might say that writing out for loops makes the code look dumb and uninteresting, it also makes it
obvious and easy to understand, which are qualities, not defects. Code that uses map/reduce or several levels
of nested dictionary and list comprehensions almost always looks scary and it's very hard to deduce the
data flow of that particular piece of code.

### 8. Avoid Deeply Nested Block Scopes

In other words, high cyclomatic complexity is bad (https://en.wikipedia.org/wiki/Cyclomatic_complexity). Reasoning about code
with so much noise around is difficult, however, there are several ways how to avoid this situation. Instead of `if someCond:`
followed a by a huge chunk of code, consider the pattern of *eager returns* and simply return as soon as possible
`if not someCond: return` so that the following block doesn't need to be nested. This is of course not applicable for all
dark corners of cyclomatic complexity, for nested loops you might want to consider refactoring each loop into it's own
function or method. While the code will get a little more verbose, and you might face other difficulties like having to pass
around variables or even promoting some to instance variables, the resulting code is still much simpler to read then
condensed web of loops mutating maybe tens of local variables.

### 9. Write Docstrings That Work Well With Tools

The preferable way of writing docstrings for functions and methods is to use the first style mentioned at
(https://pythonhosted.org/an_example_pypi_project/sphinx.html#function-definitions). Plenty of editors or plugins are able
to parse these docstrings and provide targeted code completion and rudimentary validation. For consistency all docstrings
should start and end with `"""`.

### 10. Avoid Shadowing Python Builtins

type, file, id, map, filter, etc. have already been taken, be creative and invent your own object names.

### 11. String Formatting

#### 11.1 Prefer [new style](https://docs.python.org/3/library/string.html#string-formatting) String Formatting To [old style](https://docs.python.org/2/library/stdtypes.html#string-formatting)

Though there is still a mixture of formatting styles remaining in leapp code base, this rule stands for
all new contributions.
Please use

```
new_style = "{}! {} is coming".format("Brace yourself", "Winter")
```

instead of

```
old_style_refactor_me = "%s! %s is coming!" % ("Brace yourself", "Winter")
old_style_refactor_me = "%(msg)s! %(obj)s is coming!" % {"msg": "Brace yourself", "obj": "Winter"}
```

#### 11.2 Use Keyword Arguments To Increase Readability

If you pass more than 2 arguments to format function, please invoke format with keyword arguments.
```
msg_many_args = "{who} {when} {what}".format(who="A Lanister", when="always", what="pays his debts")
```

### 12. Docstrings

Follow [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257)
  - with the exception, that the summary line of a multi-line docstring shall be on a new line, not on the same line as the opening quotes.

There are some minimal requirements for the information that actor docstrings should provide, to learn more about the specifics please
consult the [contribution guidelines](contributing).

This is example how to write docstrings:

```python
class MyActor(Actor):
    """
    Start with a single-line brief summary of the actor (under the triple quotes).

    Leave a blank line below the summary and then describe the actor's behaviour
    here in detail.
    """
    name = 'my_actor'

    def process(self):
        """This is a simple method."""
        complicated_method(True)

    def complicated_method(switch):
        """
        This is a summary line of a more complicated method.

        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc porta sed
        urna venenatis faucibus. Phasellus at bibendum ligula, a posuere metus.

        :param switch: Description of the parameter.
        :type switch: Expected type of the parameter.
        :return: Description of what the method returns
        """
        mutliline_string = (
            'I am a multiline string.\n'
            'This is my second line.'
        )
        return mutliline_string
```

### 13. Underscore usage

For leapp and leapp-repository the `_` and `P_` is reserved for localization. Please don't use it for anything else like
variable-to-be-discarded.  Instead, use a variable name prefixed with `dummy_`.  What comes after
the prefix should describe the data that is being discarded, like so:

``` python
dummy_scheme, netloc, path, dummy_params, query, fragment = urlparse("scheme://netloc/path;parameters?query#fragment")
```

Using an informative variable name for discarded values is helpful when a future developer modifies
the code and needs the discarded information.  They can quickly see that the information is already
available; they just need to rename the variable and start using it.
