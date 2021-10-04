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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file', help='path to json config file')
    args = parser.parse_args()
    return args


def main(config):
    cutoff_date = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=config['time_period_in_days'])
    crf_name = 'Ovi_' + str(datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')) + '.crf'

    for dataset in config['datasets']:

        log.info(f'Updating {dataset["source_mosaic"]}')
        arcpy.management.RemoveRastersFromMosaicDataset(in_mosaic_dataset=dataset['source_mosaic'],
                                                        where_clause='OBJECTID>=0')
        arcpy.management.AddRastersToMosaicDataset(
            in_mosaic_dataset=dataset['source_mosaic'],
            raster_type='Raster Dataset',
            input_path=dataset['raster_location'],
            update_cellsize_ranges='NO_CELL_SIZES',
            filter=dataset['raster_filter'],
        )
        arcpy.management.CalculateFields(
            in_table=dataset['source_mosaic'],
            fields=[
                ['StartDate', "datetime.datetime.strptime(!Name!.split('_')[2], '%Y%m%dT%H%M%S')"],
                ['EndDate', "datetime.datetime.strptime(!Name!.split('_')[2], '%Y%m%dT%H%M%S')"],
            ],
        )
        date_sel = f"StartDate <= timestamp '{cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}'"
        arcpy.management.RemoveRastersFromMosaicDataset(in_mosaic_dataset=dataset['source_mosaic'],
                                                        where_clause=date_sel)
        arcpy.management.CalculateFields(
            in_table=dataset['source_mosaic'],
            fields=[
                ['GroupName', '"_".join(!Name!.split(";")[0].split("_")[:-1])'],
                ['Tag', '!Name!.split("_")[8]'],
                ['MinPS', '0'],
                ['MaxPS', '1610'],
            ],
        )

        log.info(f'Creating overview crf file for {dataset["source_mosaic"]}')
        s3_crf_key = os.path.join(dataset['overview_location'], crf_name)
        with tempfile.TemporaryDirectory(dir=config['raster_store']) as temp_dir:
            local_crf = os.path.join(temp_dir, crf_name)
            with arcpy.EnvManager(pyramid='PYRAMIDS 3', cellSize=900):
                arcpy.management.CopyRaster(in_raster=dataset['source_mosaic'], out_rasterdataset=local_crf)
            subprocess.run(['aws', 's3', 'cp', local_crf, s3_crf_key.replace('/vsis3/', 's3://'), '--recursive'])

        log.info(f'Adding overview file to {dataset["source_mosaic"]}')
        arcpy.management.AddRastersToMosaicDataset(
            in_mosaic_dataset=dataset['source_mosaic'],
            raster_type='Raster Dataset',
            input_path=s3_crf_key,
            update_cellsize_ranges='NO_CELL_SIZES',
        )
        selection = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=dataset['source_mosaic'],
            selection_type='NEW_SELECTION',
            where_clause="Name LIKE 'Ovi_%'",
        )
        arcpy.management.CalculateFields(
            in_table=selection,
            fields=[
                ['StartDate', cutoff_date.strftime("'%m/%d/%Y %H:%M:%S'")],
                ['EndDate', 'datetime.datetime.now(tz=datetime.timezone.utc)'],
                ['MinPS', '1600'],
                ['MaxPS', '18000'],
                ['Category', '2'],
                ['GroupName', "'Mosaic Overview'"],
            ],
        )

        log.info(f'Updating {dataset["derived_mosaic"]}')
        arcpy.management.RemoveRastersFromMosaicDataset(in_mosaic_dataset=dataset['derived_mosaic'],
                                                        where_clause='OBJECTID>=0')
        arcpy.management.AddRastersToMosaicDataset(
            in_mosaic_dataset=dataset['derived_mosaic'],
            raster_type='Table / Raster Catalog',
            input_path=dataset['source_mosaic'],
            update_cellsize_ranges='NO_CELL_SIZES',
        )
        selection = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=dataset['derived_mosaic'],
            selection_type='NEW_SELECTION',
            where_clause="Name NOT LIKE 'Ovi_%'",
        )
        arcpy.management.CalculateFields(
            in_table=selection,
            fields=[
                ['MinPS', '0'],
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
