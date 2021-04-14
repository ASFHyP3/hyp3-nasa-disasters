# Image Services Data Management Tools 

This directory contains scripts and tools for managing data to be served by ASF via ArcGIS Image Server or ArcGIS Imagery Dedicated.

## HyP3 Transfer Script

This script transfers RTC geotiffs for a particular project from the HyP3 S3 bucket to a bucket to be accessed to generate a mosaic dataset.

To pip install or upgrade hyp3_sdk module to a specific instance of python:

```C:\Python38>python -m pip install --upgrade hyp3_sdk```

### Running the Script

To run the script, navigate to the desired Python instance directory, and run the script (include full path to the transfer script):

```C:\Python38>python C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\data_management\hyp3_transfer_script.py```

The script will prompt you for:
- your Earthdata username and password
- the HyP3 project name for the data to copy
- the bucket name (i.e. ```hyp3-nasa-disasters```)

No quotes are required around the parameter text entries. 

The script will copy over the VV.tif, VH.tif, rgb.tif and VV.xml files, tagging each file with a prefix matching the project name. 

The script will only copy over data that is not already in the bucket, so you can add additional products to a project name and rerun the script to add the new products to the destination bucket.

