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
    parser.add_argument('reference_mds',
                        help='full path to reference mosaic dataset which will be used for the image services (can be '
                             'further selected for date)')
    parser.add_argument('acs_path', help='full path to the cloud connection file (.acs)')
    parser.add_argument('image_type_filter',
                        help='image type filter used to select the type of imagery to be added to the mosaic datasets. '
                             'This is necessary where different data sources  are stored in the same bucket For '
                             'example, both rbg and VV + VH are stored in the same bucket. *rgb* | *VV* | *VH* as * is '
                             'used as a wildcard')
    parser.add_argument('s3_prefix', help='directory structure after s3 bucket')
    parser.add_argument('--time-period-days', type=int, default=31,
                        help='number of days from the current day to maintain in the derived mosaic dataset')
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    # acs_path_s3: will update automatically to combine the acs_path and s3_bucket
    acs_path_s3 = os.path.join(args.acs_path, args.s3_prefix)
    # overview_crf: will update automatically to create a crf file through the acs named Ovi_
    overview_crf = os.path.join(acs_path_s3, 'Ovi_' + str(datetime.date.today()).replace('-', '_') + '.crf')

    log.info('Adding raster files and calculating the fields for the source mosaic dataset')
    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=args.source_mds,
        raster_type='Raster Dataset',
        input_path=acs_path_s3,
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
        ],
    )

    log.info('Adding new raster files and removing outdated raster files from the derived mosaic dataset')
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

    log.info('Creating overview file for the derived mosaic dataset')
    with arcpy.EnvManager(pyramid="PYRAMIDS 3"):
        arcpy.management.CopyRaster(in_raster=args.derived_mds, out_rasterdataset=overview_crf)

    log.info('Adding overview file to derived mosaic dataset and calculating fields')
    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=args.derived_mds,
        raster_type='Raster Dataset',
        input_path=overview_crf,
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
            ['MaxPS', '1610'],
            ['StartDate', '!Name!.split("_")[2] + "/" + !Name!.split("_")[3] + "/" + !Name!.split("_")[1]'],
        ],
    )

    log.info('Building the boundary file for the reference mosaic dataset')
    arcpy.management.BuildBoundary(in_mosaic_dataset=args.reference_mds)

    log.info('Finished')


if __name__ == '__main__':
    main()
