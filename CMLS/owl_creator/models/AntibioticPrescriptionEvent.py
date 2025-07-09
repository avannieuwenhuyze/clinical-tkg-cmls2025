from CMLS.owl_creator.models.Event import Event


class AntibioticPrescriptionEvent(Event):

    def __init__(self,id,drug,beginning,end,duration,route,dose,unit,unitURI,antibioticURI,URI):
        self.has_id = id
        self.has_beginning = beginning
        self.has_duration = duration
        self.has_end = end
        self.has_route = route
        self.has_dose = dose #Must be a string
        self.has_unit = unit
        self.has_drug_name = drug

        self.URI = URI
        self.unit_URI = unitURI
        self.antibiotic_URI = antibioticURI


