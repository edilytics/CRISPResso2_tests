import os
import subprocess
import page
import requests
import time
from selenium import webdriver


class Main:
    def __init__(self):
        path = os.path.realpath(__file__)
        path = os.path.split(path)[0]
        path = os.path.split(path)[0]
        path = os.path.join(path, "chromedriver")
        self.driver = webdriver.Chrome(str(path))
        try:
            results = subprocess.Popen('docker run --name web_automated_tests -e "USE_DEFAULT_USER=False" -e "ALLOW_ADMIN_INIT=True" -i -p 1234:80 --rm crispresso2web')
            print(results)
        except subprocess.CalledProcessError as e:
            print("Unable to start docker container.")
            print(e)

    def main(self):
        if not self.register_login_test():
            return 1
        if not self.base_paired_end_test():
            return 1
        self.driver.quit()
        subprocess.run('docker container stop web_automated_tests')
        return 0

    def register_login_test(self):
        timer = 0
        request = requests.get("http://localhost:1234/startup")
        while request.status_code != 200:
            time.sleep(.5)
            timer += .5
            request = requests.get("http://localhost:1234/startup")
            if timer == 15:
                print("Page unavailable for too long. Check docker and rerun test.")
                return False
        self.driver.get("http://localhost:1234/startup")
        mainPage = page.RegisterLoginPage(self.driver)
        success = mainPage.enter_register_values()
        if not success:
            print("Unable to enter values to register.")
            return False
        success = mainPage.click_submit()
        if not success:
            print("Unable to click register.")
            return False
        self.driver.get("http://localhost:1234/login")
        mainPage = page.RegisterLoginPage(self.driver)
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
        mainPage = page.CRISPRessoCorePage(self.driver)
        success = mainPage.enter_paired_end_values()
        if not success:
            print("Unable to enter paired end values.")
            return False
        success = mainPage.click_submit()
        if not success:
            print("Unable to click submit.")
            return False
        validate = mainPage.validate()
        if not validate:
            print("Unable to validate results from paired end test.")
            return False
        return True


if __name__ == "__main__":
    Main().main()
