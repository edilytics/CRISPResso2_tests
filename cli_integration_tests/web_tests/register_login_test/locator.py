from selenium.webdriver.common.by import By


class Base_Page_Locators(object):
    SUBMIT_BUTTON = (By.ID, "submit")
    ERROR_CONTAINER = (By.ID, "errorPageContainer")


class Register_Login_Locators(object):
    NAME_FIELD = (By.ID, "name")
    NAME_VALUE = "TEST_USER"
    USERNAME_FIELD = (By.ID, "username")
    USERNAME_VALUE = "TEST_USERNAME"
    EMAIL_FIELD = (By.ID, "email")
    EMAIL_VALUE = "TEST_EMAIL@Edilytics.com"
    PASSWORD_FIELD = (By.ID, "password")
    CONFIRM_PASSWORD_FIELD = (By.ID, "password2")
    PASSWORD_VALUE = "TEST_PASSWORD"


class Paired_Ends_Results_Locators(object):
    STATISTICS_PARAMETERS_CONTAINER = (By.ID, "log-tab")
    ALIGNMENT_STATISTICS_TAB = (By.ID, "log_aln-tab")
    RUN_PARAMETERS_TAB = (By.ID, "log_params-tab")
    IMAGE_SOURCES = ["1a.Read_barplot.png",
                     "1b.Alignment_pie_chart.png",
                     "1c.Alignment_barplot.png",
                     "2a.Nucleotide_percentage_quilt.png",
                     "3a.Indel_size_distribution.png",
                     "3b.Insertion_deletion_substitutions_size_hist.png",
                     "4a.Combined_insertion_deletion_substitution_locations.png",
                     "4b.Insertion_deletion_substitution_locations.png",
                     "4c.Quantification_window_insertion_deletion_substitution_locations.png",
                     "4d.Position_dependent_average_indel_size.png"]
    PIECHART_BARPLOT_CONTAINER = (By.ID, "aln-tab")
    PIECHART_TAB = (By.ID, "aln_pie-tab")
    BARPLOT_TAB = (By.ID, "aln_bar-tab")
    NUCLEOTIDE_ZOOM = (By.ID, "zoomview_nucs_Reference")
