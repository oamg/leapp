Feature: Get information about used ports by virtual machine

Scenario: Return detailed informations about ports 22,80
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | vm         | centos6-guest-httpd | no           |
     Then getting information about ports 22,80 used by 10.0.0.10 should take less than 15 seconds

Scenario: Return information about all used ports by virtual machine
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | vm         | centos6-guest-httpd | no           |
     Then getting informations about all used ports by 10.0.0.10 should take less than 3 seconds
