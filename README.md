# A conceptual model for discovering implicit temporal knowledge in clinical data

##Abstract

The ability to query and reason over temporally evolving clinical data is key to improving decision-making in intensive care units (ICUs). Hidden synergies between medical markers are searched by clinicians and medical staff in order to make decisions about a particular critical case in intensive care. In this paper, we propose a competency-question-guided conceptual modeling approach to transform raw ICU data into an OWL-Time-compliant temporal knowledge graph. Based on clinically relevant concepts extracted from competency questions and aligned with the data schema, we design an ontology for representing temporally anchored events such as biomarker measurements, symptoms, and treatments. We then propose a pipeline to instantiate this ontology with ICU data from MIMIC-IV dataset and compute temporal relations dynamically during post-processing, enabling flexible querying across event timelines. We demonstrate the benefit of our approach through a use case on bloodstream infection detection in ICU patients, showing how temporally grounded questions can uncover clinically relevant temporal knowledge not explicitly present in the source data, and make it accessible through a reproducible, queryable graph.

## Getting Started

### Data
This project relies in part on the **MIMIC-IV** clinical databases, which are **subject to access restrictions imposed by PhysioNet** due to privacy and ethical considerations.

**MIMIC data is not included in this repository.**  
To reproduce our experiments, you must:

1. Apply for access at [https://physionet.org/](https://physionet.org/)
2. Complete the required training and sign the appropriate data use agreements (including the CITI "Data or Specimens Only Research" course)
3. Download the datasets once your application has been approved

Once you have obtained access to MIMIC, note that this project assumes the data is available through a local instance of **DukeDB**, a clinical database platform used to support querying and reasoning over structured clinical data.

### Project organisation
CMLS/
├── owl_creator/ # Module for building the OWL ontology from MIMIC data
│ ├── Application/ # Main logic for ontology generation
│ └── config/ # Configuration files (e.g., mimic_owl.ini)
│ └── database/ # Connection to dukeDB and queries
│ └── models/ # Business objects
│ └── tools/ # Logger
├── owl_definition/ # Contains the ontology design
├── owl_output/ # Contains the result of the instanciation of the process

### Configuring the ini file
Before running the process, you must configure the 'mimic_owl.ini' file located in 'owl_creator/config/'.


### Execute the process
To run the process, you must execute the main_owlcreator.py file.





