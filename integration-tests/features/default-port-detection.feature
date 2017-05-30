Feature: Get information about ports which will be forwarded from source

Scenario: Return default port detected on source machine
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | source     | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
     Then getting list of forwarded ports from source to target

