Feature: Demonstration Cockpit plugin

@root_recommended
Scenario: Initial page visit & app redeployment
  Given Cockpit is installed on the testing host
    And the demonstration user exists
    And the demonstration plugin is installed
    And the local virtual machines as root:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
  When the demonstration user visits the Import Apps page
  Then the local VMs should be listed within 120 seconds

  # The above scenario is both slow to run *and* required as setup for the next
  # scenario so we just continue here instead of defining a separate scenario
  When the demonstration user redeploys app-source to target
  Then the redeployment should be reported as complete within 120 seconds
