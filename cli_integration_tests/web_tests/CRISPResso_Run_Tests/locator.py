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


class Paired_Ends_Locators(object):
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
    NUCLEOTIDE_ZOOM = (By.ID, "zoomview_nucs_Reference")
    STATISTICS_PARAMETERS_CONTAINER = (By.ID, "log-tab")
    ALIGNMENT_STATISTICS_TAB = (By.ID, "log_aln-tab")
    RUN_PARAMETERS_TAB = (By.ID, "log_params-tab")
    PIECHART_BARPLOT_CONTAINER = (By.ID, "tabContent")
    PIECHART_TAB = (By.ID, "aln_pie-tab")
    BARPLOT_TAB = (By.ID, "aln_bar-tab")
    MODIFICATION_LENGTHS_TAB = (By.ID, "modification-lengths-tab")
    INDEL_CHARACTERIZATION_TAB = (By.ID, "indel-characterization-tabs")


class Single_End_Locators(object):
    IMAGE_SOURCES = ["1a.Read_barplot.png",
                     "1b.Alignment_pie_chart.png",
                     "1c.Alignment_barplot.png",
                     "2a.P23H.Nucleotide_percentage_quilt.png",
                     "2b.P23H.Nucleotide_percentage_quilt_around_sgRNA_GTGCGGAGCCACTTCGAGCAGC.png",
                     "3a.P23H.Indel_size_distribution.png",
                     "3b.P23H.Insertion_deletion_substitutions_size_hist.png",
                     "4a.P23H.Combined_insertion_deletion_substitution_locations.png",
                     "4b.P23H.Insertion_deletion_substitution_locations.png",
                     "4c.P23H.Quantification_window_insertion_deletion_substitution_locations.png",
                     "4d.P23H.Position_dependent_average_indel_size.png",
                     "9.P23H.Alleles_frequency_table_around_sgRNA_GTGCGGAGCCACTTCGAGCAGC.png"]
    NUCLEOTIDE_ZOOM = (By.ID, "zoomview_nucs_P23H")
    STATISTICS_PARAMETERS_CONTAINER = (By.ID, "log-tab")
    ALIGNMENT_STATISTICS_TAB = (By.ID, "log_aln-tab")
    RUN_PARAMETERS_TAB = (By.ID, "log_params-tab")
    PIECHART_BARPLOT_CONTAINER = (By.ID, "tabContent")
    PIECHART_TAB = (By.ID, "aln_pie-tab")
    BARPLOT_TAB = (By.ID, "aln_bar-tab")
    MODIFICATION_LENGTHS_TAB = (By.ID, "modification-lengths-tab")
    INDEL_CHARACTERIZATION_TAB = (By.ID, "indel-characterization-tab")


