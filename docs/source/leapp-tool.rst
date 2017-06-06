LeApp tool
==========


list-machines
^^^^^^^^^^^^^

    **usage:** 
        leapp-tool list-machines [-h] [--shallow] [pattern [pattern ...]]
    
    positional arguments:
        +-------------+--------------------------------+
        | pattern     | list machines matching pattern |
        +-------------+--------------------------------+
    
    optional arguments:
        -h, --help    Show this help message and exit
        --shallow     Skip detailed scans of VM contents


migrate-machine
^^^^^^^^^^^^^^^

    **usage:** 
        leapp-tool migrate-machine [-h] [-t TARGET]
                                   [--tcp-port [FORWARDED_PORTS [FORWARDED_PORTS ...]]]
                                   [--source-identity IDENTITY] [--source-ask-pass]
                                   [--source-user USER]
                                   [--target-identity IDENTITY] [--target-ask-pass]
                                   [--target-user USER]
                                   machine
    
    positional arguments:
        +-------------+---------------------------+
        | machine     | source machine to migrate |
        +-------------+---------------------------+
    
    optional arguments:
        ==================================================  =======================================================
        -h, --help                                          Show this help message and exit
        -t TARGET, --target TARGET                          target VM name
        --tcp-port [FORWARDED_PORTS [FORWARDED_PORTS ...]]  Target ports to forward to macrocontainer (temporary!)
        --source-identity IDENTITY                          Path to private SSH key for the source machine
        --source-ask-pass                                   Ask for SSH password for the source machine
        --source-user USER                                  Connect as this user to the source machine
        --target-identity IDENTITY                          Path to private SSH key for the target machine
        --target-ask-pass                                   Ask for SSH password for the target machine
        --target-user USER                                  Connect as this user to the target machine
        ==================================================  =======================================================



destroy-containers
^^^^^^^^^^^^^^^^^^
    **usage:**
        leapp-tool destroy-containers [-h] [--identity IDENTITY] [--ask-pass]
                                      [--user USER]
                                      target
    
    positional arguments:
        +-------------+---------------------------+
        | target      | target VM name            |
        +-------------+---------------------------+

    
    optional arguments:
        ========================  =============================== 
        -h, --help                Show this help message and exit
        --identity IDENTITY       Path to private SSH key
        --ask-pass, -k            Ask for SSH password
        --user USER, -u USER      Connect as this user
        ========================  =============================== 


port-inspect
^^^^^^^^^^^^
    **usage:** 
        leapp-tool port-inspect [-h] [--range RANGE] [--shallow] ip
    
    positional arguments:
        +-------------+----------------------------+
        | ip          | virtual machine ip address |
        +-------------+----------------------------+
    
    optional arguments:
        -h, --help      Show this help message and exit
        --range RANGE   port range, example of proper
                        form:"-100,200-1024,T:3000-4000,U:60000-"
        --shallow       Skip detailed informations about used ports, this is quick
                        SYN scan

