.. Leapp documentation master file, created by
   sphinx-quickstart on Wed May 17 15:34:45 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Leapp's documentation!
=================================
   LeApp is a "Minimum Viable Migration" utility that aims to decouple virtualized applications from 
   the operating system kernel included in their VM image by migrating them into macrocontainers that 
   include all of the traditional components of a stateful VM (operating system user space, application 
   runtime, management tools, configuration files, etc), but use the kernel of the container host rather 
   than providing their own.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getstarted
   leapp-tool
   ui
   centosci




.. Indices and tables
.. ==================
.. 
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
