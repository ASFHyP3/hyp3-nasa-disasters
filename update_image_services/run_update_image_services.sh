#!/bin/bash

# wrapper script to run update_image_services.py via a cron schedule
# some arcpy commands require the python session to be tied to a terminal, so the crontab should look like:
# 0 0 * * * script -qef -a /home/arcgis/update_image_services.log  -c /home/arcgis/hyp3-nasa-disasters/update_image_services/run_update_image_services.sh

set -e
source /home/arcgis/miniconda3/etc/profile.d/conda.sh
conda activate arcpy
python /home/arcgis/hyp3-nasa-disasters/update_image_services/update_image_services.py /home/arcgis/hyp3-nasa-disasters/update_image_services/config.json
