Feature: Get information about ports used by a remote machine

Scenario: Return detailed informations about ports 22,80
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | vm         | centos6-guest-httpd | no           |
     Then getting information about ports 22,80 used by vm should take less than 20 seconds

Scenario: Return information about all ports used by virtual machine
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | vm         | centos6-guest-httpd | no           |
     Then getting informations about all ports used by vm should take less than 10 seconds
