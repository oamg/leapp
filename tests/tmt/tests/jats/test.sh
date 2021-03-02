#!/bin/sh -eux

TESTS_RESULT=test_results
JAT_LOG="/var/tmp/jat/last/log.yaml"
JAT_RELICS="/var/tmp/jat/last/relics/xcase-results.yaml"

suite=${TESTSUITE:-leapp}
testname=${TESTNAME:-cli}

echo "Preparing to run tests for $suite.."
for jats_test in $(find /usr/share/jats/suite/$suite/$testname -name test | sed -e 's/test$//'); do
    echo "Processing $jats_test.."
    # perform cleanup just in case previous test failed hard
    if [ -d /var/tmp/jat ]; then
        rm -r /var/tmp/jat
    fi
    test_dir_name=$(echo "$jats_test" | sed -e 's/\//_/g')
    mkdir "$test_dir_name"
    # save overall test result
    jattool runtest $jats_test
    # pack artifacts and test log
    echo "$jats_test\nResult: $?" >> "$TESTS_RESULT"
    cp "$JAT_LOG" "$test_dir_name/log.yaml"
    if [ -f "$JAT_RELICS" ]; then
        cp "$JAT_RELICS" "$test_dir_name/xcase-results.yaml"
    fi
    jattool export "$JAT_LOG"
    mv $(ls jat_report-*) "$test_dir_name/jat_report.html"
done;
