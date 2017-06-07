Feature: Checking usability of target virtual machine 

Scenario: Checking for already used names on target VM
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | target     | centos7-target      | no           |
     And the following names claimed on target:
         | name       | kind                |
         | app1       | idle macrocontainer |
         | app2       | idle macrocontainer |
         | container1 | idle container      |
         | container2 | idle container      |
         | storage1   | macrocontainer dir  |
         | storage2   | macrocontainer dir  |
    Then checking target usability should take less than 10 seconds
     And all claimed names should be reported exactly once
