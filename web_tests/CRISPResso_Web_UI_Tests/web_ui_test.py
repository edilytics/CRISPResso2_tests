import argparse
import os
import subprocess
import time

import web_ui_test_page
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm


class Web_UI_Test_Main:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-extensions')
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        try:
            running_container_id = subprocess.check_output(
                ['docker', 'ps', '-aq', '-f', 'name={0}'.format('web_automated_tests')],
            ).decode('utf-8').strip()
            if running_container_id:
                os.system('docker rm -f {0}'.format(running_container_id))
            print(os.path.realpath(__file__))
            # Development command. Loads docker from the current local C2Web repo instead of the docker image.
            # self.server_process = subprocess.Popen('docker run --name web_automated_tests -e "USE_DEFAULT_USER=False" -e "ALLOW_ADMIN_INIT=True" -i -p 1234:80 -v [PATH_TO_REPO]/C2Web:/var/www/webapps/CRISPRessoWEB:rw --rm crispresso2web')
            self.server_process = subprocess.Popen(
                'docker run --name web_automated_tests -e USE_DEFAULT_USER=False -e ALLOW_ADMIN_INIT=True -i -p 1234:80 --rm crispresso2web'.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            time.sleep(10)
        except subprocess.CalledProcessError as e:
            print("Unable to start docker container.")
            print(e)

    def main(self):
        print('Starting tests')
        passed_tests = []
        failed_tests = []

        tests = [
            ('Register Login', self.register_login_test),
            ('Base Paired End', self.base_paired_end_test),
            ('Base Single End', self.base_single_end_test),
            ('Base Interleaved', self.base_interleaved_test),
            ('Base Batch', self.base_batch_test),
            ('Pooled Single End', self.pooled_single_end_test),
            ('WGS Cas9', self.wgs_single_cas9_test),
        ]
        for test_name, test in tqdm(tests):
            if test():
                passed_tests += [test_name]
            else:
                failed_tests += [test_name]
            time.sleep(1)

        self.driver.quit()
        subprocess.run('docker container stop web_automated_tests'.split())

        if passed_tests:
            print('Passed tests:\n\t{0}\n'.format('\n\t'.join(passed_tests)))
        else:
            print('No tests passed')
        if failed_tests:
            print('Failed tests:\n\t{0}\n'.format('\n\t'.join(failed_tests)))
        else:
            print('No tests failed')
        if failed_tests:
            with open(self.log_file_path, 'w') as log_fh:
                log_fh.write(self.server_process.stdout.read().decode('utf-8'))
            return 1
        return 0

    def register_login_test(self):
        self.driver.get("http://localhost:1234/startup")
        mainPage = web_ui_test_page.RegisterLoginPage(self.driver)
        success = mainPage.enter_register_values()
        if not success:
            return False
        success = mainPage.click_submit()
        if not success:
            return False
        self.driver.get("http://localhost:1234/login")
        mainPage = web_ui_test_page.RegisterLoginPage(self.driver)
        success = mainPage.enter_login_values()
        if not success:
            return False
        success = mainPage.click_submit()
        if not success:
            return False
        return True

    def base_paired_end_test(self):
        self.driver.get("http://localhost:1234/submission")
        mainPage = web_ui_test_page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_paired_end_values()
        if not success:
            return False
        success = mainPage.click_submit()
        if not success:
            return False
        validate = mainPage.validate_paired_end()
        if not validate:
            return False
        return True

    def base_single_end_test(self):
        self.driver.get("http://localhost:1234/submission")
        mainPage = web_ui_test_page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_single_end_values()
        if not success:
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            return False
        time.sleep(5)
        validate = mainPage.validate_single_end()
        if not validate:
            return False
        return True

    def base_interleaved_test(self):
        self.driver.get("http://localhost:1234/submission")
        mainPage = web_ui_test_page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_interleaved_values()
        time.sleep(1)
        if not success:
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            return False
        time.sleep(5)
        validate = mainPage.validate_interleaved()
        if not validate:
            return False
        return True

    def base_batch_test(self):
        self.driver.get("http://localhost:1234/submission")
        mainPage = web_ui_test_page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_batch_values()
        time.sleep(1)
        if not success:
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            return False
        time.sleep(5)
        validate = mainPage.validate_batch()
        if not validate:
            return False
        return True

    def pooled_single_end_test(self):
        self.driver.get("http://localhost:1234/submission_pooled")
        mainPage = web_ui_test_page.CRISPRessoPooledPage(self.driver)
        success = mainPage.enter_single_end_values()
        time.sleep(1)
        if not success:
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            return False
        time.sleep(2)
        validate = mainPage.validate_single_end()
        if not validate:
            return False
        return True

    def wgs_single_cas9_test(self):
        self.driver.get("http://localhost:1234/submission_wgs")
        mainPage = web_ui_test_page.CRISPRessoWGSPage(self.driver)
        success = mainPage.enter_cas9_values()
        time.sleep(1)
        if not success:
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            return False
        time.sleep(1)
        validate = mainPage.validate_cas9()
        if not validate:
            return False
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser('CRIPSRessoWeb Interface Unit Tests')
    parser.add_argument('--log_file_path', default='UI_test_summary_log.txt')

    args = parser.parse_args()
    Web_UI_Test_Main(args.log_file_path).main()
