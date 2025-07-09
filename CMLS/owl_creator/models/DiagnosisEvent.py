from CMLS.owl_creator.models.Event import Event

class DiagnosisEvent(Event):

    def __init__(self, id, icd_code, icd_URI, icd_version, icd_label, URI):
        self.has_id = id
        self.icd_code = icd_code
        self.icd_version = icd_version
        self.icd_label = icd_label

        self.icd_URI = icd_URI
        self.URI = URI

        #https://www.safetyandquality.gov.au/standards/clinical-care-standards/sepsis-clinical-care-standard/sepsis-codes
        self.sepsis_codes = [
            {"code_mimic": "A021", "code": "A02.1", "label": "Sepsis due to Salmonella"},
            {"code_mimic": "A037", "code": "A03.7", "label": "Sepsis due to Shigella"},
            {"code_mimic": "A207", "code": "A20.7", "label": "Sepsis due to plague"},
            {"code_mimic": "A217", "code": "A21.7", "label": "Sepsis due to tularaemia"},
            {"code_mimic": "A227", "code": "A22.7", "label": "Sepsis due to anthrax"},
            {"code_mimic": "A237", "code": "A23.7", "label": "Sepsis due to Brucella"},
            {"code_mimic": "A247", "code": "A24.7", "label": "Sepsis due to glanders and melioidosis"},
            {"code_mimic": "A267", "code": "A26.7", "label": "Sepsis due to Erysipelothrix [erysipeloid] [rhusiopathiae]"},
            {"code_mimic": "A2801", "code": "A28.01", "label": "Sepsis due to Pasteurella, not elsewhere classified"},
            {"code_mimic": "A2821", "code": "A28.21", "label": "Sepsis due to extraintestinal yersiniosis"},
            {"code_mimic": "A327", "code": "A32.7", "label": "Sepsis due to Listeria [monocytogenes]"},
            {"code_mimic": "A397", "code": "A39.7", "label": "Sepsis due to Meningococcus"},
            {"code_mimic": "A400", "code": "A40.0", "label": "Sepsis due to Streptococcus, group A"},
            {"code_mimic": "A401", "code": "A40.1", "label": "Sepsis due to Streptococcus, group B"},
            {"code_mimic": "A4021", "code": "A40.21", "label": "Sepsis due to Streptococcus, group D"},
            {"code_mimic": "A4022", "code": "A40.22", "label": "Sepsis due to Enterococcus"},
            {"code_mimic": "A403", "code": "A40.3", "label": "Sepsis due to Streptococcus pneumoniae"},
            {"code_mimic": "A408", "code": "A40.8", "label": "Other streptococcal sepsis"},
            {"code_mimic": "A409", "code": "A40.9", "label": "Streptococcal sepsis, unspecified"},
            {"code_mimic": "A410", "code": "A41.0", "label": "Sepsis due to Staphylococcus aureus"},
            {"code_mimic": "A411", "code": "A41.1", "label": "Sepsis due to other specified Staphylococcus"},
            {"code_mimic": "A412", "code": "A41.2", "label": "Sepsis due to unspecified Staphylococcus"},
            {"code_mimic": "A413", "code": "A41.3", "label": "Sepsis due to Haemophilus influenzae"},
            {"code_mimic": "A414", "code": "A41.4", "label": "Sepsis due to anaerobes"},
            {"code_mimic": "A4150", "code": "A41.50", "label": "Sepsis due to unspecified Gram-negative organisms"},
            {"code_mimic": "A4151", "code": "A41.51", "label": "Sepsis due to Escherichia coli [E. Coli]"},
            {"code_mimic": "A4152", "code": "A41.52", "label": "Sepsis due to Pseudomonas"},
            {"code_mimic": "A4158", "code": "A41.58", "label": "Sepsis due to other Gram-negative organisms"},
            {"code_mimic": "A418", "code": "A41.8", "label": "Sepsis due to other specified organism"},
            {"code_mimic": "A419", "code": "A41.9", "label": "Sepsis, unspecified"},
            {"code_mimic": "A427", "code": "A42.7", "label": "Sepsis due to actinomycosis"},
            {"code_mimic": "A547", "code": "A54.7", "label": "Sepsis due to Gonococcus"},
            {"code_mimic": "B0071", "code": "B00.71", "label": "Sepsis due to herpesviral [herpes simplex] infection"},
            {"code_mimic": "B377", "code": "B37.7", "label": "Sepsis due to Candida"},
            {"code_mimic": "O030", "code": "O03.0", "label": "Spontaneous abortion, incomplete, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O035", "code": "O03.5", "label": "Spontaneous abortion, complete or unspecified, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O040", "code": "O04.0", "label": "Medical abortion, incomplete, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O045", "code": "O04.5", "label": "Medical abortion, complete or unspecified, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O050", "code": "O05.0", "label": "Other abortion, incomplete, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O055", "code": "O05.5", "label": "Other abortion, complete or unspecified, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O060", "code": "O06.0", "label": "Unspecified abortion, incomplete, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O065", "code": "O06.5", "label": "Unspecified abortion, complete or unspecified, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O070", "code": "O07.0", "label": "Failed medical abortion, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O075", "code": "O07.5", "label": "Other and unspecified failed attempted abortion, complicated by genital tract and pelvic infection and sepsis"},
            {"code_mimic": "O080", "code": "O08.0", "label": "Genital tract and pelvic infection and sepsis following abortion and ectopic and molar pregnancy"},
            {"code_mimic": "O85", "code": "O85", "label": "Puerperal sepsis"},
            {"code_mimic": "P36", "code": "P36", "label": "Sepsis of newborn"}
        ]



    def is_sepsis(self):
            return bool(any(entry["code_mimic"] == self.icd_code for entry in self.sepsis_codes))
        