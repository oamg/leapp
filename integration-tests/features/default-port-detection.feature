Feature: Get information about ports which will be forwarded from source

Scenario: Return detailed informations about ports 22,80
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | vm         | centos6-guest-httpd | no           |
     Then getting information about ports 22,80 which will be remapped to 9022,80
