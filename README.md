# A project for comparing the force measured by three different snow penetrometers.

## Overview:
- Data used in this project can be found https://huggingface.co/datasets/cryogars/penetrometer_data, and running process_ingest/get_data.py will download the dataset into the project directory.
- The structure of the data is preserved and should be loaded in the main directory
- The workflow includes:
- Ingesting and organizing profiles
- Inspecting and cleaning SMP and Snow Scope profiles
- Dynamic Time Warping to match profiles
- Comparing penetration force across stratigraphic layers


  
