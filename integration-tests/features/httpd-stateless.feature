Feature: Redeploy stateless HTTP services

Scenario: Migrate between remote hosts using rsync
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
    When app-source is migrated to target as a macrocontainer and rsync is used for fs migration
    Then the HTTP 403 response on port 80 should match within 120 seconds
     And attempting another migration should fail within 10 seconds

Scenario: Migrate between remote hosts using rsync - systemd
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos7-guest-httpd | no           |
         | target     | centos7-target      | no           |
    ## WORKAROUND FOR: https://bugzilla.redhat.com/show_bug.cgi?id=1474726
    When app-source is migrated to target as a macrocontainer and rsync is used for fs migration
    #When app-source is migrated to target as a macrocontainer
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

Scenario: Importing an application to the current host using rsync & forced creation
   Given Docker is installed on the testing host
     And the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
    When app-source is imported as a macrocontainer
    Then the HTTP 403 response on port 80 should match within 120 seconds
     And attempting another migration should fail within 10 seconds

Scenario: Restart docker and check that the container is running
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | target     | centos7-target      | no           |
         | app-source | centos6-guest-httpd | no           |
   When app-source is migrated to target as a macrocontainer named container-app
   And  docker is restarted
   Then container named container-app should be restarted and running

