import time
from selenium.common.exceptions import NoSuchElementException
import locator
from selenium.webdriver.support import ui
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select


class BasePage(object):
    def __init__(self, driver):
        self.driver = driver


class RegisterLoginPage(BasePage):
    def enter_register_values(self):
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.NAME_FIELD))
            name.send_keys(locator.Register_Login_Locators.NAME_VALUE)
        except:
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.USERNAME_FIELD))
            name.send_keys(locator.Register_Login_Locators.USERNAME_VALUE)
        except:
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.EMAIL_FIELD))
            name.send_keys(locator.Register_Login_Locators.EMAIL_VALUE)
        except:
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.PASSWORD_FIELD))
            name.send_keys(locator.Register_Login_Locators.PASSWORD_VALUE)
        except:
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.CONFIRM_PASSWORD_FIELD))
            name.send_keys(locator.Register_Login_Locators.PASSWORD_VALUE)
        except:
            return False
        return True

    def enter_login_values(self):
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.USERNAME_FIELD))
            name.send_keys(locator.Register_Login_Locators.USERNAME_VALUE)
        except:
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.PASSWORD_FIELD))
            name.send_keys(locator.Register_Login_Locators.PASSWORD_VALUE)
        except:
            return False
        return True

    def click_submit(self):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Base_Page_Locators.SUBMIT_BUTTON))
            element.click()
        except:
            return False
        return True


class CRISPRessoCorePage(BasePage):
    def enter_paired_end_values(self):
        try:
            self.driver.execute_script("populateNHEJ()")
        except:
            return False
        return True

    def click_submit(self):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Base_Page_Locators.SUBMIT_BUTTON))
            element.click()
        except:
            return False
        return True

    def validate(self):
        missing_elements = []
        try:
            element = WebDriverWait(self.driver, 50).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.STATISTICS_PARAMETERS_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.ALIGNMENT_STATISTICS_TAB))
                element.click()
            except:
                missing_elements.append("Alignment Statistics Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.RUN_PARAMETERS_TAB))
                element.click()
            except:
                missing_elements.append("Run Parameters Tab missing or non-functional")
        except:
            missing_elements.append("Alignment Statistics and Run Parameters Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.PIECHART_BARPLOT_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.PIECHART_TAB))
                element.click()
            except:
                missing_elements.append("Pie Chart Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.BARPLOT_TAB))
                element.click()
            except:
                missing_elements.append("Bar Plot Tab missing or non-functional")
        except:
            missing_elements.append("Pie Chart and Bar Plot Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.NUCLEOTIDE_ZOOM))
        except:
            missing_elements.append("Nucleotide Zoom Image Missing")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < 11:
            missing_elements.append("Images missing.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc+1:]
            if image not in locator.Paired_Ends_Results_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image.get_attribute('src')} is the incorrect image.")
        if len(missing_elements) != 0:
            print("Missing elements for page validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True
