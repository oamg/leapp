Feature: System status caching in DBus service

Scenario: Basic status caching for machine listing performance
   Given the LeApp DBus service is running
     And the local virtual machines:
         | name       | definition          | ensure_fresh |
         | vm1        | centos6-guest-httpd | no           |
         | vm2        | centos7-target      | no           |
   # These initial numbers are for response times *without* status caching
   Then the status cache should be populated within 0 seconds
    And a shallow machine listing should take less than 15 seconds
    And a full machine listing should take less than 30 seconds
