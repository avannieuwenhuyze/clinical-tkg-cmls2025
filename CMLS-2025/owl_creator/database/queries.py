
from CMLS.owl_creator.database.duck_database import Duck_database
from datetime import datetime

class Queries():
    
    def __init__(self, config_path):
        self.config_path = config_path



    def cohort_selection(self,limit):
        """
        Selects a cohort of patients.

        This method applies specific criteria to filter a list of patients to include in the analysis.

        Selection criteria:
            - Only the first ICU stay for each patient is considered
            - Patients aged between 18 and 89 years
            - ICU stay duration greater than 24 hours and less than 100 days

        Returns:
            Dataframe: A dataframe containing the subject_id (patient id), hadm_id (admisison id), stay_id (ICU stay id),
        """

        db = Duck_database(self.config_path)

        query = """  
                    SELECT subject_id, hadm_id, stay_id, 
                    FROM (
                        SELECT p.subject_id, 
                            a.hadm_id, 
                            i.stay_id, 
                            i.intime, 
                            i.outtime,
                

                            ROW_NUMBER() OVER (PARTITION BY p.subject_id ORDER BY i.intime ASC) AS row_num

                        FROM main.patients p
                        INNER JOIN main.admissions a ON a.subject_id = p.subject_id
                        INNER JOIN main.icustays i ON i.subject_id = p.subject_id AND i.hadm_id = a.hadm_id
                        INNER JOIN main.age a2 on a2.subject_id = p.subject_id and a2.hadm_id = a.hadm_id
                    
                        WHERE
                            DATE_DIFF('hour' , i.intime, i.outtime) > 24
                            AND DATE_DIFF('hour' , i.intime, i.outtime) < 2400
                            AND a2.age BETWEEN 18 AND 89
                            
                    ) subquery
                    WHERE row_num = 1
                    ORDER BY subject_id asc
                """
        if limit.isnumeric() :
            query += "LIMIT "+str(limit)

        db_instance = db.connect()
        results = db_instance.execute(query,).fetchdf()
        db.close()

        return results


    #---------------
    # PATIENT
    #---------------
    def get_patient_informations(self,subject_id,hadm_id):

        db = Duck_database(self.config_path)

        query = """
                SELECT p.subject_id , a.hadm_id , a2.age, p.gender, p.dod 
                FROM main.patients p
                INNER JOIN main.admissions a on a.subject_id = p.subject_id 
                INNER JOIN main.age a2 on a2.hadm_id = a.hadm_id and a2.subject_id = p.subject_id 
                INNER JOIN main.icustays i on i.subject_id = p.subject_id and i.hadm_id = a.hadm_id 
                WHERE p.subject_id = ?
                AND a.hadm_id = ?
                """

        db_instance = db.connect()
        results = db_instance.execute(query,(int(subject_id),int(hadm_id))).fetchnumpy()
        db.close()

        return (results)
    
    def get_sepsis3(self,subject_id,stay_id):

        db = Duck_database(self.config_path)

        query = """
                SELECT count(1) as isSepsis
                FROM main.sepsis3
                WHERE subject_id = ?
                AND stay_id = ?
            """ 
        
        db_instance = db.connect()
        results = db_instance.execute(query,(int(subject_id),int(stay_id))).fetchnumpy()
        db.close()

        return results


    #---------------
    # ICU STAY
    #---------------
    def get_icustay_informations(self,subject_id, hadm_id,stay_id):
        db = Duck_database(self.config_path)

        query = """
                SELECT i.intime as hasBeginning, i.outtime as hasEnd , DATE_DIFF('hours',i.intime,i.outtime) as hasDuration
                FROM main.icustays i 
                WHERE i.stay_id = ?
                AND i.hadm_id = ?
                AND i.subject_id = ?
                                """

        db_instance = db.connect()
        results = db_instance.execute(query,(int(stay_id),int(hadm_id),int(subject_id))).fetchnumpy()
        db.close()

        return (results)
    

    #---------------
    # BIOMARKER
    #---------------
    def get_biomarkers(self,subject_id, hadm_id,icu_begin,icu_end,limit=None):
        db = Duck_database(self.config_path)
        query = """
            SELECT 
            l.labevent_id as id,
            dl.label as hasBiomarkerName, 
            dl.category as hasCategory, 
            dl.fluid as hasSpecimenType, 
            l.value as hasValue, 
            l.valuenum as hasValueNum, 
            l.comments as hasValueText,
            l.valueuom as hasUnit,
            l.charttime as hasTime,
            l.ref_range_lower as hasRefRangeLower,
            l.ref_range_upper as hasRefRangeUpper
            FROM main.labevents l 
            INNER JOIN main.d_labitems dl  on dl.itemid = l.itemid
            WHERE l.subject_id = ?
            AND l.hadm_id = ?
            AND l.charttime between ? and ?
            ORDER by l.charttime asc
            """
        
        if limit.isnumeric() :
            query += "LIMIT "+str(limit)

        db_instance = db.connect()
        results = db_instance.execute(query,(int(subject_id),int(hadm_id),icu_begin,icu_end)).fetchnumpy()
        db.close()

        return (results)
    

    #---------------
    # CLINICAL SIGNS
    #---------------

    def get_clinicals_signs(self,subject_id,stay_id,icu_begin,icu_end,limit=None):
        db = Duck_database(self.config_path)
        query ="""
            SELECT 
            di.label as hasClinicalSignType,
            di.category as hasCategory,
            di.unitname as hasUnit,
            c.value as hasValue, 
            c.valuenum as hasValueNum, 
            c.charttime as hasTime
            FROM main.chartevents c
            INNER JOIN main.d_items di ON di.itemid = c.itemid
            WHERE  c.subject_id = ?
            AND c.stay_id= ?
            AND di.category IN ('Routine Vital Signs')
            AND di.param_type IN ('Numeric')
            AND c.charttime between ? and ?
            ORDER BY c.charttime asc
        """
        if limit.isnumeric() :
            query += "LIMIT "+str(limit)
        
        db_instance = db.connect()
        results = db_instance.execute(query,(int(subject_id),int(stay_id),icu_begin,icu_end)).fetchnumpy()

        db.close()

        return (results)
    

    #---------------
    # MICROBIOLOGY EVENTS (BLOOD)
    #---------------
    def get_microbiology(self,subject_id,hadm_id,icu_begin,icu_end,limit=None):
        db = Duck_database(self.config_path)
        query ="""
                SELECT
                me.microevent_id as hasId,
                me.charttime as hasTime,
                me.spec_type_desc as hasSpecimenType,
                me.org_name as hasOrganismName,
                me.ab_name as hasAntibioticName,
                me.interpretation as hasInterpretation
                FROM main.microbiologyevents me
                WHERE me.subject_id = ?
                AND me.hadm_id = ?
                AND LOWER(me.spec_type_desc) LIKE '%blood%'
                AND me.charttime BETWEEN ? AND ?
                ORDER BY me.charttime ASC
        """
        if limit.isnumeric() :
            query += "LIMIT "+str(limit)
        
        db_instance = db.connect()
        results = db_instance.execute(query,(int(subject_id),int(hadm_id),icu_begin,icu_end)).fetchnumpy()

        db.close()

        return (results)

    #------------------------------
    # ANTIBIOTIC ADMINISTRATION
    #-----------------------------
    def get_antibiotics_prescriptions(self,subject_id,hadm_id,icu_begin,icu_end,limit=None):
        db = Duck_database(self.config_path)
        query = """
                    SELECT 
                    p.starttime as hasBeginning, 
                    p.stoptime as hasEnd,
                    p.stoptime - p.starttime as hasDuration,
                    p.drug as administerDrug,
                    p.dose_val_rx as hasDose,
                    p.dose_unit_rx as hasUnit,
                    p.route as hasRoute
                    FROM main.prescriptions p 
                    WHERE p.subject_id = ?
                    AND p.hadm_id = ?
                    AND p.starttime BETWEEN ? AND ?
                    AND p.stoptime > p.starttime
                    ORDER BY p.starttime 
                """
        if limit.isnumeric() :
            query += "LIMIT "+str(limit)

        db_instance = db.connect()
        results = db_instance.execute(query,(int(subject_id),int(hadm_id),icu_begin,icu_end)).fetchnumpy()

        db.close()

        return (results)
        
    
    #-----------------------------
    # DIAGNOSIS
    #-----------------------------
    def get_diagnosis(self,subject_id,hadm_id,limit=None):
        db = Duck_database(self.config_path)
        query = """
                   SELECT
                    d.icd_code as hasICDCode,
                    d.icd_version as hasICDVersion,
                    di.long_title as diagnosis_label 
                FROM main.diagnoses_icd d
                INNER JOIN main.d_icd_diagnoses di
                    ON d.icd_code = di.icd_code AND d.icd_version = di.icd_version
                WHERE d.subject_id = ?
                AND d.hadm_id = ?
                """
        if limit.isnumeric() :
            query += "LIMIT "+str(limit)

        db_instance = db.connect()
        results = db_instance.execute(query,(int(subject_id),int(hadm_id))).fetchnumpy()

        db.close()

        return (results)
    

    #-----------------------------
    # COMMORBIDITY
    #-----------------------------

    def get_comorbidity(self,subject_id,hadm_id,limit=None):
        db = Duck_database(self.config_path)

        query = """
    
                    WITH diag AS (
                        SELECT
                            hadm_id
                            , CASE WHEN icd_version = 9 THEN icd_code ELSE NULL END AS icd9_code
                            , CASE WHEN icd_version = 10 THEN icd_code ELSE NULL END AS icd10_code
                        FROM main.diagnoses_icd
                    )

                    , com AS (
                        SELECT
                            ad.hadm_id

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) IN ('410', '412')
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('I21', 'I22')
                                OR
                                SUBSTR(icd10_code, 1, 4) = 'I252'
                                THEN 1
                                ELSE 0 END) AS myocardial_infarct

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) = '428'
                                OR
                                SUBSTR(
                                    icd9_code, 1, 5
                                ) IN ('39891', '40201', '40211', '40291', '40401', '40403'
                                    , '40411', '40413', '40491', '40493')
                                OR
                                SUBSTR(icd9_code, 1, 4) BETWEEN '4254' AND '4259'
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('I43', 'I50')
                                OR
                                SUBSTR(
                                    icd10_code, 1, 4
                                ) IN ('I099', 'I110', 'I130', 'I132', 'I255', 'I420'
                                    , 'I425', 'I426', 'I427', 'I428', 'I429', 'P290'
                                )
                                THEN 1
                                ELSE 0 END) AS congestive_heart_failure

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) IN ('440', '441')
                                OR
                                SUBSTR(
                                    icd9_code, 1, 4
                                ) IN ('0930', '4373', '4471', '5571', '5579', 'V434')
                                OR
                                SUBSTR(icd9_code, 1, 4) BETWEEN '4431' AND '4439'
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('I70', 'I71')
                                OR
                                SUBSTR(icd10_code, 1, 4) IN ('I731', 'I738', 'I739', 'I771', 'I790'
                                                            , 'I792'
                                                            , 'K551'
                                                            , 'K558'
                                                            , 'K559'
                                                            , 'Z958'
                                                            , 'Z959'
                                )
                                THEN 1
                                ELSE 0 END) AS peripheral_vascular_disease

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) BETWEEN '430' AND '438'
                                OR
                                SUBSTR(icd9_code, 1, 5) = '36234'
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('G45', 'G46')
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'I60' AND 'I69'
                                OR
                                SUBSTR(icd10_code, 1, 4) = 'H340'
                                THEN 1
                                ELSE 0 END) AS cerebrovascular_disease

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) = '290'
                                OR
                                SUBSTR(icd9_code, 1, 4) IN ('2941', '3312')
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('F00', 'F01', 'F02', 'F03', 'G30')
                                OR
                                SUBSTR(icd10_code, 1, 4) IN ('F051', 'G311')
                                THEN 1
                                ELSE 0 END) AS dementia

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) BETWEEN '490' AND '505'
                                OR
                                SUBSTR(icd9_code, 1, 4) IN ('4168', '4169', '5064', '5081', '5088')
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'J40' AND 'J47'
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'J60' AND 'J67'
                                OR
                                SUBSTR(icd10_code, 1, 4) IN ('I278', 'I279', 'J684', 'J701', 'J703')
                                THEN 1
                                ELSE 0 END) AS chronic_pulmonary_disease

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) = '725'
                                OR
                                SUBSTR(icd9_code, 1, 4) IN ('4465', '7100', '7101', '7102', '7103'
                                                            , '7104', '7140', '7141', '7142', '7148'
                                )
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('M05', 'M06', 'M32', 'M33', 'M34')
                                OR
                                SUBSTR(icd10_code, 1, 4) IN ('M315', 'M351', 'M353', 'M360')
                                THEN 1
                                ELSE 0 END) AS rheumatic_disease

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) IN ('531', '532', '533', '534')
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('K25', 'K26', 'K27', 'K28')
                                THEN 1
                                ELSE 0 END) AS peptic_ulcer_disease

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) IN ('570', '571')
                                OR
                                SUBSTR(
                                    icd9_code, 1, 4
                                ) IN ('0706', '0709', '5733', '5734', '5738', '5739', 'V427')
                                OR
                                SUBSTR(
                                    icd9_code, 1, 5
                                ) IN ('07022', '07023', '07032', '07033', '07044', '07054')
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('B18', 'K73', 'K74')
                                OR
                                SUBSTR(
                                    icd10_code, 1, 4
                                ) IN ('K700', 'K701', 'K702', 'K703', 'K709', 'K713'
                                    , 'K714', 'K715', 'K717', 'K760', 'K762'
                                    , 'K763', 'K764', 'K768', 'K769', 'Z944')
                                THEN 1
                                ELSE 0 END) AS mild_liver_disease

                            
                            , MAX(CASE WHEN
                                SUBSTR(
                                    icd9_code, 1, 4
                                ) IN ('2500', '2501', '2502', '2503', '2508', '2509')
                                OR
                                SUBSTR(
                                    icd10_code, 1, 4
                                ) IN ('E100', 'E101', 'E106', 'E108', 'E109', 'E110', 'E111'
                                    , 'E116'
                                    , 'E118'
                                    , 'E119'
                                    , 'E120'
                                    , 'E121'
                                    , 'E126'
                                    , 'E128'
                                    , 'E129'
                                    , 'E130'
                                    , 'E131'
                                    , 'E136'
                                    , 'E138'
                                    , 'E139'
                                    , 'E140'
                                    , 'E141', 'E146', 'E148', 'E149')
                                THEN 1
                                ELSE 0 END) AS diabetes_without_cc

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 4) IN ('2504', '2505', '2506', '2507')
                                OR
                                SUBSTR(
                                    icd10_code, 1, 4
                                ) IN ('E102', 'E103', 'E104', 'E105', 'E107', 'E112', 'E113'
                                    , 'E114'
                                    , 'E115'
                                    , 'E117'
                                    , 'E122'
                                    , 'E123'
                                    , 'E124'
                                    , 'E125'
                                    , 'E127'
                                    , 'E132'
                                    , 'E133'
                                    , 'E134'
                                    , 'E135'
                                    , 'E137'
                                    , 'E142'
                                    , 'E143', 'E144', 'E145', 'E147')
                                THEN 1
                                ELSE 0 END) AS diabetes_with_cc

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) IN ('342', '343')
                                OR
                                SUBSTR(icd9_code, 1, 4) IN ('3341', '3440', '3441', '3442'
                                                            , '3443', '3444', '3445', '3446', '3449'
                                )
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('G81', 'G82')
                                OR
                                SUBSTR(icd10_code, 1, 4) IN ('G041', 'G114', 'G801', 'G802', 'G830'
                                                            , 'G831'
                                                            , 'G832'
                                                            , 'G833'
                                                            , 'G834'
                                                            , 'G839'
                                )
                                THEN 1
                                ELSE 0 END) AS paraplegia

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) IN ('582', '585', '586', 'V56')
                                OR
                                SUBSTR(icd9_code, 1, 4) IN ('5880', 'V420', 'V451')
                                OR
                                SUBSTR(icd9_code, 1, 4) BETWEEN '5830' AND '5837'
                                OR
                                SUBSTR(
                                    icd9_code, 1, 5
                                ) IN (
                                    '40301'
                                    , '40311'
                                    , '40391'
                                    , '40402'
                                    , '40403'
                                    , '40412'
                                    , '40413'
                                    , '40492'
                                    , '40493'
                                )
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('N18', 'N19')
                                OR
                                SUBSTR(icd10_code, 1, 4) IN ('I120', 'I131', 'N032', 'N033', 'N034'
                                                            , 'N035'
                                                            , 'N036'
                                                            , 'N037'
                                                            , 'N052'
                                                            , 'N053'
                                                            , 'N054'
                                                            , 'N055'
                                                            , 'N056'
                                                            , 'N057'
                                                            , 'N250'
                                                            , 'Z490'
                                                            , 'Z491'
                                                            , 'Z492'
                                                            , 'Z940'
                                                            , 'Z992'
                                )
                                THEN 1
                                ELSE 0 END) AS renal_disease

                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) BETWEEN '140' AND '172'
                                OR
                                SUBSTR(icd9_code, 1, 4) BETWEEN '1740' AND '1958'
                                OR
                                SUBSTR(icd9_code, 1, 3) BETWEEN '200' AND '208'
                                OR
                                SUBSTR(icd9_code, 1, 4) = '2386'
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('C43', 'C88')
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'C00' AND 'C26'
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'C30' AND 'C34'
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'C37' AND 'C41'
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'C45' AND 'C58'
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'C60' AND 'C76'
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'C81' AND 'C85'
                                OR
                                SUBSTR(icd10_code, 1, 3) BETWEEN 'C90' AND 'C97'
                                THEN 1
                                ELSE 0 END) AS malignant_cancer

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 4) IN ('4560', '4561', '4562')
                                OR
                                SUBSTR(icd9_code, 1, 4) BETWEEN '5722' AND '5728'
                                OR
                                SUBSTR(
                                    icd10_code, 1, 4
                                ) IN ('I850', 'I859', 'I864', 'I982', 'K704', 'K711'
                                    , 'K721', 'K729', 'K765', 'K766', 'K767')
                                THEN 1
                                ELSE 0 END) AS severe_liver_disease

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) IN ('196', '197', '198', '199')
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('C77', 'C78', 'C79', 'C80')
                                THEN 1
                                ELSE 0 END) AS metastatic_solid_tumor

                            
                            , MAX(CASE WHEN
                                SUBSTR(icd9_code, 1, 3) IN ('042', '043', '044')
                                OR
                                SUBSTR(icd10_code, 1, 3) IN ('B20', 'B21', 'B22', 'B24')
                                THEN 1
                                ELSE 0 END) AS aids
                        FROM main.admissions ad
                        LEFT JOIN diag
                            ON ad.hadm_id = diag.hadm_id
                        GROUP BY ad.hadm_id
                    )

                    , ag AS (
                        SELECT
                            hadm_id
                            , age
                            , CASE WHEN age <= 50 THEN 0
                                WHEN age <= 60 THEN 1
                                WHEN age <= 70 THEN 2
                                WHEN age <= 80 THEN 3
                                ELSE 4 END AS age_score
                        FROM main.age
                    )

                    SELECT
                        ad.subject_id
                        , ad.hadm_id
                        , ag.age_score
                        , myocardial_infarct
                        , congestive_heart_failure
                        , peripheral_vascular_disease
                        , cerebrovascular_disease
                        , dementia
                        , chronic_pulmonary_disease
                        , rheumatic_disease
                        , peptic_ulcer_disease
                        , mild_liver_disease
                        , diabetes_without_cc
                        , diabetes_with_cc
                        , paraplegia
                        , renal_disease
                        , malignant_cancer
                        , severe_liver_disease
                        , metastatic_solid_tumor
                        , aids
                        , age_score
                        + myocardial_infarct + congestive_heart_failure
                        + peripheral_vascular_disease + cerebrovascular_disease
                        + dementia + chronic_pulmonary_disease
                        + rheumatic_disease + peptic_ulcer_disease
                        + GREATEST(mild_liver_disease, 3 * severe_liver_disease)
                        + GREATEST(2 * diabetes_with_cc, diabetes_without_cc)
                        + GREATEST(2 * malignant_cancer, 6 * metastatic_solid_tumor)
                        + 2 * paraplegia + 2 * renal_disease
                        + 6 * aids
                        AS charlson_comorbidity_index
                    FROM main.admissions ad
                    LEFT JOIN com
                        ON ad.hadm_id = com.hadm_id
                    LEFT JOIN ag
                        ON com.hadm_id = ag.hadm_id
                    WHERE ad.subject_id = ?
                    AND ad.hadm_id = ?
        """

        if limit.isnumeric() :
            query += "LIMIT "+str(limit)

        db_instance = db.connect()
        results = db_instance.execute(query,(int(subject_id),int(hadm_id))).fetchnumpy()

        db.close()

        return (results)

