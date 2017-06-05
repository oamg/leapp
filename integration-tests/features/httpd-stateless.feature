Feature: Redeploy stateless HTTP services

Scenario: HTTP default server page
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
    When app-source is redeployed to target as a macrocontainer
    Then the HTTP 403 response on port 80 should match within 90 seconds

Scenario: HTTP default server page - migrated by using rsync
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
    When app-source is redeployed to target as a macrocontainer and rsync is used for fs migration
    Then the HTTP 403 response on port 80 should match within 90 seconds
