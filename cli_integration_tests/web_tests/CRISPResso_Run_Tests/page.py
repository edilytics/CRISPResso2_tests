import time
import locator
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage(object):
    def __init__(self, driver):
        self.driver = driver

    def click_submit(self):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Base_Page_Locators.SUBMIT_BUTTON))
            element.click()
        except Exception as e:
            print(e)
            return False
        return True


class RegisterLoginPage(BasePage):
    def enter_register_values(self):
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.NAME_FIELD))
            name.send_keys(locator.Register_Login_Locators.NAME_VALUE)
        except Exception as e:
            print(e)
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.USERNAME_FIELD))
            name.send_keys(locator.Register_Login_Locators.USERNAME_VALUE)
        except Exception as e:
            print(e)
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.EMAIL_FIELD))
            name.send_keys(locator.Register_Login_Locators.EMAIL_VALUE)
        except Exception as e:
            print(e)
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.PASSWORD_FIELD))
            name.send_keys(locator.Register_Login_Locators.PASSWORD_VALUE)
        except Exception as e:
            print(e)
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.CONFIRM_PASSWORD_FIELD))
            name.send_keys(locator.Register_Login_Locators.PASSWORD_VALUE)
        except Exception as e:
            print(e)
            return False
        return True

    def enter_login_values(self):
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.USERNAME_FIELD))
            name.send_keys(locator.Register_Login_Locators.USERNAME_VALUE)
        except Exception as e:
            print(e)
            return False
        try:
            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Register_Login_Locators.PASSWORD_FIELD))
            name.send_keys(locator.Register_Login_Locators.PASSWORD_VALUE)
        except Exception as e:
            print(e)
            return False
        return True


