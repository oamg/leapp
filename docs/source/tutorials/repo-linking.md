# Linking repositories

Snactor allows you to link repositories, which is needed if you want to use actors, tags, 
models, etc. from another repository.

Firstly, leave the current repository and [create a new one](create-repository) called *tutorial-linked*
and enter its folder.

To link the *tutorial* repository, run the snactor tool:

```shell
    $ snactor repo link --path ../tutorial
```

You can also link the repository using name or UUID of the repository.
When using repository name, beware that the first matching name will be linked.
Therefore it's recommended to rather link repositories by path or repository id.

Now, you will be able to use actors, tags, models, and topics from tutorial repository. 
You can check this using `snactor discover` command:

```shell
    $ snactor discover --all
```

## A screen cast of the steps above

<asciinema-player src="_static/screencasts/repo-linking.cast"></ascinema-player>