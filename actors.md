# What is an actor?
An actor in terms of the Leapp project is a step that is executed within a workflow. Actors define what kind of data they expect and what kind of data they produce. Actors also provide a list of tags, with which actors mark their use cases.

Actors scan the system and produce the found information as messages. Other actors consume those messages to make decisions, or process the data to produce new messages. Some actors might apply changes to the system based on the information gathered earlier.


# Do I need to write actors and why?
There are multiple situations in which you will need to write your own actors. For example, if you want to migrate or upgrade an application that is not supported by the leapp tool or a supported application with a special configuration that cannot be migrated or upgraded by using default actors. Another situation might be that you want to introduce a new functionality using the Leapp framework.

To learn how to write actors, see the [tutorial](http://leapp.readthedocs.io/en/latest/tutorials.html).
Follow the [contributing guidelines for writing actors](https://github.com/oamg/leapp-repository/blob/master/CONTRIBUTING.md).
