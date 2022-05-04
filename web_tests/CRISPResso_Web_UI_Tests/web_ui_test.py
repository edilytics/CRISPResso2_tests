import os
import subprocess
import time

import web_ui_test_page
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

SELENIUM_LOG_FILE_PATH = '../UI_selenium_log.txt'
DOCKER_LOG_FILE_PATH = '../UI_docker_log.txt'

class Web_UI_Test_Main:
    def __init__(self):
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
            with open(DOCKER_LOG_FILE_PATH, 'w+') as docker_out:
                # Development command. Loads docker from the current local C2Web repo instead of the docker image.
                # results = subprocess.Popen('docker run --name web_automated_tests -e USE_DEFAULT_USER=False -e
                    # ALLOW_ADMIN_INIT=True -i -p 1234:80 -v [PATH_TO_REPO]/C2Web:/var/www/webapps/CRISPRessoWEB:rw --rm
                    # crispresso2web'.split(), stdout=docker_out, stderr=docker_out)
                results = subprocess.Popen('docker run --name web_automated_tests -e USE_DEFAULT_USER=False -e '
                                           'ALLOW_ADMIN_INIT=True -i -p 1234:80 --rm crispresso2web'.split(),
                                           stdout=docker_out, stderr=docker_out)
            time.sleep(10)
            print(results)
        except subprocess.CalledProcessError as e:
            print("Unable to start docker container.")
            print(e)

    def main(self):
        with open(SELENIUM_LOG_FILE_PATH, 'w+') as out:
            out.write("Starting Tests.\n")
        passed_tests = []
        failed_tests = []
        if not self.register_login_test():
            failed_tests.append("Register and Login Test Failed")
            return 1
        else:
            passed_tests.append("Register and Login Test Passed")
        print("Login/Register Test Finished")
        time.sleep(1)
        if not self.base_paired_end_test():
            failed_tests.append("Base Paired End Test Failed")
        else:
            passed_tests.append("Base Paired End Test Passed")
        print("Base Paired End Test Finished")
        time.sleep(1)
        if not self.base_single_end_test():
            failed_tests.append("Base Single End Test Failed")
        else:
            passed_tests.append("Base Single End Test Passed")
        print("Base Single End Test Finished")
        time.sleep(1)
        if not self.base_interleaved_test():
            failed_tests.append("Base Interleaved Test Failed")
        else:
            passed_tests.append("Base Interleaved Test Passed")
        print("Base Interleaved Test Finished")
        time.sleep(1)
        if not self.base_batch_test():
            failed_tests.append("Base Batch Test Failed")
        else:
            passed_tests.append("Base Batch Test Passed")
        print("Base Batch Test Finished")
        time.sleep(1)
        if not self.pooled_single_end_test():
            failed_tests.append("Pooled Single End Test Failed")
        else:
            passed_tests.append("Pooled Single End Test Passed")
        print("Pooled Single End Test Finished")
        time.sleep(1)
        if not self.wgs_single_cas9_test():
            failed_tests.append("WGS Cas9 Test Failed")
        else:
            passed_tests.append("WGS Cas9 Test Passed")
        print("WGS Cas9 Test Finished")
        time.sleep(1)
        self.driver.quit()
        with open(DOCKER_LOG_FILE_PATH, 'a+') as docker_out:
            subprocess.run('docker container stop web_automated_tests'.split(), stdout=docker_out, stderr=docker_out)
        passed = True
        print("\nSuccessful Tests:")
        if len(passed_tests) > 0:
            for passed in passed_tests:
                print(passed)
        print("\nFailed Tests:")
        if len(failed_tests) > 0:
            passed = False
            for failed in failed_tests:
                print(failed)
        else:
            print("None")
        with open(SELENIUM_LOG_FILE_PATH, 'a+') as out:
            out.write("Tests Finished.\n")
        if passed:
            return 0
        return 1

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
    Web_UI_Test_Main().main()
