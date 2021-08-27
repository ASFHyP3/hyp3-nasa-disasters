import datetime
import os

import arcpy
import boto3

arcpy.env.overwriteOutput = True

# source_mds: full path to source mosaic dataset which will reference all images in the S3 bucket
source_mds = r"C:\Users\rob10341\OneDrive - Esri\RPR_ESRI_Projects\NASA\NASA_scripting\NASA_scripting.gdb\image_management_testing_nasa_working_source"

# derived_mds: full path to derived mosaic dataset which will hold the rasters from the source mosaic dataset after date
# selection with overviews (crf)
derived_mds = r"C:\Users\rob10341\OneDrive - Esri\RPR_ESRI_Projects\NASA\NASA_scripting\NASA_scripting.gdb\image_management_testing_nasa_working_derived"

# reference_mds: full path to reference mosaic dataset which will be used for the image services (can be further
# selected for date)
reference_mds = r"C:\Users\rob10341\OneDrive - Esri\RPR_ESRI_Projects\NASA\NASA_scripting\NASA_scripting.gdb\image_management_testing_nasa_working_referenced"

# acs_path: full path to the cloud connection file (.acs)
acs_path = r"C:\Image_Mgmt_Workflows\NASA_hyp3-nasa-disasters.acs"

# s3_bucket: S3 bucket name
s3_bucket = "hyp3-nasa-disasters"

# s3 dir: directory structure after s3 bucket
s3_dir = "RTC_services"

# aws_access_key_id: aws access key
aws_access_key_id = ""

# aws_secret_access_key: aws secret key
aws_secret_access_key = ""

# directory of log files
log_dir = r"C:\Users\rob10341\OneDrive - Esri\RPR_ESRI_Projects\NASA\NASA_scripting"

# image_type_filter: image type filter used to select the type of imagery to be added to the mosaic datasets. This is
# necessary where different data sources are stored in the same bucket
# For example, both rbg and VV + VH are stored in the same bucket. *rgb* | *VV* | *VH* as * is used as a wildcard
image_type_filter = "*rgb*"

# time_period_days: number of days from the current day to maintain in the derived mosaic dataset
time_period_days = 31

# ovi_time_period_days: number of days from the current day to delete overviews in S3
ovi_time_period_days = 1


class Messager:
    # Email properties can either be provided at initialization or using sendEmailOnExit method
    def __init__(self):
        self.message_list = []

    def log(self, msg):
        print(msg)  # print messages out immediately
        self.message_list.append(msg)  # hold onto message to append to email body

    def save_to_txt(self, log_dir, message_list):
        txt = open(os.path.join(log_dir, "log_file_" + str(datetime.date.today()) + ".txt"), "w")
        for message in message_list:
            txt.write(str(message))
        txt.close()


class MosaicDataset:
    def __init__(self, mosaic_dataset, raster_type, input_path, log):
        self.mosaic_dataset = mosaic_dataset
        self.raster_type = raster_type
        self.input_path = input_path
        self.log = log

    def add_rasters_to_mosaic_dataset(self, **kwargs):
        # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/add-rasters-to-mosaic-dataset.htm
        arcpy.management.AddRastersToMosaicDataset(in_mosaic_dataset=self.mosaic_dataset,
                                                   raster_type=self.raster_type,
                                                   input_path=self.input_path,
                                                   **kwargs)
        # arcpy.AddMessage("Added raster files in {0} to {1} mosaic dataset".format(self.input_path, self.mosaic_dataset))
        self.log("\n\nAdded raster files in {0} to {1} mosaic dataset".format(self.input_path, self.mosaic_dataset))

    def build_boundary_mosaic_dataset(self, **kwargs):
        # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/build-boundary.htm
        arcpy.management.BuildBoundary(in_mosaic_dataset=self.mosaic_dataset, **kwargs)
        # arcpy.AddMessage("Built boundary for mosaic dataset {0}".format(self.mosaic_dataset))
        self.log("\n\nBuilt boundary for mosaic dataset {0}".format(self.mosaic_dataset))

    def calculate_fields_with_selection(self, where_clause=None, **kwargs):
        # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/calculate-fields.htm
        if where_clause:
            selection = arcpy.management.SelectLayerByAttribute(self.mosaic_dataset, "NEW_SELECTION", where_clause)
            arcpy.management.CalculateFields(in_table=selection, **kwargs)
        else:
            arcpy.management.CalculateFields(in_table=self.mosaic_dataset, **kwargs)
        # arcpy.AddMessage("Calculated field(s) for mosaic dataset: {0}".format(self.mosaic_dataset))
        self.log("\n\nCalculated field(s) for mosaic dataset: {0}".format(self.mosaic_dataset))

    def remove_rasters_from_mosaic_dataset(self, **kwargs):
        # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/remove-rasters-from-mosaic-dataset.htm
        arcpy.management.RemoveRastersFromMosaicDataset(in_mosaic_dataset=self.mosaic_dataset, **kwargs)
        # arcpy.AddMessage("Removed rasters from mosaic dataset {0}".format(self.mosaic_dataset))
        self.log("\n\nRemoved rasters from mosaic dataset {0}".format(self.mosaic_dataset))


