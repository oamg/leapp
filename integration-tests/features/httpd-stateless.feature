Feature: Redeploy stateless HTTP services

Scenario: HTTP default server page
   Given the local virtual machines:
         | name       | image               | playbook |
         | app-source | centos6-guest-httpd |          |
         | target     | centos7-target      |          |
    When app-source is redeployed to target as a macrocontainer
    Then the HTTP responses on port 80 should match
