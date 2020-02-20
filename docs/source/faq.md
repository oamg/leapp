# Frequently Asked Questions

- [What is Leapp?](#what-is-leapp)
- [How can I get on board with contributing to Leapp?](#how-can-i-get-on-board-with-contributing-to-leapp)
- [What is an actor and what does it do?](#what-is-an-actor-and-what-does-it-do)
- [When and why do I need to write an actor?](#when-and-why-do-i-need-to-write-an-actor)
- [How can I exchange any data between actors?](#how-can-i-exchange-any-data-between-actors)
- [What do I have to do in order to execute actor I just wrote?](#what-do-i-have-to-do-in-order-to-execute-actor-i-just-wrote)
- [What should I do if I need to execute multiple actors? Can I somehow ensure the dependencies between them?](#what-should-i-do-if-i-need-to-execute-multiple-actors-can-i-somehow-ensure-the-dependencies-between-them)
- [How can I specify what run time dependencies will my actor have?](#how-can-i-specify-what-run-time-dependencies-will-my-actor-have)
- [How can I distinguish between actors that I depend on directly (I need to consume their output) and indirectly (I just need them to be executed as part of the upgrade as I don’t handle the upgrade of that specific piece; think PHP vs. Apache - upgrade of Apache is independent of the upgrade of PHP but it needs to be done to enable its upgrade)?](#how-can-i-distinguish-between-actors-that-i-depend-on-directly-i-need-to-consume-their-output-and-indirectly-i-just-need-them-to-be-executed-as-part-of-the-upgrade-as-i-don-t-handle-the-upgrade-of-that-specific-piece-think-php-vs-apache-upgrade-of-apache-is-independent-of-the-upgrade-of-php-but-it-needs-to-be-done-to-enable-its-upgrade)
- [Once I write an actor that consumes data from some other actors, how can I be sure that the format will not change on the producing side in the future?](#once-i-write-an-actor-that-consumes-data-from-some-other-actors-how-can-i-be-sure-that-the-format-will-not-change-on-the-producing-side-in-the-future)
- [What are the best practices for writing actors?](#what-are-the-best-practices-for-writing-actors)
- [What are the requirements for actors to be accepted by upstream?](#what-are-the-requirements-for-actors-to-be-accepted-by-upstream)
- [How can I debug my actor? Is there a standard/supported way how to log and get logs from actors/channels?](#what-are-the-requirements-for-actors-to-be-accepted-by-upstream)
- [Are there some technical limitations for an actor? E.g. maximum time execution, size of the input/output, libraries I can use… In case there are, is it possible to specify that the actor needs e.g. longer time for execution?](#are-there-some-technical-limitations-for-an-actor-e-g-maximum-time-execution-size-of-the-input-output-libraries-i-can-use-in-case-there-are-is-it-possible-to-specify-that-the-actor-needs-e-g-longer-time-for-execution)
- [Are there some actions that are either forbidden or not recommended to be done in actors?](#are-there-some-actions-that-are-either-forbidden-or-not-recommended-to-be-done-in-actors)
- [I got an error about PES data/ Repositories mapping where I find such files?](#i-got-an-error-about-pes-data-repositories-mapping-where-i-find-such-files)

## What is Leapp?

Leapp project aims to enable users to modernize their existing workloads without disrupting them in three different ways: upgrading them in place, migrating them to a different place or containerize them. Currently, the in-place upgrade functionality is being worked on only.

## How can I get on board with contributing to Leapp?

For the Leapp framework we are currently developing the functionality for the in-place upgrade of RHEL 7 to RHEL 8. You can improve the user experience of the upgrade by creating so called actors for the Leapp framework. We've written a quick guide on how to create such actors for the RHEL 7 to RHEL 8 upgrades: [How to create a Leapp actor for RHEL 7 to 8 upgrade.](el7toel8/actor-rhel7-to-rhel8)

## What is an actor and what does it do?

An actor in the realm of the Leapp project is a step that is executed within a workflow. Actors define what kind of data they expect and what kind of data they produce.

One of the use cases for actors is to scan the system and provide the discoveries to other actors through messages. Other actors consume these messages to make decisions, apply changes to the system, or process the information to produce new messages.

## When and why do I need to write an actor?

In regards to the upgrades of RHEL 7 to RHEL 8, Leapp should be able to upgrade all the RHEL 7 packages that Red Hat supports to their RHEL 8 equivalents. If it is not possible to upgrade a package, Leapp needs to at least report it to the user. It is a shared responsibility of a) the Leapp developers and b) the development leads of the RHEL 8 subsystems owning RHEL 7 packages. That means that if you are an owner of a package in RHEL 7, you might be approached by your subsystem development lead to analyze the "upgradeability" of the package from RHEL 7 to RHEL 8. If there is any incompatibility between those packages or any aspect that could negatively impact the upgrade user experience, then that's the reason for creating an actor - to make the upgrade experience of the user as smooth as possible. As to when to write such an actor, that is up to discussion among the leads of OAMG, working on Leapp, and your subsystem leads, to set the milestones for the actor development, testing and release.

## How can I exchange any data between actors?

All communication between actors in Leapp is carried out using " messages". An actor can consume or produce messages. A message may contain any data, but the data needs to be in a specific format defined by a "model". If an actor wants to consume a message produced by another actor, it needs to specify the specific model of the consumed messages. Leapp will make sure to execute such an actor only after some message of the specified model was produced by another actor. If no message of the specified model was produced in previous phases or in the current phase, the consuming actor will get no messages of that kind.
Source: [How to create a Leapp actor for RHEL 7 to 8 upgrade](el7toel8/actor-rhel7-to-rhel8)

## What do I have to do in order to execute actor I just wrote?

If you want to execute just a single actor when developing it, then use the snactor tool. [Here's a tutorial](first-actor) on how to use it.
If you want to add your actor to an existing workflow, for example the RHEL 7 to 8 upgrade workflow, then tag your actor with appropriate workflow and phase tags.
Source: [How to create a Leapp actor for RHEL 7 to 8 upgrade](el7toel8/actor-rhel7-to-rhel8)

## What should I do if I need to execute multiple actors? Can I somehow ensure the dependencies between them?

To be sure that your ActorA runs before your ActorB, produce a specific message in ActorA and let ActorB consume it. By doing this you create a dependency of ActorB on ActorA.
To run just your actors during development, use snactor run --save-output ActorA to save the message of ActorA to the Leapp repository database and then snactor run ActorB. This way, the ActorB will be able to consume the ActorA's saved message. Read more about that in the [tutorial about messaging](messaging).

## How can I specify what run time dependencies will my actor have?

See the section about dependencies in the [Best practices document](best-practices.html#do-not-introduce-new-dependencies)

## How can I distinguish between actors that I depend on directly (I need to consume their output) and indirectly (I just need them to be executed as part of the upgrade as I don't handle the upgrade of that specific piece; think PHP vs. Apache - upgrade of Apache is independent of the upgrade of PHP but it needs to be done to enable its upgrade)?

In the case of actors you depend on directly because you consume their message, you don't need to do anything extra, the Leapp framework will make sure that the actors that produce the messages you consume are executed before your actor.
In case of the actors you depend on indirectly you may approach it in various ways:

- Talk to the developers of the actors you depend on indirectly and agree on sending a message between their actors and your actor. This will cause a direct dependency described above.
- Talk to the [Engineering Lead](contributing.html#contact) of the OS and Application Modernization group and tell them to coordinate development, testing and release of your actor and the actors you depend on indirectly, targeting the same milestone.

## Once I write an actor that consumes data from some other actors, how can I be sure that the format will not change on the producing side in the future?

The format of a message is specified in a message model. You cannot, however, be sure that the model for the messages you're consuming will not change in the future. If that happens, the CI should report errors in the pull request in which the changes to the model are introduced. But for the CI to find out the issue, you as an actor developer need to write thorough unit tests to cover this eventuality.

## What are the best practices for writing actors?

Read the [Best practices for writing actors](best-practices).

## What are the requirements for actors to be accepted by upstream?

It should follow the [Contribution guidelines](contributing) and the [Best practices for writing actors](best-practices) as much as feasible.

## How can I debug my actor? Is there a standard/supported way how to log and get logs from actors/channels?

You can run your actor using the snactor tool and printing the output. [See the tutorial](first-actor) on how to use snactor.
Source: [How to create a Leapp actor for RHEL 7 to 8 upgrade](el7toel8/actor-rhel7-to-rhel8)

## Are there some technical limitations for an actor? E.g. maximum time execution, size of the input/output, libraries I can use... In case there are, is it possible to specify that the actor needs e.g. longer time for execution?

There are no technical limitations but rather conceptual:

- Libraries to use:
  - See the section about actor dependencies in the [Best practices document](best-practices.html#do-not-introduce-new-dependencies)

Execution time:

- Some Red Hat customers do business in fields where time matters a lot. They may have obligations to not allow more than a few minutes of downtime per year. It means that we should make sure that our tooling causes as short downtime as possible.
- It's not currently possible to tell the Leapp framework that the actor takes longer time to execute.

## Are there some actions that are either forbidden or not recommended to be done in actors?

In regards to the RHEL 7 to RHEL 8 in-place upgrades, the rule is to not alter the system in any way before the point of no return, which is the start of the RPMUpgrade phase running in the initramfs. Any deviation from this rule must be well justified.

## I got an error about PES data/ Repositories mapping where I find such files?

These files can not be packaged together in Leapp RPM for license reasons.

For information on how to get these files, please read this [article](https://access.redhat.com/articles/3664871).
