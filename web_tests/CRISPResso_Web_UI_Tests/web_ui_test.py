import os
import subprocess
import time

import web_ui_test_page
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


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
            # Development command. Loads docker from the current local C2Web repo instead of the docker image.
            # results = subprocess.Popen('docker run --name web_automated_tests -e "USE_DEFAULT_USER=False" -e "ALLOW_ADMIN_INIT=True" -i -p 1234:80 -v [PATH_TO_REPO]/C2Web:/var/www/webapps/CRISPRessoWEB:rw --rm crispresso2web')
            results = subprocess.Popen('docker run --name web_automated_tests -e USE_DEFAULT_USER=False -e ALLOW_ADMIN_INIT=True -i -p 1234:80 --rm crispresso2web'.split())
            time.sleep(10)
            print(results)
        except subprocess.CalledProcessError as e:
            print("Unable to start docker container.")
            print(e)

    def main(self):
        passed_tests = []
        failed_tests = []
        if not self.register_login_test():
            failed_tests.append("Register and Login Test Failed")
            return 1
        else:
            passed_tests.append("Register and Login Test Passed")
        time.sleep(1)
        if not self.base_paired_end_test():
            failed_tests.append("Base Paired End Test Failed")
        else:
            passed_tests.append("Base Paired End Test Passed")
        time.sleep(1)
        if not self.base_single_end_test():
            failed_tests.append("Base Single End Test Failed")
        else:
            passed_tests.append("Base Single End Test Passed")
        time.sleep(1)
        if not self.base_interleaved_test():
            failed_tests.append("Base Interleaved Test Failed")
        else:
            passed_tests.append("Base Interleaved Test Passed")
        time.sleep(1)
        if not self.base_batch_test():
            failed_tests.append("Base Batch Test Failed")
        else:
            passed_tests.append("Base Batch Test Passed")
        time.sleep(1)
        if not self.pooled_single_end_test():
            failed_tests.append("Pooled Single End Test Failed")
        else:
            passed_tests.append("Pooled Single End Test Passed")
        time.sleep(1)
        if not self.wgs_single_cas9_test():
            failed_tests.append("WGS Cas9 Test Failed")
        else:
            passed_tests.append("WGS Cas9 Test Passed")
        time.sleep(1)
        self.driver.quit()
        subprocess.run('docker container stop web_automated_tests'.split())
        print("\nSuccessful Tests:")
        if len(passed_tests) > 0:
            for passed in passed_tests:
                print(passed)
        print("\nFailed Tests:")
        if len(failed_tests) > 0:
            for failed in failed_tests:
                print(failed)
            return 1
        else:
            print("None")
        return 0

    def register_login_test(self):
        self.driver.get("http://localhost:1234/startup")
        mainPage = web_ui_test_page.RegisterLoginPage(self.driver)
        success = mainPage.enter_register_values()
        if not success:
            print("Unable to enter values to register.")
            return False
        success = mainPage.click_submit()
        if not success:
            print("Unable to click register.")
            return False
        self.driver.get("http://localhost:1234/login")
        mainPage = web_ui_test_page.RegisterLoginPage(self.driver)
        success = mainPage.enter_login_values()
        if not success:
            print("Unable to enter values to login.")
            return False
        success = mainPage.click_submit()
        if not success:
            print("Unable to click login.")
            return False
        return True

    def base_paired_end_test(self):
        self.driver.get("http://localhost:1234/submission")
        mainPage = web_ui_test_page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_paired_end_values()
        if not success:
            print("Unable to enter paired end values.")
            return False
        success = mainPage.click_submit()
        if not success:
            print("Unable to click submit.")
            return False
        validate = mainPage.validate_paired_end()
        if not validate:
            print("Unable to validate results from paired end test.")
            return False
        return True

    def base_single_end_test(self):
        self.driver.get("http://localhost:1234/submission")
        mainPage = web_ui_test_page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_single_end_values()
        if not success:
            print("Unable to enter paired end values.")
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            print("Unable to click submit.")
            return False
        time.sleep(5)
        validate = mainPage.validate_single_end()
        if not validate:
            print("Unable to validate results from single end test.")
            return False
        return True

    def base_interleaved_test(self):
        self.driver.get("http://localhost:1234/submission")
        mainPage = web_ui_test_page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_interleaved_values()
        time.sleep(1)
        if not success:
            print("Unable to enter interleaved values.")
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            print("Unable to click submit.")
            return False
        time.sleep(5)
        validate = mainPage.validate_interleaved()
        if not validate:
            print("Unable to validate results from interleaved test.")
            return False
        return True

    def base_batch_test(self):
        self.driver.get("http://localhost:1234/submission")
        mainPage = web_ui_test_page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_batch_values()
        time.sleep(1)
        if not success:
            print("Unable to enter batch values.")
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            print("Unable to click submit.")
            return False
        time.sleep(5)
        validate = mainPage.validate_batch()
        if not validate:
            print("Unable to validate results from batch test.")
            return False
        return True

    def pooled_single_end_test(self):
        self.driver.get("http://localhost:1234/submission_pooled")
        mainPage = web_ui_test_page.CRISPRessoPooledPage(self.driver)
        success = mainPage.enter_single_end_values()
        time.sleep(1)
        if not success:
            print("Unable to enter file values.")
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            print("Unable to click submit.")
            return False
        time.sleep(2)
        validate = mainPage.validate_single_end()
        if not validate:
            print("Unable to validate results from pooled single end test.")
            return False
        return True

    def wgs_single_cas9_test(self):
        self.driver.get("http://localhost:1234/submission_wgs")
        mainPage = web_ui_test_page.CRISPRessoWGSPage(self.driver)
        success = mainPage.enter_cas9_values()
        time.sleep(1)
        if not success:
            print("Unable to enter file values.")
            return False
        time.sleep(1)
        success = mainPage.click_submit()
        if not success:
            print("Unable to click submit.")
            return False
        time.sleep(1)
        validate = mainPage.validate_cas9()
        if not validate:
            print("Unable to validate results from WGS Cas9 test.")
            return False
        return True


if __name__ == "__main__":
    Web_UI_Test_Main().main()
