## Terminology

### Actor

An actor in terms of the Leapp project is a step that is executed within a workflow.
Actors define what kind of data they expect, and what they produce. Actors also
provide a list of tags, with which actors mark their use cases.

Actors scan the system and produce the information found as messages.
Other actors consume those messages to make decisions, or process the data
to produce new messages.
Some actors might apply changes to the system based on the information gathered earlier.

### Message

A message is produced by an actor, and the payload follows the definition of the [Model](#model)
it is named after. Messaging is a term used to describe the data exchange between [actors](#actor).

### Model

Models are the definition of the data model used in [message](#message) payloads.

### Phase

Phases are sections in a workflow dedicated to some specific area of execution.
A phase consists of three [stages](#stage): Before, Main, and After.
Phases are defined by assigning one or more tags to them, which will be used
to find actors in the [repositories](#repository) loaded.

### Repository

A repository is the place where all actors, models, tags, topics, and workflows are defined.
Additionally to that shared files, libraries and tools can be put into the repository.

### Stage

Stage is a part of a [phase](#phase). There are three defined stages:
- Before
- Main
- After

Before and After phases can be used to allow an actor to be run before or after any
other actors in the phase. This should be useful in some hooking scenarios, where
an action is supposed to be happening before or after another action. This way, other
actors could be influenced.

### Tag

A tag allows the framework to find [actors](#actor) in the [repository](#repository)
and group their execution based on that tag.

### Topic

Topics are assigned to models and are used for grouping the data into areas of interest.

### Workflow

Workflows describe what work is going to be done and when. A workflow is describing a sequence of phases,
where one phase has assigned filters with which the framework selects actors that should be executed from
the repositories on the system.

