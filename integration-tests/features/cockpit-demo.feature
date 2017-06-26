Feature: Demonstration Cockpit plugin

Scenario: Application import to current host
  Given Cockpit is installed on the testing host
    And Docker is installed on the testing host
    And the demonstration user exists
    And the demonstration plugin is installed
    And the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
  When the demonstration user visits the Import Apps page
   And enters app-source's IP address as the import source
   And clicks the "Import" button
  Then the app import should be reported as complete within 120 seconds
