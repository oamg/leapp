Feature: Destroy existing macrocontainers on target virtual machine

Scenario: Destroying macrocontainers on target VM
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
    Then destroying app1 on target should take less than 10 seconds
     And "app1" should no longer be reported as in use
     And all remaining claimed names should still be reported as in use
    Then destroying container1 on target should take less than 10 seconds
     And "container1" should no longer be reported as in use
     And all remaining claimed names should still be reported as in use
    Then destroying storage1 on target should take less than 10 seconds
     And "storage1" should no longer be reported as in use
     And all remaining claimed names should still be reported as in use
    Then destroying nonexistent on target should take less than 10 seconds
     And all remaining claimed names should still be reported as in use