class CRISPRessoCorePage(BasePage):
    def enter_paired_end_values(self):
        try:
            self.driver.execute_script("populateNHEJ()")
        except Exception as e:
            print(e)
            return False
        return True

    def enter_single_end_values(self):
        try:
            self.driver.execute_script("populateMultiAllele()")
        except Exception as e:
            print(e)
            return False
        return True

    def enter_interleaved_values(self):
        try:
            self.driver.execute_script("populateInterleaved()")
        except Exception as e:
            print(e)
            return False
        return True

    def enter_batch_values(self):
        try:
            self.driver.execute_script("populateBatch()")
        except Exception as e:
            print(e)
            return False
        return True

    def validate_paired_end(self):
        missing_elements = []
        try:
            element = WebDriverWait(self.driver, 100).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Locators.STATISTICS_PARAMETERS_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Paired_Ends_Locators.ALIGNMENT_STATISTICS_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Alignment Statistics Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Paired_Ends_Locators.RUN_PARAMETERS_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Run Parameters Tab missing or non-functional")
        except Exception as e:
            print(e)
            missing_elements.append("Alignment Statistics and Run Parameters Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Locators.PIECHART_BARPLOT_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Paired_Ends_Locators.PIECHART_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Pie Chart Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Paired_Ends_Locators.BARPLOT_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Bar Plot Tab missing or non-functional")
        except Exception as e:
            print(e)
            missing_elements.append("Pie Chart and Bar Plot Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Locators.NUCLEOTIDE_ZOOM))
        except Exception as e:
            print(e)
            missing_elements.append("Nucleotide Zoom Image Missing")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Locators.INDEL_CHARACTERIZATION_TAB))
            try:
                list_items = element.find_elements_by_tag_name("li")
                for item in list_items:
                    item.click()
            except Exception as e:
                print(e)
                missing_elements.append("Missing Indel Characterization Tabs")
        except Exception as e:
            print(e)
            missing_elements.append("Indel Characterization Container")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < 11:
            missing_elements.append("Images missing.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Paired_Ends_Locators.IMAGE_SOURCES:
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
            element = WebDriverWait(self.driver, 100).until(
                EC.visibility_of_element_located(locator.Single_End_Locators.STATISTICS_PARAMETERS_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Single_End_Locators.ALIGNMENT_STATISTICS_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Alignment Statistics Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Single_End_Locators.RUN_PARAMETERS_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Run Parameters Tab missing or non-functional")
        except Exception as e:
            print(e)
            missing_elements.append("Alignment Statistics and Run Parameters Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Single_End_Locators.PIECHART_BARPLOT_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Single_End_Locators.PIECHART_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Pie Chart Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Single_End_Locators.BARPLOT_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Bar Plot Tab missing or non-functional")
        except Exception as e:
            print(e)
            missing_elements.append("Pie Chart and Bar Plot Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Single_End_Locators.NUCLEOTIDE_ZOOM))
        except Exception as e:
            print(e)
            missing_elements.append("Nucleotide Zoom Image Missing")
        try:
            element = WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(locator.Paired_Ends_Locators.INDEL_CHARACTERIZATION_TAB))
            try:
                list_items = element.find_elements_by_tag_name("li")
                for item in list_items:
                    item.click()
            except Exception as e:
                print(e)
                missing_elements.append("Missing Indel Characterization Tabs")
        except Exception as e:
            print(e)
            missing_elements.append("Indel Characterization Container")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < 12:
            missing_elements.append("Images missing.")
            print(len(images))
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Single_End_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image.")
        if len(missing_elements) != 0:
            print("Missing elements for page validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_interleaved(self):
        missing_elements = []
        try:
            element = WebDriverWait(self.driver, 100).until(
                EC.visibility_of_element_located(locator.Interleaved_Locators.STATISTICS_PARAMETERS_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Interleaved_Locators.ALIGNMENT_STATISTICS_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Alignment Statistics Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Interleaved_Locators.RUN_PARAMETERS_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Run Parameters Tab missing or non-functional")
        except Exception as e:
            print(e)
            missing_elements.append("Alignment Statistics and Run Parameters Tabs Container")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Interleaved_Locators.PIECHART_BARPLOT_CONTAINER))
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Interleaved_Locators.PIECHART_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Pie Chart Tab missing or non-functional")
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(locator.Interleaved_Locators.BARPLOT_TAB))
                element.click()
            except Exception as e:
                print(e)
                missing_elements.append("Bar Plot Tab missing or non-functional")
        except Exception as e:
            print(e)
            missing_elements.append("Pie Chart and Bar Plot Tabs Container")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < 12:
            missing_elements.append("Images missing.")
            print(len(images))
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Interleaved_Locators.IMAGE_SOURCES:
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
            title = WebDriverWait(self.driver, 100).until(
                EC.visibility_of_element_located(locator.Batch_Locators.TITLE))
        except Exception as e:
            print(e)
            missing_elements.append("Title not loading")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Locators.IMAGE_SOURCES):
            missing_elements.append("Images missing.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image.")

        tabs = []
        try:
            time.sleep(2)
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Batch_Locators.FANCF_UNTR_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF_untr")
        except Exception as e:
            print(e)
            missing_elements.append("FANCF_untr link missing or unclickable")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Batch_Locators.FANCF_BE1_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF_BE1")
        except Exception as e:
            print(e)
            missing_elements.append("FANCF_BE1 link missing or unclickable")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Batch_Locators.FANCF_BE2_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF_BE2")
        except Exception as e:
            print(e)
            missing_elements.append("FANCF_BE2 link missing or unclickable")
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.Batch_Locators.FANCF_BE3_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF_BE3")
        except Exception as e:
            print(e)
            missing_elements.append("FANCF_BE3 link missing or unclickable")
        for tab in range(len(tabs)):
            self.driver.switch_to.window(self.driver.window_handles[tab + 1])
            if tabs[tab] == "FANCF_untr":
                if not self.validate_batch_FANCF_untr():
                    missing_elements.append("FANCF_untr page validation failed")
            elif tabs[tab] == "FANCF_BE1":
                if not self.validate_batch_FANCF_BE1():
                    missing_elements.append("FANCF_BE1 page validation failed")
            elif tabs[tab] == "FANCF_BE2":
                if not self.validate_batch_FANCF_BE2():
                    missing_elements.append("FANCF_BE2 page validation failed")
            elif tabs[tab] == "FANCF_BE3":
                if not self.validate_batch_FANCF_BE3():
                    missing_elements.append("FANCF_BE3 page validation failed")
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.close_extra_tabs()
        self.driver.switch_to.window(self.driver.window_handles[0])
        if len(missing_elements) != 0:
            print("Missing elements for page validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_batch_FANCF_untr(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Locators.UNTR_IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF_untr.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Locators.UNTR_IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF_untr.")
        if len(missing_elements) != 0:
            print("Missing elements for FANCF_untr validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_batch_FANCF_BE1(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Locators.BE1_IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF_BE1.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Locators.BE1_IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF_BE1.")
        if len(missing_elements) != 0:
            print("Missing elements for FANCF_BE1 validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_batch_FANCF_BE2(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Locators.BE2_IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF_BE2.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Locators.BE2_IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF_BE2.")
        if len(missing_elements) != 0:
            print("Missing elements for FANCF_BE2 validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_batch_FANCF_BE3(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Batch_Locators.BE3_IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF_BE3.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Batch_Locators.BE3_IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF_BE3.")
        if len(missing_elements) != 0:
            print("Missing elements for FANCF_BE3 validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def close_extra_tabs(self):
        curr = self.driver.current_window_handle
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if handle != curr:
                self.driver.close()


class CRISPRessoPooledPage(BasePage):
    def enter_single_end_values(self):
        try:
            self.driver.execute_script("populatePooledSingleEnd()")
        except Exception as e:
            print(e)
            return False
        return True

    def validate_single_end(self):
        missing_elements = []
        try:
            title = WebDriverWait(self.driver, 50).until(
                EC.visibility_of_element_located(locator.Pooled_Locators.MODIFICATION_TITLE))
        except Exception as e:
            print(e)
            missing_elements.append("Page not loading")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.Pooled_Locators.IMAGE_SOURCES):
            missing_elements.append("Images missing from Pooled results.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.Pooled_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image.")
        if len(missing_elements) != 0:
            print("Missing elements for Pooled validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True


class CRISPRessoWGSPage(BasePage):
    def enter_cas9_values(self):
        try:
            self.driver.execute_script("populateWGSCas9()")
        except Exception as e:
            print(e)
            return False
        return True

    def validate_cas9(self):
        missing_elements = []
        try:
            title = WebDriverWait(self.driver, 100).until(
                EC.visibility_of_element_located(locator.WGS_Locators.OUTPUT_TITLE))
        except Exception as e:
            print(e)
            missing_elements.append("Title not loading")
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.WGS_Locators.IMAGE_SOURCES):
            missing_elements.append("Images missing.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.WGS_Locators.IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image.")

        tabs = []
        try:
            time.sleep(2)
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator.WGS_Locators.FANCF_LINK))
            href = element.get_attribute('href')
            self.driver.execute_script("window.open('%s', '_blank')" % href)
            tabs.append("FANCF")
        except Exception as e:
            print(e)
            missing_elements.append("FANCF link missing or unclickable")

        for tab in range(len(tabs)):
            self.driver.switch_to.window(self.driver.window_handles[tab + 1])
            if tabs[tab] == "FANCF":
                if not self.validate_WGS_FANCF():
                    missing_elements.append("FANCF page validation failed")
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.close_extra_tabs()
        self.driver.switch_to.window(self.driver.window_handles[0])
        if len(missing_elements) != 0:
            print("Missing elements for page validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def validate_WGS_FANCF(self):
        missing_elements = []
        images = self.driver.find_elements_by_tag_name('img')
        if len(images) < len(locator.WGS_Locators.FANCF_IMAGE_SOURCES):
            missing_elements.append("Images missing from FANCF.")
        for image in images:
            image = image.get_attribute('src')
            loc = image.rfind('/')
            image = image[loc + 1:]
            if image not in locator.WGS_Locators.FANCF_IMAGE_SOURCES:
                missing_elements.append(f"{image} is the incorrect image on FANCF.")
        if len(missing_elements) != 0:
            print("Missing elements for FANCF validation:")
            for missing in missing_elements:
                print(missing)
            return False
        return True

    def close_extra_tabs(self):
        curr = self.driver.current_window_handle
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if handle != curr:
                self.driver.close()
