# Creating a new project for actor development

Leapp uses repositories with a defined [filesystem layout](best-practises.html#repository-directory-layout)
The snactor tool helps you to create a project repository in which you can develop and test your
actors, tags, models and topics.

To create a new project called *tutorial* you run the snactor tool like this:

```shell
    $ snactor new-project tutorial
```

Now you can enter the tutorial folder in which the project has been initialized:

```shell
    $ cd tutorial
    $ ls -a
```

From here you can start creating your actors, tags, models and topics.

## A screen cast of the steps above

<asciinema-player src="_static/screencasts/create-project.json"></ascinema-player>
