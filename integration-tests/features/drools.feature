Feature: Test HTTP response of Drools
Scenario: Drools default server page
    Given the local virtual machines:
         | name | definition | ensure_fresh |
         | drools | centos6-drools | no |
         | target | centos7-target | no |
    When drools is redeployed to target as a macrocontainer with ports 8080 forwarded
    Then the HTTP 200 response against /drools-wb/ on port 8080 should match within 300 seconds
