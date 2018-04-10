# Creating a new project for actor development

Leapp uses repositories with a defined [filesystem layout](best-practises.html#repository-directory-layout).
The snactor tool helps you to create a project repository, in which you can develop and test your
actors, tags, models, and topics.

To create a new project called *tutorial*, run the snactor tool:

```shell
    $ snactor new-project tutorial
```

Enter the tutorial folder where the project has been initialized, and see its content:

```shell
    $ cd tutorial
    $ ls -a
```

Now, you can start creating your actors, tags, models, and topics.

## A screen cast of the steps above

<asciinema-player src="_static/screencasts/create-project.json"></ascinema-player>
