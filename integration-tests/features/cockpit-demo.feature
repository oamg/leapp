Feature: Demonstration Cockpit plugin

@wip
@skip
Scenario: Initial page visit
  Given Cockpit is installed on the testing host
    And the demonstration user exists
    And the demonstration plugin is installed
    And the local virtual machines:
         | name       | definition          | ensure_fresh |
         | vm1        | centos6-guest-httpd | no           |
         | vm2        | centos7-target      | no           |
  When the demonstration user visits the Le-App page
  Then the local VMs should be listed within 120 seconds
