import os
import sys
import yaml
import re

ARTIFACT_DIR = os.environ.get('ARTIFACT_DIR')
EC = 0

TEST_HINTS = {
    'initial_reboot':
        '''
        Initial reboot timed out,
        please re-run the test.
        ''',
    'leapp_install':
        '''
        We were unable to install leapp and/or leapp-repository
        packages. Please refer to leapp_install/output.txt to see output
        of yum install command.
        ''',
    'upgrade':
        '''
        Leapp upgrade has failed. For more information check upgrade/output.txt
        or any other enclosed leapp file.
        ''',
    'reboot_to_upgrade_initramdisk':
        '''
        Timeout when rebooting to initramfs. Check full console log for more
        information or re-run the test.
        ''',
    'kernel':
        '''
        We expect the kernel version to be a RHEL 8 one after upgrade.
        Check the kernel/output.txt file to see kernel version.
        ''',
    'release':
        '''
        We expect the OS-release to be RHEL 8 after upgrade.
        Check the release/output.txt file to see os-release.
        ''',
    'rpm':
        '''
        We expect all the binary rpms from the tested build to be installed after upgrade.
        Please refer to rpm/list.txt file to find out what packages were not installed.

        We highly advise to check PES data as well.
        You can find PES at pes.leapp.lab.eng.brq.redhat.com
        PES manual with tutorials can be found at source.redhat.com/groups/public/oamg/docs/package_evolution_service_manual
        '''
}

#
# How the results should look like:
#
# results:
#
# - test: best_test
#   result: fail
#   logs:
#   - best_test.log
#
#


class TestReport:
    def __init__(self):
        self.results = []

    def add_result(self, test_name, test_result, test_logs):
        self.results.append({
            'test': test_name,
            'result': test_result,
            'logs': test_logs
            })

    def print_results(self):
        failed = False
        for entry in self.results:
            line = f'{entry["test"]} - {entry["result"]}'
            if entry["result"] != 'pass':
                failed = True
            print(line)
        res = 'pass' if not failed else 'fail'
        print(f'Overall result: {res}')

    def make_results(self):
        with open('{}/results.yml'.format(ARTIFACT_DIR), 'w') as file:
            file.write("results:\n\n")
            yaml.dump(self.results, file, default_flow_style=False)


def make_hint(test_name):
    with open('{0}/{1}/README.txt'.format(ARTIFACT_DIR, test_name), 'w') as f:
        f.write(TEST_HINTS[test_name])


def get_result(log_file, pattern):
    with open(log_file, 'r') as f:
        result = re.search(pattern, f.read())
        return result


def gather_results(test_report):
    ec = EC
    #
    # initial reboot check
    #
    test_name = 'initial_reboot'
    if get_result('{0}/{1}/output.txt'.format(ARTIFACT_DIR, test_name), '"changed": true'):
        test_report.add_result(test_name, 'pass', ['{0}/output.txt'.format(test_name)])
    elif get_result('{0}/{1}/output_2.txt'.format(ARTIFACT_DIR, test_name), '"failed": false'):
        test_report.add_result(test_name, 'pass', ['{0}/output_2.txt'.format(test_name)])
    else:
        # machine timed out and we cannot re-establish connection
        make_hint(test_name)
        test_report.add_result(test_name, 'fail', ['{0}/output.txt'.format(test_name), '{}/README.txt'.format(test_name)])
        ec = 1
        raise Exception()

    #
    # leapp_install check
    #
    test_name = 'leapp_install'
    if get_result('{0}/{1}/exit_code.txt'.format(ARTIFACT_DIR, test_name), '0'):
        test_report.add_result(test_name, 'pass', ['{0}/output.txt'.format(test_name)])
    else:
        make_hint(test_name)
        test_report.add_result(test_name, 'fail', ['{0}/output.txt'.format(test_name), '{}/README.txt'.format(test_name)])
        ec = 1
        raise Exception()

    #
    # upgrade check
    #
    test_name = 'upgrade'
    if get_result('{0}/{1}/exit_code.txt'.format(ARTIFACT_DIR, test_name), '0'):
        test_report.add_result(test_name, 'pass', ['{0}/output.txt'.format(test_name)])
    else:
        make_hint(test_name)
        test_report.add_result(test_name, 'fail', ['{0}/output.txt'.format(test_name), '{}/README.txt'.format(test_name)])
        ec = 1
        raise Exception()

    #
    # reboot_to_upgrade_initramdisk check (timeout)
    #
    test_name = 'reboot_to_upgrade_initramdisk'
    if get_result('{0}/{1}/output.txt'.format(ARTIFACT_DIR, test_name), '"changed": true'):
        test_report.add_result(test_name, 'pass', ['{0}/output.txt'.format(test_name)])
    elif get_result('{0}/{1}/output_2.txt'.format(ARTIFACT_DIR, test_name), '"failed": false'):
        test_report.add_result(test_name, 'pass', ['{0}/output_2.txt'.format(test_name)])
    elif get_result('{0}/{1}/output_3.txt'.format(ARTIFACT_DIR, test_name), '"failed": false'):
        test_report.add_result(test_name, 'pass', ['{0}/output_3.txt'.format(test_name)])
    else:
        # machine timed out and we cannot re-establish connection
        make_hint(test_name)
        test_report.add_result(test_name, 'fail', ['{0}/output.txt'.format(test_name), '{}/README.txt'.format(test_name)])
        ec = 1
        raise Exception()

    #
    # 'kernel version' test
    #
    test_name = 'kernel'
    if get_result('{0}/{1}/output.txt'.format(ARTIFACT_DIR, test_name), 'el8'):
        test_report.add_result(test_name, 'pass', ['{0}/output.txt'.format(test_name)])
    else:
        make_hint(test_name)
        test_report.add_result(test_name, 'fail', ['{0}/output.txt'.format(test_name), '{}/README.txt'.format(test_name)])
        ec = 1

    #
    # 'OS release' test
    #
    test_name = 'release'
    if get_result('{0}/{1}/output.txt'.format(ARTIFACT_DIR, test_name), 'Ootpa'):
        test_report.add_result(test_name, 'pass', ['{0}/output.txt'.format(test_name)])
    else:
        make_hint(test_name)
        test_report.add_result(test_name, 'fail', ['{0}/output.txt'.format(test_name), '{}/README.txt'.format(test_name)])
        ec = 1

    #
    # 'rpm -q' test
    #
    test_name = 'rpm'
    if get_result('{0}/{1}/list.txt'.format(ARTIFACT_DIR, test_name), 'is not installed'):
        make_hint(test_name)
        test_report.add_result(test_name, 'fail', ['{0}/list.txt'.format(test_name), '{}/README.txt'.format(test_name)])
        ec = 1
    else:
        test_report.add_result(test_name, 'pass', ['{0}/list.txt'.format(test_name)])

    return ec


if __name__ == "__main__":
    ec = EC
    test_report = TestReport()
    try:
        ec = gather_results(test_report)
    except IOError as err:
        # problem when opening file
        test_report.add_result('Open log files', 'error', [])
        ec = 2

    finally:
        test_report.make_results()
        test_report.print_results()
        sys.exit(ec)
