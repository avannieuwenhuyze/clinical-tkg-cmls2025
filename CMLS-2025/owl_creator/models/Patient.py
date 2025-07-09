

class Patient:

    def __init__(self,subject_id,gender,age,comorbidity,charlson,sepsis3,URI):
        self.has_subject_id = subject_id
        self.has_gender = gender
        self.has_age = age
        self.URI=URI
        self.has_comorbidity = comorbidity
        self.charlson_score =charlson

        self.sepsis3 = sepsis3





        