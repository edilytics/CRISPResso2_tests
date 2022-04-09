import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

import locator
from selenium.webdriver.support import ui
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select


class BasePage(object):
    def __init__(self, driver):
        self.driver = driver

    def click_submit(self):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Base_Page_Locators.SUBMIT_BUTTON))
            element.click()
        except:
            return False
        return True


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


class CRISPRessoCorePage(BasePage):
    def enter_paired_end_values(self):
        try:
            self.driver.execute_script("populateNHEJ()")
        except:
            return False
        return True

    def enter_single_end_values(self):
        try:
            self.driver.execute_script("populateMultiAllele()")
        except:
            return False
        return True

    def enter_batch_values(self):
        try:
            self.driver.execute_script("populateBatch()")
        except:
            return False
        return True

    def validate_paired_end(self):
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
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.INDEL_CHARACTERIZATION_TAB))
            try:
                list_items = element.find_elements_by_tag_name("li")
                for item in list_items:
                    item.click()
            except:
                missing_elements.append("Missing Indel Characterization Tabs")
        except:
            missing_elements.append("Indel Characterization Container")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < 11:
            missing_elements.append("Images missing.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc+1:]
            if image not in locator.Paired_Ends_Results_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image.")
        if len(missing_elements) != 0:
            print("Missing elements for page validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_single_end(self):
        missing_elements = []
        try:
            element = WebDriverWait(self.driver, 50).until(
                EC.visibility_of_element_located(locator.Single_End_Results_Locators.STATISTICS_PARAMETERS_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Single_End_Results_Locators.ALIGNMENT_STATISTICS_TAB))
                element.click()
            except:
                missing_elements.append("Alignment Statistics Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Single_End_Results_Locators.RUN_PARAMETERS_TAB))
                element.click()
            except:
                missing_elements.append("Run Parameters Tab missing or non-functional")
        except:
            missing_elements.append("Alignment Statistics and Run Parameters Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Single_End_Results_Locators.PIECHART_BARPLOT_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Single_End_Results_Locators.PIECHART_TAB))
                element.click()
            except:
                missing_elements.append("Pie Chart Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Single_End_Results_Locators.BARPLOT_TAB))
                element.click()
            except:
                missing_elements.append("Bar Plot Tab missing or non-functional")
        except:
            missing_elements.append("Pie Chart and Bar Plot Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Single_End_Results_Locators.NUCLEOTIDE_ZOOM))
        except:
            missing_elements.append("Nucleotide Zoom Image Missing")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Results_Locators.INDEL_CHARACTERIZATION_TAB))
            try:
                list_items = element.find_elements_by_tag_name("li")
                for item in list_items:
                    item.click()
            except:
                missing_elements.append("Missing Indel Characterization Tabs")
        except:
            missing_elements.append("Indel Characterization Container")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < 11:
            missing_elements.append("Images missing.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Single_End_Results_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image.")
        if len(missing_elements) != 0:
            print("Missing elements for page validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_batch(self):
        missing_elements = []
        try:
            title = WebDriverWait(self.driver, 50).until(
                EC.visibility_of_element_located(locator.Batch_Results_Locators.TITLE))
        except:
            missing_elements.append("Title not loading")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Results_Locators.IMAGE_SOURCES):
            missing_elements.append("Images missing.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Results_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image.")

        tabs = []
        try:
            time.sleep(3)
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Batch_Results_Locators.FANCF_UNTR_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF_untr")
        except Exception as e:
            missing_elements.append("FANCF_untr link missing or unclickable")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Batch_Results_Locators.FANCF_BE1_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF_BE1")
        except:
            missing_elements.append("FANCF_BE1 link missing or unclickable")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Batch_Results_Locators.FANCF_BE2_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF_BE2")
        except:
            missing_elements.append("FANCF_BE2 link missing or unclickable")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Batch_Results_Locators.FANCF_BE3_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF_BE3")
        except:
            missing_elements.append("FANCF_BE3 link missing or unclickable")
        for tab in range(len(tabs)):
            self.driver.switch_to.window(self.driver.window_handles[tab+1])
            if tabs[tab] == "FANCF_untr":
                validate = self.validate_batch_FANCF_untr()
            elif tabs[tab] == "FANCF_BE1":
                validate = self.validate_batch_FANCF_BE1()
            elif tabs[tab] == "FANCF_BE2":
                validate = self.validate_batch_FANCF_BE2()
            elif tabs[tab] == "FANCF_BE3":
                validate = self.validate_batch_FANCF_BE3()
        if len(missing_elements) != 0:
            print("Missing elements for page validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_batch_FANCF_untr(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Results_Locators.IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF_untr.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Results_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF_untr.")

    def validate_batch_FANCF_BE1(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Results_Locators.BE1_IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF_BE1.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Results_Locators.BE1_IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF_BE1.")

    def validate_batch_FANCF_BE2(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Results_Locators.BE2_IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF_BE2.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Results_Locators.BE2_IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF_BE2.")

    def validate_batch_FANCF_BE3(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Results_Locators.BE3_IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF_BE3.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Results_Locators.BE3_IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF_BE3.")
