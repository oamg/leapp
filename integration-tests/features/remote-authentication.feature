Feature: End-to-end testing of supported remote authentication models

Scenario: Remote access using the --identity option
    Given the default identity file is not registered with ssh-agent
      And the local virtual machines:
         | name               | definition          | ensure_fresh |
         | remote-system      | centos7-target      | no           |
    Then remote-system should be accessible using the default identity file

Scenario: Remote access using the --identity option @ centos6
    Given the default identity file is not registered with ssh-agent
      And the local virtual machines:
         | name               | definition          | ensure_fresh |
         | remote-system      | centos6-guest-httpd | no           |
    Then remote-system should be accessible using the default identity file

@skip
Scenario: Remote access using the --ask-pass option
   Given the tests are being run as root
     And the local virtual machines:
         | name           | definition          | ensure_fresh |
         | remote-system  | centos7-target      | no           |
    Then remote-system should be accessible using the default password

Scenario: Remote access using ssh-agent
   Given the local virtual machines:
         | name           | definition          | ensure_fresh |
         | remote-system  | centos7-target      | no           |
    Then remote-system should be accessible using ssh-agent
