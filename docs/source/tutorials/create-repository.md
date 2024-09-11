# Creating a new repository for actor development

Leapp uses repositories with a defined [filesystem layout](../repository-dir-layout).
The snactor tool helps you to create a repository repository, in which you can develop and test your
actors, tags, models, and topics.

To create a new repository called *tutorial*, run the snactor tool:

```shell
    $ snactor repo new tutorial
```

Enter the tutorial folder where the repository has been initialized, and see its content:

```shell
    $ cd tutorial
    $ ls -a
```

Now, you can start creating your actors, tags, models, and topics.

## A screen cast of the steps above

<asciinema-player src="_static/screencasts/create-repository.json"></ascinema-player>
