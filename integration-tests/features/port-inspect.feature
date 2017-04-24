Feature: Get information about used ports by virtual machine

@wip
Scenario: Return information about used ports by virtual machine
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | vm         | centos6-guest-httpd | no           |
     Then getting information about used ports by 10.0.0.10 from range 1-10000 should take less than 60 seconds
