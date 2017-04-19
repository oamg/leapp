Feature: Destroy existing macrocontainers on target virtual machine 

Scenario: Destroying macrocontainers on target VM
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
    When app-source is redeployed to target as a macrocontainer
    Then destroying existing macrocontainers on target should take less than 60 seconds
