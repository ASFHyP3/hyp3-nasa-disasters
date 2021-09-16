import argparse
import datetime
import json
import logging
import os
import subprocess
import tempfile

import arcpy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

arcpy.env.overwriteOutput = True


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file', help='path to json config file')
    args = parser.parse_args()
    return args


def main(config):
    cutoff_date = datetime.datetime.today() - datetime.timedelta(days=config['time_period_in_days'])

    for dataset in config['datasets']:
        log.info(f'Adding raster files and calculating the fields for {dataset["source_mosaic"]}')
        arcpy.management.AddRastersToMosaicDataset(
            in_mosaic_dataset=dataset['source_mosaic'],
            raster_type='Raster Dataset',
            input_path=dataset['raster_location'],
            update_cellsize_ranges='NO_CELL_SIZES',
            filter=dataset['raster_filter'],
            duplicate_items_action='EXCLUDE_DUPLICATES',
        )
        selection = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=dataset['source_mosaic'],
            selection_type='NEW_SELECTION',
            where_clause='StartDate IS NULL',
        )
        arcpy.management.CalculateFields(
            in_table=selection,
            fields=[
                ['StartDate',
                 '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" + !Name!.split("_")[2][:4] + " " + '
                 '!Name!.split("_")[2][9:11] + ":" + !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
                ['EndDate',
                 '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" + !Name!.split("_")[2][:4] + " " + '
                 '!Name!.split("_")[2][9:11] + ":" + !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
                ['GroupName', '!Name!.split(";")[0][:-4]'],
                ['Tag', '!Name!.split("_")[8]'],
                ['MaxPS', '1610'],
            ],
        )

        log.info(f'Adding new raster files and removing outdated raster files from {dataset["derived_mosaic"]}')
        arcpy.management.AddRastersToMosaicDataset(
            in_mosaic_dataset=dataset['derived_mosaic'],
            raster_type='Table / Raster Catalog',
            input_path=dataset['source_mosaic'],
            update_cellsize_ranges='NO_CELL_SIZES',
            duplicate_items_action='EXCLUDE_DUPLICATES',
        )
        date_sel = f"StartDate <= timestamp '{cutoff_date.strftime('%Y-%m-%d %I:%M:%S')}'"
        arcpy.management.RemoveRastersFromMosaicDataset(in_mosaic_dataset=dataset['derived_mosaic'], where_clause=date_sel)

        log.info(f'Creating overview file for {dataset["derived_mosaic"]}')
        crf_name = 'Ovi_' + str(datetime.date.today()).replace('-', '_') + '.crf'
        s3_crf_key = os.path.join(dataset['overview_location'], crf_name)
        with tempfile.TemporaryDirectory(dir=config['raster_store']) as temp_dir:
            local_crf = os.path.join(temp_dir, crf_name)
            with arcpy.EnvManager(compression="'JPEG_YCbCr' 80", tileSize="5120 5120", pyramid="PYRAMIDS 3", cellSize=300):
                arcpy.management.CopyRaster(in_raster=dataset['derived_mosaic'], out_rasterdataset=local_crf)
            subprocess.run(['aws', 's3', 'cp', local_crf, s3_crf_key.replace('/vsis3/', 's3://'), '--recursive'])

        log.info(f'Adding overview file to {dataset["derived_mosaic"]} and calculating fields')
        arcpy.management.AddRastersToMosaicDataset(
            in_mosaic_dataset=dataset['derived_mosaic'],
            raster_type='Raster Dataset',
            input_path=s3_crf_key,
            update_cellsize_ranges='NO_CELL_SIZES',
        )
        selection = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=dataset['derived_mosaic'],
            selection_type='NEW_SELECTION',
            where_clause="Name LIKE '%Ovi%'",
        )
        arcpy.management.CalculateFields(
            in_table=selection,
            fields=[
                ['StartDate', (cutoff_date - datetime.timedelta(days=1)).strftime("'%m/%d/%Y %H:%M:%S'")],
                ['EndDate', (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("'%m/%d/%Y %H:%M:%S'")],
                ['MinPS', '1600'],
                ['Category', '2'],
                #['GroupName', 'Mosaic Overview'],  # TODO add date generated
            ],
        )

        log.info(f'Building the boundary file for {dataset["referenced_mosaic"]}')
        arcpy.management.BuildBoundary(in_mosaic_dataset=dataset['referenced_mosaic'])

        log.info('Finished')


if __name__ == '__main__':
    args = get_args()
    with open(args.config_file) as f:
        config = json.load(f)
    main(config)