class Batch_Locators(object):
    IMAGE_SOURCES = ["Nucleotide_percentage_quilt_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                     "Nucleotide_percentage_quilt.png",
                     "Nucleotide_conversion_map_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                     "Nucleotide_conversion_map.png"]
    TITLE = (By.ID, "CRISPResso2_Batch_Output")
    FANCF_UNTR_LINK = (By.ID, "FANCF_untr")
    FANCF_BE1_LINK = (By.ID, "FANCF_BE1")
    FANCF_BE2_LINK = (By.ID, "FANCF_BE2")
    FANCF_BE3_LINK = (By.ID, "FANCF_BE3")
    UNTR_IMAGE_SOURCES = ["1a.Read_barplot.png",
                          "1b.Alignment_pie_chart.png",
                          "1c.Alignment_barplot.png",
                          "2a.Nucleotide_percentage_quilt.png",
                          "2a.Nucleotide_percentage_quilt.png",
                          "2b.Nucleotide_percentage_quilt_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                          "3a.Indel_size_distribution.png",
                          "3b.Insertion_deletion_substitutions_size_hist.png",
                          "4a.Combined_insertion_deletion_substitution_locations.png",
                          "4b.Insertion_deletion_substitution_locations.png",
                          "4c.Quantification_window_insertion_deletion_substitution_locations.png",
                          "4d.Position_dependent_average_indel_size.png",
                          "9.Alleles_frequency_table_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                          "10a.Substitution_frequencies_at_each_bp.png",
                          "10b.Substitution_frequency_barplot.png",
                          "10c.Substitution_frequency_barplot_in_quantification_window.png",
                          "10d.Log2_nucleotide_frequency_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                          "10e.Selected_conversion_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                          "10f.Selected_conversion_no_ref_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                          "10g.Selected_conversion_no_ref_scaled_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png"]
    BE1_IMAGE_SOURCES = ["1a.Read_barplot.png",
                         "1b.Alignment_pie_chart.png",
                         "1c.Alignment_barplot.png",
                         "2a.Nucleotide_percentage_quilt.png",
                         "2a.Nucleotide_percentage_quilt.png",
                         "2b.Nucleotide_percentage_quilt_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "3a.Indel_size_distribution.png",
                         "3b.Insertion_deletion_substitutions_size_hist.png",
                         "4a.Combined_insertion_deletion_substitution_locations.png",
                         "4b.Insertion_deletion_substitution_locations.png",
                         "4c.Quantification_window_insertion_deletion_substitution_locations.png",
                         "4d.Position_dependent_average_indel_size.png",
                         "9.Alleles_frequency_table_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10a.Substitution_frequencies_at_each_bp.png",
                         "10b.Substitution_frequency_barplot.png",
                         "10c.Substitution_frequency_barplot_in_quantification_window.png",
                         "10d.Log2_nucleotide_frequency_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10e.Selected_conversion_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10f.Selected_conversion_no_ref_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10g.Selected_conversion_no_ref_scaled_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png"]
    BE2_IMAGE_SOURCES = ["1a.Read_barplot.png",
                         "1b.Alignment_pie_chart.png",
                         "1c.Alignment_barplot.png",
                         "2a.Nucleotide_percentage_quilt.png",
                         "2a.Nucleotide_percentage_quilt.png",
                         "2b.Nucleotide_percentage_quilt_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "3a.Indel_size_distribution.png",
                         "3b.Insertion_deletion_substitutions_size_hist.png",
                         "4a.Combined_insertion_deletion_substitution_locations.png",
                         "4b.Insertion_deletion_substitution_locations.png",
                         "4c.Quantification_window_insertion_deletion_substitution_locations.png",
                         "4d.Position_dependent_average_indel_size.png",
                         "9.Alleles_frequency_table_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10a.Substitution_frequencies_at_each_bp.png",
                         "10b.Substitution_frequency_barplot.png",
                         "10c.Substitution_frequency_barplot_in_quantification_window.png",
                         "10d.Log2_nucleotide_frequency_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10e.Selected_conversion_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10f.Selected_conversion_no_ref_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10g.Selected_conversion_no_ref_scaled_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png"]
    BE3_IMAGE_SOURCES = ["1a.Read_barplot.png",
                         "1b.Alignment_pie_chart.png",
                         "1c.Alignment_barplot.png",
                         "2a.Nucleotide_percentage_quilt.png",
                         "2a.Nucleotide_percentage_quilt.png",
                         "2b.Nucleotide_percentage_quilt_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "3a.Indel_size_distribution.png",
                         "3b.Insertion_deletion_substitutions_size_hist.png",
                         "4a.Combined_insertion_deletion_substitution_locations.png",
                         "4b.Insertion_deletion_substitution_locations.png",
                         "4c.Quantification_window_insertion_deletion_substitution_locations.png",
                         "4d.Position_dependent_average_indel_size.png",
                         "9.Alleles_frequency_table_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10a.Substitution_frequencies_at_each_bp.png",
                         "10b.Substitution_frequency_barplot.png",
                         "10c.Substitution_frequency_barplot_in_quantification_window.png",
                         "10d.Log2_nucleotide_frequency_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10e.Selected_conversion_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10f.Selected_conversion_no_ref_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png",
                         "10g.Selected_conversion_no_ref_scaled_at_Cs_around_sgRNA_GGAATCCCTTCTGCAGCACC.png"]


class Interleaved_Locators(object):
    IMAGE_SOURCES = ["1a.Read_barplot.png",
                     "1b.Alignment_pie_chart.png",
                     "1c.Alignment_barplot.png",
                     "2a.Inferred.Nucleotide_percentage_quilt.png",
                     "2b.Inferred.Nucleotide_percentage_quilt_around_Guessed-sgRNA.png",
                     "3a.Inferred.Indel_size_distribution.png",
                     "3b.Inferred.Insertion_deletion_substitutions_size_hist.png",
                     "4a.Inferred.Combined_insertion_deletion_substitution_locations.png",
                     "4b.Inferred.Insertion_deletion_substitution_locations.png",
                     "4c.Inferred.Quantification_window_insertion_deletion_substitution_locations.png",
                     "4d.Inferred.Position_dependent_average_indel_size.png",
                     "9.Inferred.Alleles_frequency_table_around_Guessed-sgRNA.png",
                     "2a.Inferred2.Nucleotide_percentage_quilt.png",
                     "2b.Inferred2.Nucleotide_percentage_quilt_around_Guessed-sgRNA.png",
                     "3a.Inferred2.Indel_size_distribution.png",
                     "3b.Inferred2.Insertion_deletion_substitutions_size_hist.png",
                     "4a.Inferred2.Combined_insertion_deletion_substitution_locations.png",
                     "4b.Inferred2.Insertion_deletion_substitution_locations.png",
                     "4c.Inferred2.Quantification_window_insertion_deletion_substitution_locations.png",
                     "4d.Inferred2.Position_dependent_average_indel_size.png",
                     "9.Inferred2.Alleles_frequency_table_around_Guessed-sgRNA.png"]
    NUCLEOTIDE_ZOOM = (By.ID, "zoomview_nucs_P23H")
    STATISTICS_PARAMETERS_CONTAINER = (By.ID, "log-tab")
    ALIGNMENT_STATISTICS_TAB = (By.ID, "log_aln-tab")
    RUN_PARAMETERS_TAB = (By.ID, "log_params-tab")
    PIECHART_BARPLOT_CONTAINER = (By.ID, "tabContent")
    PIECHART_TAB = (By.ID, "aln_pie-tab")
    BARPLOT_TAB = (By.ID, "aln_bar-tab")
    MODIFICATION_LENGTHS_TAB = (By.ID, "modification-lengths-tab")
    INDEL_CHARACTERIZATION_TAB = (By.ID, "indel-characterization-tab")


class Pooled_Locators(object):
    MODIFICATION_TITLE = (By.ID, "modification_summary_title")
    IMAGE_SOURCES = ["CRISPRessoPooled_reads_summary.png",
                     "CRISPRessoPooled_modification_summary.png"]
