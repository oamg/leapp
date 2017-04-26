Feature: Redeploy stateless HTTP services

Scenario: HTTP default server page
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
    When app-source is redeployed to target as a macrocontainer
    Then the HTTP 403 response on port 80 should match within 90 seconds

Scenario: Drools default server page
    Given the local virtual machines:
         | name | definition | ensure_fresh |
         | drools | centos6-drools | no |
         | target | centos7-target | no |
    When drools is redeployed to target as a macrocontainer
    Then the HTTP 200 response against drools-wb/ on port 8080 should match within 90 seconds