class Raster:
    def __init__(self, in_raster, out_rasterdataset, log):
        self.in_raster = in_raster
        self.out_rasterdataset = out_rasterdataset
        self.log = log

    def copy_raster(self, **kwargs):
        # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/copy-raster.htm
        arcpy.management.CopyRaster(in_raster=self.in_raster, out_rasterdataset=self.out_rasterdataset, **kwargs)
        # arcpy.AddMessage("Copied raster {0} to {1} ".format(self.in_raster, self.out_rasterdataset))
        self.log("\n\nCopied raster {0} to {1} ".format(self.in_raster, self.out_rasterdataset))


class S3Object:
    def __init__(self, s3_bucket, s3_dir, aws_access_key_id, aws_secret_access_key, time_period_days,
                 ovi_time_period_days, log):
        self.s3_bucket = s3_bucket
        self.s3_dir = s3_dir
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.time_period_days = time_period_days
        self.ovi_time_period_days = ovi_time_period_days
        self.s3 = boto3.client('s3', aws_access_key_id=self.aws_access_key_id,
                               aws_secret_access_key=self.aws_secret_access_key)
        self.log = log

    def delete_s3_object_by_date(self):
        raster_del_list = []
        for obj in self.s3.list_objects(Bucket=self.s3_bucket, Prefix=self.s3_dir, Delimiter='')['Contents']:
            s3_obj_key = obj['Key']
            if ("tif" in s3_obj_key) and (
                    datetime.datetime.today() - datetime.datetime.strptime(s3_obj_key.split("/")[-1].split("_")[2][0:8],
                                                                           "%Y%m%d")).days >= self.time_period_days:
                print(s3_obj_key)
                raster_del_list.append(s3_obj_key)
                # s3.delete_object(Bucket=s3_bucket, Key=s3_obj_key)
            elif ("crf" in s3_obj_key) and ("_alllayers" in s3_obj_key) and (
                    datetime.datetime.today() - datetime.datetime.strptime(
                    s3_obj_key.split("/")[1].replace(".crf", "").replace("Ovi", "").replace("_", ""),
                    "%Y%m%d")).days >= self.ovi_time_period_days:
                print(s3_obj_key)
                raster_del_list.append(s3_obj_key)
                # s3.delete_object(Bucket=s3_bucket, Key=s3_obj_key)
            elif ("crf" in s3_obj_key) and ("conf" in s3_obj_key) and (
                    datetime.datetime.today() - datetime.datetime.strptime(
                    s3_obj_key.split("/")[1].replace(".crf", "").replace("Ovi", "").replace("_", ""),
                    "%Y%m%d")).days >= self.ovi_time_period_days:
                print(s3_obj_key)
                raster_del_list.append(s3_obj_key)
                # s3.delete_object(Bucket=s3_bucket, Key=s3_obj_key)
        return raster_del_list


