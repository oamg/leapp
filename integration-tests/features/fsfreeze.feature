Feature: Check FS freezing

@skip
Scenario: Verify whether fs was frozen
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | source     | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
     When source is migrated to target and fs is frozen
     Then source FS will be frozen

Scenario: Verify whether fs was not frozen
   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | source     | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |
     When source is migrated to target and fs is not frozen
     Then source FS will not be frozen
