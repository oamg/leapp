Feature: Redeploy stateless HTTP services

Scenario: HTTP default server page
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
    When app-source is migrated to target as a macrocontainer
    Then the HTTP 403 response on port 80 should match within 120 seconds
     And attempting another migration should fail within 10 seconds

Scenario: HTTP default server page - migrated by using rsync
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
    When app-source is migrated to target as a macrocontainer and rsync is used for fs migration
    Then the HTTP 403 response on port 80 should match within 120 seconds
     And attempting another migration should fail within 10 seconds

Scenario: Forced migration overwriting an existing container
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
     And the following names claimed on target:
         | name       | kind                |
         | migrated   | idle macrocontainer |
   Then migrating app-source to target as "migrated" should fail within 10 seconds
    And attempting another migration with forced creation should succeed within 120 seconds
    And the HTTP 403 response on port 80 should match within 120 seconds
