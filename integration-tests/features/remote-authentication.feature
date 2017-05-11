Feature: End-to-end testing of supported remote authentication models

Scenario: Remote access using the --identity option
   Given the local virtual machines:
         | name           | definition          | ensure_fresh |
         | remote-system  | centos7-target      | no           |
    Then remote-system should be accessible using the default identity file

Scenario: Remote access using ssh-agent
   Given the default identity file is registered with ssh-agent
     And the local virtual machines:
         | name           | definition          | ensure_fresh |
         | remote-system  | centos7-target      | no           |
    Then remote-system should be accessible using ssh-agent