def main():
    # acs_path_s3: will update automatically to combine the acs_path and s3_bucket
    acs_path_s3 = os.path.join(acs_path, s3_dir)
    # overview_crf: will update automatically to create a crf file through the acs named Ovi_
    overview_crf = os.path.join(acs_path_s3, "Ovi_" + str(datetime.date.today()).replace("-", "_") + ".crf")
    # sql_statement: sql statement to select rows with empty StartDate (newly added rasters)
    sql_statement = "StartDate IS NULL"
    # date_sel: select a date that is less than or equal to the specified date range
    date_sel = 'StartDate <= timestamp ' + "'" + str(
        (datetime.datetime.today() - datetime.timedelta(days=time_period_days)).strftime("%Y-%m-%d %I:%M:%S")) + "'"
    # ovi_sel: select the overview files
    ovi_sel = "Name LIKE '%Ovi%'"

    # Log Messages
    log_messages = Messager()
    # Open auto ingestion script with time stamp
    log_messages.log("\n\nStarting auto ingestion script at: " + str(datetime.datetime.now()))

    # Add raster files and calculate the fields for the source mosaic dataset
    manage_source = MosaicDataset(source_mds, "Raster Dataset", acs_path_s3, log_messages.log)
    manage_source.add_rasters_to_mosaic_dataset(
        update_cellsize_ranges="",
        update_boundary="UPDATE_BOUNDARY",
        update_overviews="NO_OVERVIEWS",
        filter=image_type_filter,
        duplicate_items_action="EXCLUDE_DUPLICATES",
    )
    manage_source.calculate_fields_with_selection(
        where_clause=sql_statement,
        fields=[
            ["StartDate",
             '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" + !Name!.split("_")[2][:4] + " " + '
             '!Name!.split("_")[2][9:11] + ":" + !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
            ["EndDate",
             '!Name!.split("_")[2][4:6] + "/" + !Name!.split("_")[2][6:8] + "/" + !Name!.split("_")[2][:4] + " " + '
             '!Name!.split("_")[2][9:11] + ":" + !Name!.split("_")[2][11:13] + ":" + !Name!.split("_")[2][13:15]'],
            ["GroupName", '!Name!.split(";")[0][:-4]'],
            ["Tag", '!Name!.split("_")[8]'],
        ],
    )

    # Add new raster files and remove outdated raster files from the derived mosaic dataset
    manage_derived = MosaicDataset(derived_mds, "Table / Raster Catalog", source_mds, log_messages.log)
    manage_derived.add_rasters_to_mosaic_dataset(
        update_cellsize_ranges="",
        update_boundary="UPDATE_BOUNDARY",
        update_overviews="NO_OVERVIEWS",
        duplicate_items_action="EXCLUDE_DUPLICATES",
    )
    manage_derived.remove_rasters_from_mosaic_dataset(where_clause=date_sel, update_boundary="UPDATE_BOUNDARY")

    # Create overview file for the derived mosaic dataset
    manage_derived_create_ovi = Raster(derived_mds, overview_crf, log_messages.log)
    manage_derived_create_ovi.copy_raster()

    # Add overview file to derived mosaic dataset and calculate fields
    manage_derived = MosaicDataset(derived_mds, "Raster Dataset", overview_crf, log_messages.log)
    manage_derived.add_rasters_to_mosaic_dataset(
        update_cellsize_ranges="",
        update_boundary="UPDATE_BOUNDARY",
        update_overviews="NO_OVERVIEWS",
    )

    manage_derived.calculate_fields_with_selection(
        where_clause=ovi_sel,
        fields=[
            ["MaxPS", '1610'],
            ["StartDate", '!Name!.split("_")[2] + "/" + !Name!.split("_")[3] + "/" + !Name!.split("_")[1]'],
        ],
    )

    # Build the boundary file for the reference mosaic dataset
    manage_reference = MosaicDataset(reference_mds, "", "", log_messages.log)
    manage_reference.build_boundary_mosaic_dataset()

    # Delete outdated raster files in S3
    # del_s3 = S3Object(s3_bucket, s3_dir, aws_access_key_id, aws_secret_access_key, time_period_days,
    #                   ovi_time_period_days, log_messages.log)
    # del_s3.delete_s3_object_by_date()

    # Close auto ingestion script with time stamp
    log_messages.log("\n\nClosing auto ingestion script at: " + str(datetime.datetime.now()))

    # Save message log to a txt file
    Messager.save_to_txt(log_dir, log_messages.message_list)


if __name__ == '__main__':
    main()
