# ------------------------------------------------------------------------------
# Copyright 2013 Esri
# Modifications Copyright 2021 Alaska Satellite Facility
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
# Name: MDCS_UC.py
# Description: A class to implement all user functions or to extend the built in MDCS functions/commands chain.
# Version: 20201230
# Requirements: ArcGIS 10.1 SP1
# Author: Esri Imagery Workflows team
# ------------------------------------------------------------------------------
#!/usr/bin/env python
import os
import sys
import arcpy


class UserCode:

    def __init__(self):
        pass    # initialize variables that need to be shared between multiple user commands.

    def sample00(self, data):
        base = data['base']
        # using Base class for its XML specific common functions. (getXMLXPathValue, getXMLNodeValue, getXMLNode)
        xmlDOM = data['mdcs']
        # access to MDCS config file
        command_used = base.getXMLNodeValue(xmlDOM, 'Command')
        workspace = data['workspace']
        md = data['mosaicdataset']
        log = data['log']
        log.Message('%s\\%s' % (workspace, md), 0)
        return True

    def sample01(self, data):
        log = data['log']           # How to use logging within the user function.
        log.Message('hello world', 0)
        return True

    def sample02(self, data):
        log = data['log']           # How to use logging within the user function.
        log.Message('Returning multiple values', 0)
        data['useResponse'] = True
        data['response'] = ['msg0', 'msg1', 'msg2']
        data['status'] = True   # overall function status
        return True
        # True must be returned if data['useResponse'] is required.
        # data['response'] can be used to return multiple values.

    def customCV(self, data):
        workspace = data['workspace']
        md = data['mosaicdataset']
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.UpdateCursor(ds)
        if (ds_cursor is not None):
            print ('Calculating values..')
            row = ds_cursor.next()
            while(row is not None):
                row.setValue('MinPS', 0)
                row.setValue('MaxPS', 300)
                WRS_Path = row.getValue('WRS_Path')
                WRS_Row = row.getValue('WRS_Row')
                if (WRS_Path is not None and
                        WRS_Row is not None):
                    PR = (WRS_Path * 1000) + WRS_Row
                    row.setValue('PR', PR)
                AcquisitionData = row.getValue('AcquisitionDate')
                if (AcquisitionData is not None):
                    AcquisitionData = str(AcquisitionData).replace('-', '/')
                    day = int(AcquisitionData.split()[0].split('/')[1])
                    row.setValue('Month', day)
                grp_name = row.getValue('GroupName')
                if (grp_name is not None):
                    CMAX_INDEX = 16
                    if (len(grp_name) >= CMAX_INDEX):
                        row.setValue('DayOfYear', int(grp_name[13:CMAX_INDEX]))
                        row.setValue('Name', grp_name.split('_')[0] + '_' + row.getValue('Tag'))
                ds_cursor.updateRow(row)
                row = ds_cursor.next()
            del ds_cursor
        return True

    def UpdateTagField(self, data):
        workspace = data['workspace']
        md = data['mosaicdataset']
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.UpdateCursor(ds)
        if (ds_cursor is not None):
            print ('Updating Tag values..')
            row = ds_cursor.next()
            while(row is not None):
                tag = row.getValue('Tag')
                if (tag is not None):
                    row.setValue('Tag', 'VV,VH')
                ds_cursor.updateRow(row)
                row = ds_cursor.next()
            del ds_cursor
        return True

    def UpdateFieldsWM(self, data):
        log = data['log']
        xmlDOM = data['mdcs']
        base = data['base']
        workspace = data['workspace']
        md = data['mosaicdataset']
        s3name = base.getXMLNodeValue(xmlDOM, 's3tag')
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.da.UpdateCursor(ds, ["Name", "GroupName",
                                               "Tag", "MaxPS", "StartDate",
                                               "EndDate", "DownloadURL"])
        # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/updatecursor-class.htm
        if (ds_cursor is not None):
            log.Message('Updating Field Values..', 0)
            for row in ds_cursor:
                try:
                    NameField = row[0]
                    GroupField = NameField.split(";")[0][:-3]
                    TagField = NameField.split("_")[8]
                    MaxPSField = 1610
                    StartDateField = (NameField.split("_")[2][4:6] + "/" + NameField.split("_")[2][6:8] + "/" +
                                      NameField.split("_")[2][:4] + " " + NameField.split("_")[2][9:11] + ":" +
                                      NameField.split("_")[2][11:13] + ":" + NameField.split("_")[2][13:15])
                    EndDateField = (NameField.split("_")[2][4:6] + "/" + NameField.split("_")[2][6:8] + "/" +
                                    NameField.split("_")[2][:4] + " " + NameField.split("_")[2][9:11] + ":" +
                                    NameField.split("_")[2][11:13] + ":" + NameField.split("_")[2][13:15])
                    DownloadURLField = "https://s3-us-west-2.amazonaws.com/hyp3-nasa-disasters/" + str(s3name) + \
                                       str('/') + str(NameField) + ".tif"
                    row[1] = GroupField
                    row[2] = TagField
                    row[3] = MaxPSField
                    row[4] = StartDateField
                    row[5] = EndDateField
                    row[6] = DownloadURLField
                    ds_cursor.updateRow(row)
                    log.Message("{} updated".format(NameField), 0)
                except Exception as exp:
                    log.Message(str(exp), 2)
            del ds_cursor
        return True

    def UpdateFieldsRGB(self, data):
        log = data['log']
        xmlDOM = data['mdcs']
        base = data['base']
        workspace = data['workspace']
        md = data['mosaicdataset']
        s3name = base.getXMLNodeValue(xmlDOM, 's3tag')
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.da.UpdateCursor(ds, ["Name", "GroupName",
                                               "Tag", "MaxPS", "StartDate",
                                               "EndDate", "DownloadURL"])
        # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/updatecursor-class.htm
        if (ds_cursor is not None):
            log.Message('Updating Field Values..', 0)
            for row in ds_cursor:
                try:
                    NameField = row[0]
                    GroupField = NameField.split(";")[0][:-4]
                    TagField = NameField.split("_")[8]
                    MaxPSField = 1610
                    StartDateField = (NameField.split("_")[2][4:6] + "/" + NameField.split("_")[2][6:8] + "/" +
                                      NameField.split("_")[2][:4] + " " + NameField.split("_")[2][9:11] + ":" +
                                      NameField.split("_")[2][11:13] + ":" + NameField.split("_")[2][13:15])
                    EndDateField = (NameField.split("_")[2][4:6] + "/" + NameField.split("_")[2][6:8] + "/" +
                                    NameField.split("_")[2][:4] + " " + NameField.split("_")[2][9:11] + ":" +
                                    NameField.split("_")[2][11:13] + ":" + NameField.split("_")[2][13:15])
                    DownloadURLField = "https://s3-us-west-2.amazonaws.com/hyp3-nasa-disasters/" + str(s3name) + \
                                       str('/') + str(NameField) + ".tif"
                    row[1] = GroupField
                    row[2] = TagField
                    row[3] = MaxPSField
                    row[4] = StartDateField
                    row[5] = EndDateField
                    row[6] = DownloadURLField
                    ds_cursor.updateRow(row)
                    log.Message("{} updated".format(NameField), 0)
                except Exception as exp:
                    log.Message(str(exp), 2)
            del ds_cursor
        return True

    def UpdateFieldsRTC(self, data):
        log = data['log']
        workspace = data['workspace']
        md = data['mosaicdataset']
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.da.UpdateCursor(ds, ["Name", "GroupName", "Tag",
                                               "MaxPS", "StartDate", "EndDate"])
        # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/updatecursor-class.htm
        if (ds_cursor is not None):
            log.Message('Updating Field Values..', 0)
            for row in ds_cursor:
                try:
                    NameField = row[0]
                    GroupField = NameField.split(";")[0][:-3]
                    TagField = NameField.split("_")[8]
                    MaxPSField = 1610
                    StartDateField = (NameField.split("_")[2][4:6] + "/" + NameField.split("_")[2][6:8] + "/" +
                                      NameField.split("_")[2][:4] + " " + NameField.split("_")[2][9:11] + ":" +
                                      NameField.split("_")[2][11:13] + ":" + NameField.split("_")[2][13:15])
                    EndDateField = (NameField.split("_")[2][4:6] + "/" + NameField.split("_")[2][6:8] + "/" +
                                    NameField.split("_")[2][:4] + " " + NameField.split("_")[2][9:11] + ":" +
                                    NameField.split("_")[2][11:13] + ":" + NameField.split("_")[2][13:15])
                    row[1] = GroupField
                    row[2] = TagField
                    row[3] = MaxPSField
                    row[4] = StartDateField
                    row[5] = EndDateField
                    ds_cursor.updateRow(row)
                    log.Message("{} updated".format(NameField), 0)
                except Exception as exp:
                    log.Message(str(exp), 2)
            del ds_cursor
        return True

    def UpdateNameFieldRTC(self, data):
        log = data['log']
        xmlDOM = data['mdcs']
        base = data['base']
        workspace = data['workspace']
        md = data['mosaicdataset']
        s3name = base.getXMLNodeValue(xmlDOM, 's3tag')
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.da.UpdateCursor(ds, ["Name", "GroupName", "Tag", "MaxPS",
                                               "DownloadURL_VV", "DownloadURL_VH"])
        # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/updatecursor-class.htm
        if (ds_cursor is not None):
            log.Message('Updating Field Values..', 0)
            for row in ds_cursor:
                try:
                    ## NameField = row[0]
                    GroupField = row[1]
                    TagField = row[2]
                    if (TagField is not None):
                        TagField = "VV,VH"
                    ## lstNameField = NameField.split(';')
                    lstTagField = TagField.split(',')
                    newNameField = GroupField + "_" + lstTagField[0] + ';' + GroupField + "_" + lstTagField[1]
                    row[0] = newNameField
                    row[2] = TagField
                    row[3] = 1610
                    row[4] = "https://s3-us-west-2.amazonaws.com/hyp3-nasa-disasters/" + str(s3name) + str('/') + str(
                        GroupField) + "_VV.tif"
                    row[5] = "https://s3-us-west-2.amazonaws.com/hyp3-nasa-disasters/" + str(s3name) + str('/') + str(
                        GroupField) + "_VH.tif"
                    ds_cursor.updateRow(row)
                    log.Message("{} updated".format(newNameField), 0)
                except Exception as exp:
                    log.Message(str(exp), 2)
            del ds_cursor
        return True

    def UpdateOverviewFields(self, data):
        import datetime
        log = data['log']
        workspace = data['workspace']
        md = data['mosaicdataset']
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.da.UpdateCursor(ds, ["Tag", "StartDate"])
        stdatelist = []
        if (ds_cursor is not None):
            log.Message('Determining Start and End Dates...', 0)
            # Determine the range of dates in the mosaic dataset
            for row in ds_cursor:
                if row[0] != 'Dataset':
                    stdatelist.append(row[1])
            stdate = min(stdatelist)
            endate = max(stdatelist)
            del ds_cursor
        ds_cursor = arcpy.da.UpdateCursor(ds, ["Tag", "MinPS", "Category", "StartDate", "EndDate", "GroupName"])
        if (ds_cursor is not None):
            log.Message('Updating Overview Field Values...', 0)
            # Populate appropriate fields in the overview row of the attribute table
            for row in ds_cursor:
                try:
                    if row[0] == 'Dataset':
                        row[1] = 1600
                        row[2] = 2
                        #row[3] = datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S')
                        row[3] = stdate + datetime.timedelta(hours=-8)
                        row[4] = endate + datetime.timedelta(hours=8)
                        row[5] = "Mosaic Overview"
                        ds_cursor.updateRow(row)
                        log.Message("Overview fields updated.", 0)
                except Exception as exp:
                    log.Message(str(exp), 2)
            del ds_cursor
        return True

    def UpdateFieldsCoh(self, data):
        log = data['log']
        workspace = data['workspace']
        md = data['mosaicdataset']
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.da.UpdateCursor(ds, ["Name", "ProductType", "Season", "Polarization", "Tile", "Dataset_ID",
                                               "Tag", "MaxPS", "StartDate", "EndDate", "GroupName", "DownloadURL",
                                               "URLDisplay"])
        # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/updatecursor-class.htm
        if (ds_cursor is not None):
            log.Message('Updating Field Values..', 0)
            for row in ds_cursor:
                try:
                    NameField = row[0]
                    ProductTypeField = NameField.split("_")[3]
                    SeasonName = NameField.split("_")[1]
                    if SeasonName == 'summer':
                        SeasonCode = 'JJA'
                        SeasonField = 'June/July/August'
                        StartDateField = '06/01/2020'
                        EndDateField = '08/31/2020'
                    elif SeasonName == 'fall':
                        SeasonCode = 'SON'
                        SeasonField = 'September/October/November'
                        StartDateField = '09/01/2020'
                        EndDateField = '11/30/2020'
                    elif SeasonName == 'winter':
                        SeasonCode = 'DJF'
                        SeasonField = 'December/January/February'
                        StartDateField = '12/01/2019'
                        EndDateField = '02/29/2020'
                    elif SeasonName == 'spring':
                        SeasonCode = 'MAM'
                        SeasonField = 'March/April/May'
                        StartDateField = '03/01/2020'
                        EndDateField = '05/31/2020'
                    else:
                        SeasonField = 'unknown'
                    PolarizationField = str(NameField.split("_")[2]).upper()
                    TileField = NameField.split("_")[0]
                    DatasetIDField = ProductTypeField+'_'+PolarizationField+'_'+SeasonCode
                    TagField = DatasetIDField
                    MaxPSField = 310
                    GroupNameField = DatasetIDField
                    DownloadURLField = r'https://sentinel-1-global-coherence-earthbigdata.s3.us-west-' \
                                       r'2.amazonaws.com/data/tiles/{}/{}.tif'.format(TileField, NameField)
                    row[1] = ProductTypeField
                    row[2] = SeasonField
                    row[3] = PolarizationField
                    row[4] = TileField
                    row[5] = DatasetIDField
                    row[6] = TagField
                    row[7] = MaxPSField
                    row[8] = StartDateField
                    row[9] = EndDateField
                    row[10] = GroupNameField
                    row[11] = DownloadURLField
                    row[12] = NameField
                    ds_cursor.updateRow(row)
                    log.Message("{} updated".format(NameField), 0)
                except Exception as exp:
                    log.Message(str(exp), 2)
            del ds_cursor
        return True

    def UpdateCohOverviewFields(self, data):
        import datetime
        log = data['log']
        workspace = data['workspace']
        md = data['mosaicdataset']
        ds = os.path.join(workspace, md)
        ds_cursor = arcpy.da.UpdateCursor(ds, ["Tag", "MinPS", "Category", "StartDate", "EndDate", "GroupName",
                                               "Name", "ProductType", "Season", "Polarization", "Tile", "DownloadURL",
                                               "URLDisplay"])
        if (ds_cursor is not None):
            log.Message('Updating Overview Field Values...', 0)
            # Populate appropriate fields in the overview row of the attribute table
            for row in ds_cursor:
                try:
                    NameOvField = row[6]
                    ProdTypeOvField = NameOvField.split("_")[1]
                    SeasonOvCode = NameOvField.split("_")[3]
                    if SeasonOvCode == 'DJF':
                        SeasonOvField = 'December/January/February'
                    elif SeasonOvCode == 'MAM':
                        SeasonOvField = 'March/April/May'
                    elif SeasonOvCode == 'JJA':
                        SeasonOvField = 'June/July/August'
                    elif SeasonOvCode == 'SON':
                        SeasonOvField = 'September/October/November'
                    else:
                        SeasonOvField = 'unknown'
                    PolOvField = NameOvField.split("_")[2]
                    TileOvField = 'Zoom in to see specific tile information'
                    DLOvField = 'Zoom in to source raster level to download datasets'
                    if row[0] == 'Dataset':
                        row[1] = 300
                        row[2] = 2
                        row[3] = '12/01/2019'
                        row[4] = '11/30/2020'
                        row[5] = "Mosaic Overview"
                        row[7] = ProdTypeOvField
                        row[8] = SeasonOvField
                        row[9] = PolOvField
                        row[10] = TileOvField
                        row[11] = DLOvField
                        row[12] = DLOvField
                        ds_cursor.updateRow(row)
                        log.Message("Overview fields updated.", 0)
                except Exception as exp:
                    log.Message(str(exp), 2)
            del ds_cursor
        return True
