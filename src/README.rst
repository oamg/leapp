LeApp: Macrocontainers for Legacy Applications
==============================================

LeApp is a "Minimum Viable Migration" utility that aims to
decouple virtualized applications from the operating system
kernel included in their VM image by migrating them into
macrocontainers that include all of the traditional components
of a stateful VM (operating system user space, application
runtime, management tools, configuration files, etc), but
use the kernel of the container host rather than providing
their own.

This approach to migration does *not* immediately take
advantage of all of the potential usability and
maintainability benefits offered by modern autoscaling
platforms, but may be sufficient to allow legacy
applications to be migrated and legacy hosting services
to be discontinued.

Installation
------------

Installation is currently only supported as part of
the LeApp Cockpit plugin demo or the LeApp integration
tests.