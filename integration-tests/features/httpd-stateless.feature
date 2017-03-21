Feature: Redeploy stateless HTTP services

Scenario: HTTP default server page
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | yes          |
    When app-source is redeployed to target as a macrocontainer
    Then the HTTP responses on port 80 should match
