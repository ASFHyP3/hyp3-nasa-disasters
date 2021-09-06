# arcpy.management.CreateCloudStorageConnectionFile('.', 'asj-hyp3-dev.acs', 'AMAZON', 'asj-hyp3-dev', region='us-west-2', config_options='AWS_NO_SIGN_REQUEST')

import argparse
import datetime
import logging
import os

import arcpy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

arcpy.env.overwriteOutput = True


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_mds',
                        help='full path to source mosaic dataset which will reference all images in the S3 bucket')
    parser.add_argument('derived_mds',
                        help='full path to derived mosaic dataset which will hold the rasters from the source mosaic '
                             'dataset after date')
    parser.add_argument('referenced_mds',
                        help='full path to referenced mosaic dataset which will be used for the image services (can be '
                             'further selected for date)')
    parser.add_argument('raster_path', help='full path to the input raster files')
    parser.add_argument('image_type_filter',
                        help='image type filter used to select the type of imagery to be added to the mosaic datasets. '
                             'This is necessary where different data sources  are stored in the same bucket For '
                             'example, both rbg and VV + VH are stored in the same bucket. *rgb* | *VV* | *VH* as * is '
                             'used as a wildcard')
    parser.add_argument('overview_location', help='location to store overview .crf file')
    parser.add_argument('--time-period-days', type=int, default=31,
                        help='number of days from the current day to maintain in the derived mosaic dataset')
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    log.info(f'Adding raster files and calculating the fields for {args.source_mds}')
    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=args.source_mds,
        raster_type='Raster Dataset',
        input_path=args.raster_path,
        update_cellsize_ranges='NO_CELL_SIZES',
        filter=args.image_type_filter,
        duplicate_items_action='EXCLUDE_DUPLICATES',
    )
    selection = arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=args.source_mds,
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

    log.info(f'Adding new raster files and removing outdated raster files from {args.derived_mds}')
    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=args.derived_mds,
        raster_type='Table / Raster Catalog',
        input_path=args.source_mds,
        update_cellsize_ranges='NO_CELL_SIZES',
        duplicate_items_action='EXCLUDE_DUPLICATES',
    )
    cutoff_date = datetime.datetime.today() - datetime.timedelta(days=args.time_period_days)
    date_sel = f"StartDate <= timestamp '{cutoff_date.strftime('%Y-%m-%d %I:%M:%S')}'"
    arcpy.management.RemoveRastersFromMosaicDataset(in_mosaic_dataset=args.derived_mds, where_clause=date_sel)

    log.info(f'Creating overview file for {args.derived_mds}')
    with arcpy.EnvManager(compression="'JPEG_YCbCr' 80", tileSize="5120 5120", pyramid="PYRAMIDS 3", cellSize=300):
        arcpy.management.CopyRaster(in_raster=args.derived_mds, out_rasterdataset=args.overview_location)

    log.info(f'Adding overview file to {args.derived_mds} and calculating fields')
    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=args.derived_mds,
        raster_type='Raster Dataset',
        input_path=args.overview_location,
        update_cellsize_ranges='NO_CELL_SIZES',
    )
    selection = arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=args.derived_mds,
        selection_type='NEW_SELECTION',
        where_clause="Name LIKE '%Ovi%'",
    )
    arcpy.management.CalculateFields(
        in_table=selection,
        fields=[
            ['StartDate', '!Name!.split("_")[2] + "/" + !Name!.split("_")[3] + "/" + !Name!.split("_")[1]'],  # FIXME 8 hours before earliest raster
            ['EndDate', '!Name!.split("_")[2] + "/" + !Name!.split("_")[3] + "/" + !Name!.split("_")[1]'],  # FIXME 8 hours after latest raster
            ['MinPS', '1600'],
            ['Category', '2'],
            ['GroupName', 'Mosaic Overview'],  # TODO add date generated
        ],
    )

    log.info(f'Building the boundary file for {args.referenced_mds}')
    arcpy.management.BuildBoundary(in_mosaic_dataset=args.referenced_mds)

    log.info('Finished')


if __name__ == '__main__':
    main()
