# Image Services Data Management Tools 

This directory contains scripts and tools for managing data to be served by ASF via ArcGIS Image Server or ArcGIS Imagery Dedicated.

## Process New Granules Script
The process_new_granules.py script looks for new acquisitions to process and add to an existing project name.

The script requires a JSON configuration file that defines the search parameters for the project and the HyP3 processing parameters to be applied when generating the RTC products.

### Running the Script
To run the script, open a terminal and ensure that the hyp3-image-services conda environment is activated. Either cd to the directory that contains the script, or call the full path when running the command.

Type "python" followed by the script name (and path if not currently in that directory) and the parameter JSON file for the desired project:

```
>python process_new_granules.py [parameter_file.json]
```
Example using the alaska_rivers configuration file:

```
(hyp3-image-services) C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\data_management>python process_new_granules.py alaska_rivers.json
```

## HyP3 Transfer Script

This script transfers RTC geotiffs (unzipped) for a particular project from the HyP3 S3 bucket to a public bucket for use in mosaic datasets.

### Running the Script

To run the script, open a terminal, navigate to the desired Python instance directory, and run the script (include full path to the transfer script):

```cd C:\Python38```

```C:\Python38>python C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\data_management\hyp3_transfer_script.py```

The script will prompt you for:
- your Earthdata username and password
- the HyP3 project name for the data to copy
- the bucket name (i.e. ```hyp3-nasa-disasters```)

No quotes are required around the parameter text entries. 

The script will copy over the VV.tif, VH.tif, rgb.tif and VV.xml files, tagging each file with a prefix matching the project name. 

The script will only copy over data that is not already in the bucket, so you can add additional products to a project name and rerun the script to add the new products to the destination bucket.

## Installation
These scripts work best in a conda environment, which is defined in the environment.yml file.

To pip install or upgrade hyp3_sdk module to a specific instance of python:

```C:\Python38>python -m pip install --upgrade hyp3_sdk```