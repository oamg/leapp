# Building blocks and architecture
The leapp framework works with several entities. This document explains how the entities interact together and then the individual entities in more detail.

## Architecture overview
![Architecture overview](/_static/images/framework-arch-overview.png)

There are two tools for working with the framework, the end user application
`leapp` and the development utility `snactor`. The `leapp` tool is designed to
run specific workflows, while the `snactor` tool can run arbitrary workflows,
but also individual actors.

A *workflow* describes what work is going to be done and when. Each workflow consists
of a sequence of *phases*, which contain *actors* divided into three stages: before, main, and after. Workflows, actors, and all the parts necessary for
the execution are loaded from *repositories*. The phase to which actor belong is specified in it's definition via a *tag*.

Actors can pass data to actors futher in the workflow via *messages*, the structure of messages is defined by a *model*. Each actor declares messages of which model it *consumes* and *produces*.

For more information about each of the building blocks, see [this section](#entities-in-leapp).

### How is this different from Ansible?
Leapp is message-driven. The execution of actors is dependent on the data produced by other actors running before them. This data is passed around in the form of *messages*.
This is in a contrast with Ansible where everything has to be specified up front.

## Entities in Leapp

### Actor
An actor in terms of the Leapp project is a step that is executed within a
workflow. Actors define what kind of messages they expect, and what messages
they produce. Actors also provide a list of tags, with which actors mark their
use cases. Actors are defined as subclasses of the
{py:class}`leapp.actors.Actor` class.

Actors scan the system and produce the information found as messages. Other
actors consume those messages to make decisions, or process the data to produce
new messages. Some actors might apply changes to the system based on the
information gathered earlier.

Each actor is executed in a forked child process to prevent the modification of
the application state. All messages and logs produced by the actors are stored
in the *audit database*.

For instructions on how to create your own actors see the
{doc}`tutorials/first-actor` tutorial. {doc}`tutorials/unit-testing` and
{doc}`tutorials/debugging` cover unit testing and debugging, respectively.

### Message
A message is an object produced by an actor. The payload follows the definition
of the [Model](#model) it is named after. Messaging is a term used to describe
the data exchange between [actors](#actor).

See the {doc}`tutorials/messaging` tutorial for more information.

#### Report
A report is a special kind of message. The model for all reports is
{py:class}`leapp.reporting.Report`. Reports are produced just like an ordinary
message, however they are not consumed by any other actor. Instead the
contained information is presented to the user in the generated file at
`/var/log/leapp-report.txt` (with small portion summarized directly in the
output).

Reports can be used to inform the user about e.g. what will be done during the worflow or to *inhibit*.

There are helpers for producing reports in the {py:mod}`leapp.reporting` module.

### Model
Models are the definition of the data model used in [message](#message) payloads.
Each Model is a subclass of the {py:class}`leapp.models.Model` class.

### Phase
Phases are sections in a workflow dedicated to some specific area of execution.
A phase consists of three [stages](#stage): Before, Main, and After.
Phases are defined by assigning one or more tags to them, which will be used
to find actors in the loaded [repositories](#repository).

### Repository
A repository is the place where all actors, models, tags, topics, and workflows
are defined. In addition to those, shared files, libraries and tools can also
be put into the repository.
Repositories are defined by subclassing the {py:class}`leapp.repository.Repository`.

```{toctree}
repository-dir-layout
```

See the {doc}`tutorials/create-repository` tutorial for instructions on how to
create your own repositories.
Leapp also allows you to *link* repositories in order to use content from another repository this is covered in the {doc}`tutorials/repo-linking` tutorial.

### Stage
Stage is a part of a [phase](#phase). There are three defined stages:
- Before
- Main
- After

Before and After stages can be used to allow an actor to be run before or after any
other actors in the phase. This could be useful in some hooking scenarios, where
an action is supposed to be happening before or after another action. This way, other
actors could be influenced.

### Tag
A tag allows the framework to find [actors](#actor) in a [repository](#repository)
and group their execution based on that tag.
The base class for tags is {py:class}`leapp.tags.Tag`.

### Topic
Topics are assigned to models and are used for grouping the data into areas of interest.
The base clas for topics is {py:class}`leapp.topics.Topic`.

### Workflow
Workflows describe what work is going to be done and when. A workflow is
describing a sequence of phases, where each phase has assigned
{py:class}`~leapp.workflows.tagfilters.TagFilter`s with which the framework
selects actors that should be executed from the repositories on the system.
Workflows are defined by subclassing the {py:class}`leapp.workflows.Workflow`.

The {doc}`tutorials/working-with-workflows` tutorial goes through the creation of a workflow together with phases and inclusion of an actor.

### Workflow APIs
Workflow APIs are custom API classes that actors can use and automatically
inherit their consumed and produced messages. This way one can write a stable
API for third party actor writers, without being affected by changes of message
model layout, name changes etc.
