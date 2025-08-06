# OpenRIS
OpenRIS is a tool designed to provide a RIS-type system for managing radiology workflow. It uses Flask for backend management and a set of HTML and JavaScript pages for the frontend. At the moment, it offers the following features :
     
- Patient Management
- Order scheduling/management/tracking
- Worklist creation
- Report creation/labelisation
- Communication with a PACS server (Orthanc)

## Installation
In order to work properly, OpenRIS requires a MongoDB database manager such as a Docker image (default port) and a
version of Orthanc (default port) with plugins to manage worklists
(https://orthanc.uclouvain.be/book/plugins/worklists-plugin.html) and Python scripts (https://orthanc.uclouvain.be/book/plugins/python.html),
as well as a web viewer installed and configured.

Be sure to configure Orthanc correctly by providing it with the Python script located in
src/orthanc-scripts/orthanc_main_script.py and configure the script to use the correct Python environment
(site-packages marked by a TODO inside the script).

Once the DB and Orthanc are correctly instantiated, it is essential to check the ports used by these applications to
ensure they match the ports used by OpenRIS and to configure the config.py file.

## Caution
Since OpenRIS use a NER model (https://github.com/Stanford-AIMI/radgraph) to labelise its reports, the generated
annotations can be wrong or unprecise. OpenRIS is an Open Source application, you are free to add more postprocessing
or preprocessing functions

At the moment, the major issue encounter in OpenRIS is the handling of HL7 protocol for its communication with a system
like a HIS. To overcome this, you might have to implement an interface and the send function of OpenRIS to handle HL7 through MLLP server and redirect it
to OpenRIS with /receive-hl7 route instead of using HTTP to wrap HL7 message.
