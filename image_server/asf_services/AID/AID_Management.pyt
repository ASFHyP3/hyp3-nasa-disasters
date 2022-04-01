# Copyright 2019 Esri
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
# Name: AID_Management.pyt
# Description: GPTools to create pod, check job status, create, delete, update, start/stop image services
# Version: 1.0
# Date Created : 20210209
# Date updated : 20210209
# Requirements: ArcGIS Pro 2.5
# Author: Esri Imagery Workflows team
# ------------------------------------------------------------------------------

import os
import sys
import time
import json
import subprocess
import requests
import re
from distutils.dir_util import copy_tree
import shutil
import tempfile
import zipfile
import cis_utils as utils
import datetime
import arcpy
from arcgis.gis import GIS
from SolutionsLog.logger import Logger

CLOUD_PATH_PREFIXES = ('/vsis3', '/vsicurl', '/vsiaz')
CACHED_PROFILES_FOLDER_NAME = '{}_profiles'
DEFAULT_WAIT_TIME = 4
CREATE_WAIT_TIME = 34
DELETE_WAIT_TIME = 14
TILE_PACKAGE_EXTENSIONS = ('.slpk', '.tpkx')


def initializeLog(toolName):
    log = Logger()
    root_folder = os.path.dirname(__file__)
    log_output_folder = os.path.join(root_folder, 'logs')
    log.SetLogFolder(log_output_folder)
    log.Project(toolName)
    log.LogNamePrefix(toolName)
    log.StartLog()
    return log


def closeLog(log):
    log.Message("Done", log.const_general_text)
    log.WriteLog('#all')

def mrfstring(mpath):
    try:
        mrfp = open(mpath, 'r').readlines()
        for n,line in enumerate(mrfp):
            mrfp[n] = (line.rstrip()).lstrip()

        str_mrf = (''.join(mrfp))
        return str_mrf
    except Exception as e:
        print (str(e))
        return False

def get_data_type(data_path):
    in_data_prop ={}
    in_data_prop['type'] = ''
    in_data_prop['name'] = ''
    in_data_prop['wks'] = ''
    in_data_prop['wks_type'] = ''
    in_data_prop['wks_name'] = ''
    in_data_prop['wks_name_noext'] = ''
    in_data_prop['acsfilepath'] =''
    in_data_prop['dtype'] = ''
    in_data_prop['format'] = ''

    try:
        if data_path.startswith(CLOUD_PATH_PREFIXES):
            in_data_prop['type'] = 'cloudraster'
            in_data_prop['name'] = "cl_" + os.path.basename(data_path)[:-4]
            in_data_prop['dtype'] = 'raster'
            return in_data_prop
        data_describe = arcpy.Describe(data_path)
        if data_describe.datatype == 'MosaicDataset':
            in_data_prop['dtype'] = 'mosaic'
            in_data_prop['type'] = 'mosaic'
            in_data_prop['name'] = data_describe.Name
            in_data_prop['wks'] = data_describe.path
            wks_info = arcpy.Describe(data_describe.path)
            if (wks_info.workspaceFactoryProgID == 'esriDataSourcesGDB.FileGDBWorkspaceFactory'):
                in_data_prop['wks_type'] = 'fgdb'
                in_data_prop['wks_name_noext'] = wks_info.name[:-4]
            elif(wks_info.workspaceFactoryProgID == ''):
                in_data_prop['wks_type'] = 'folder'
            else:
                in_data_prop['wks_type'] = 'unknown'
            in_data_prop['wks_name'] = wks_info.name
            return in_data_prop
        else:
            in_data_prop['dtype'] = 'raster'
            r_test = arcpy.Raster(data_path,True)
            in_data_prop['format'] = r_test.format
            in_data_prop['name']=r_test.name
#            data_describe_raster = arcpy.Describe(r_test)
            if data_describe.datatype == 'RasterDataset':
                in_data_prop['type'] = 'raster'
                in_data_prop['wks'] = data_describe.path
                in_data_prop['wks_name_noext'] = 'rd_' + str(os.path.basename(data_describe.path))
                if '.acs' in data_path:
                    in_data_prop['wks_type'] = 'cloudfolder'
                    acspath = data_path.split('.acs')[0] + '.acs'
                    if (os.path.isfile(acspath)):
                        in_data_prop['acsfilepath'] = acspath
                        in_data_prop['type'] = 'cloudraster'

                else:
                    in_data_prop['wks_type'] = 'folder'


            return in_data_prop
    except:
        in_data_prop['type'] = 'mosaic'
        in_data_prop['dtype'] = 'mosaic'
        return in_data_prop

def copy_mosaic(input_data,gdb_name,unzipped_folder_path,data_name,log):

    try:
        arcpy.CreateFileGDB_management(unzipped_folder_path, gdb_name)
    except Exception as e:
        arcpy.AddError("Error in creating gdb at output location.")
        log.Message("Error in creating gdb at output location.{}".format(str(e)),
                    log.const_critical_text)
        return False
    try:
        arcpy.Copy_management(input_data,
                              os.path.join(unzipped_folder_path,
                                           gdb_name,
                                           data_name))
    except Exception as e:
        arcpy.AddError("Error in copying mosaic to output location.")
        log.Message("Error in copying mosaic to output location.{}".format(str(e)),
                    log.const_critical_text)
        return False
    return True

def get_all_file_paths(directory):
    abs_src = os.path.abspath(directory)
    file_paths = []

    for root, directories, files in os.walk(directory):
        for filename in files:
            if ('.sr.lock' in filename):
                continue
            absname = os.path.abspath(os.path.join(root, filename))
            arcname = absname[len(abs_src) + 1:]
            file_paths.append({'absname': absname, 'arcname': arcname})

    return file_paths


def delete_exported_mosaic_json(input_data):
    try:
        tempfolder = tempfile.gettempdir()
        mosaic_json = None
        mosaic_name = os.path.basename(input_data)
        mosaic_json_path = os.path.join(tempfolder,
                                        '{}.txt'.format(mosaic_name))
        os.remove(mosaic_json_path)
    except Exception as e:
        pass


def get_mosaic_json(input_data):
    try:
        message = {}
        success = True
        tempfolder = tempfile.gettempdir()
        mosaic_json = None
        mosaic_name = os.path.basename(input_data)
        mosaic_json_path = os.path.join(tempfolder,
                                        '{}.json'.format(mosaic_name))
        try:
            arcpy.gp.command('ExportMosaicDataset {} json {} --formatJSON'.format(
                input_data, mosaic_json_path))
        except Exception as e:
            message = "Could not export mosaic dataset {}".format(str(e))
            success = False
        try:
            with open(mosaic_json_path) as f:
                mosaic_json = json.load(f)
        except Exception as e:
            message = "Could not load mosaic json. {}".format(str(e))
            success = False
        return {'success': success, 'message': message,
                'mosaic_json': mosaic_json}
    except Exception as e:
        return {'success': False,
                'message': 'Error in export mosaic:{}'.format(str(e)),
                'mosaic_json': None}


def get_paths_from_raster_node(raster_node):
    paths = []
    arguments = raster_node.get('arguments')
    if arguments:
        if type(arguments) == dict:
            if arguments.get('Raster'):
                paths.extend(get_paths_from_raster_node(
                    arguments.get('Raster')))
        elif type(arguments) == list:
            for argument in arguments:
                paths.extend(get_paths_from_raster_node(argument))
    elif raster_node.get('name'):
        paths.append(raster_node['name'])
    return paths


def get_drive_letter(path):
    try:
        if path.startswith('<MRF_META>'):
            try:
                data_file_path = path.split('<DataFile>')[
                    1].split('</DataFile>')[0]
            except:
                data_file_path = ''
            if data_file_path and not data_file_path.startswith(
                ('z:\\mrfcache', 'z:/mrfcache')):
                data_file_path = data_file_path.replace('\\', '/')
                return data_file_path.split('/')[0]
    except Exception as e:
        return None


def get_all_raster_paths(mosaic_json):
    rasters = mosaic_json.get('Rasters')
    paths = []
    for raster in rasters:
        raster_node = raster.get('Raster')
        raster_paths = get_paths_from_raster_node(raster_node)
        paths.extend(raster_paths)
    return paths

def get_all_raster_paths_mdtools(input_data, log):
    try:
        md_tools_exe = os.path.join(arcpy.GetInstallInfo()['InstallDir'],'bin',
                                    'mdtools.exe')
        all_paths = []
        temp_dir = tempfile.gettempdir()
        cell_size = arcpy.management.GetRasterProperties(input_data, 'CELLSIZEX').getOutput(0)
        xmin = arcpy.management.GetRasterProperties(input_data, 'LEFT').getOutput(0)
        ymin = arcpy.management.GetRasterProperties(input_data, 'BOTTOM').getOutput(0)
        xmax = arcpy.management.GetRasterProperties(input_data, 'RIGHT').getOutput(0)
        ymax = arcpy.management.GetRasterProperties(input_data, 'TOP').getOutput(0)
        output_path = os.path.join(temp_dir,
                                   '{}.txt'.format(os.path.basename(input_data)))
        args = [md_tools_exe, '--export_paths',
                '--MD={}'.format(input_data),
                '--op={}'.format(output_path),
                '--cellsize={}'.format(cell_size),
                '--aoi={},{},{},{}'.format(xmin, ymin, xmax, ymax)]
        export_status = run_subprocess(args, log)
        if export_status:
            with open(output_path,'r') as output_clean:
                output_c = output_clean.read()
                output_c=((output_c.replace('>\n    <','><')).replace('>\n  <','><')).replace(">\n<",'><').replace("\n\n",('\n'))
                output_c=((output_c.replace('>\n\t\t<','><')).replace('>\n\t<','><')).replace(">\n<",'><').replace("\n\n",('\n'))
            with open(output_path,'w') as newoutput:
                newoutput.write(output_c)

            cursor = arcpy.SearchCursor(output_path)
            for row in cursor:
                all_paths.append(row.getValue('Path'))
            return all_paths
        else:
            log.Message("Export paths did not work..", log.const_critical_text)
            return []
    except Exception as e:
        log.Message("Could not extract paths using md tools {}".format(
            str(e)), log.const_critical_text)
        arcpy.AddError("Could not extract paths using md tools {}".format(
            str(e)))
        return []

def export_raster_paths(input_data, log):
    try:
        all_paths = []
        tempdir = tempfile.gettempdir()
        gdb_name = os.path.basename(input_data)
        gdb_path = os.path.join(tempdir, '{}.gdb'.format(gdb_name))
        try:
            arcpy.management.CreateFileGDB(tempdir, gdb_name)
        except Exception as e:
            pass
        table_path = os.path.join(gdb_path, 'mosaic_paths')
        arcpy.management.ExportMosaicDatasetPaths(input_data, table_path, None, "ALL", "RASTER")
        cursor = arcpy.SearchCursor(table_path)
        for row in cursor:
            all_paths.append(row.getValue('Path'))
        return all_paths
    except Exception as e:
        arcpy.AddError('Error in export raser paths:{}'.format(str(e)))
        log.Message('Error in export raser paths:{}'.format(str(e)),
                    log.const_critical_text)

def validate_path(path):
    try:
        if path.startswith('<MRF_META>'):
            try:
                source_path = path.split('<Source')[1].split('</Source>')[0]
                source_path = source_path.split('>')[1]
            except:
                message = 'Source path is invalid'
                return False, message
            if not source_path.startswith(CLOUD_PATH_PREFIXES):
                message = 'Source path should be on the cloud and should start with /vsis3 or /vsicurl or /vsiaz'
                return False, message
            try:
                data_file_path = path.split('<DataFile>')[
                    1].split('</DataFile>')[0]
            except:
                message = 'DataFile path is invalid'
                return False, message
            if not data_file_path.startswith(('z:\\mrfcache', 'z:/mrfcache')):
                message = 'DataFile path should start with z:/mrfcache'
                return False, message
        else:
            if not path.startswith(CLOUD_PATH_PREFIXES):
                message = 'Raster path should either be embedded or \
                           should be a cloud path.'
                return False, message
            else:
                if 'http' in path:
                    url = 'http{}'.format(path.split('http')[1])
                    response = requests.head(url)
                    if response.status_code != 200:
                        message = 'The URL is not accessible.'
                        return False, message
        return True, ''
    except Exception as e:
        return False, 'Error:{}'.format(str(e))


def run_subprocess(args, log):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        p = subprocess.Popen(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             startupinfo=startupinfo)
        stdout, stderr = p.communicate()
        if stderr:
            log.Message(stderr, log.const_critical_text)
            arcpy.AddError(stderr)
        success = False if p.returncode != 0 else True
        return success
    except Exception as e:
        arcpy.AddError("Error in running md tools {}: {}".format(
            str(args), str(e)))
        log.Message("Error in running md tools {}: {}".format(
            str(args), str(e)), log.const_critical_text)


def replace_paths(mosaic_path, oldpath, newpath, log):
    try:
        md_tools_exe = os.path.join(arcpy.GetInstallInfo()['InstallDir'], 'bin',
                                    'mdtools.exe')
        if os.path.exists(md_tools_exe):
            args = [md_tools_exe, '--replace_paths',
                    '--MD={}'.format(mosaic_path),
                    '--oldpath={}'.format(oldpath),
                    '--newpath={}'.format(newpath)]
            replace_status = run_subprocess(args, log)
            if not replace_status:
                log.Message("Error in replace paths", log.const_critical_text)
            else:
                log.Message("Replace paths success", log.const_general_text)
    except Exception as e:
        log.Message("Could not replace paths using md tools {}".format(
            str(e)), log.const_critical_text)
        arcpy.AddError("Could not replace paths using md tools {}".format(
            str(e)))


def add_portal_item(service_name, description, service_url, log,
                    service_type='Image Service',
                    service_type_name='ImageServer'):
    try:
        item = {
            "type": service_type,
            "title": service_name,
            "tags": ','.join([service_name, service_type_name]),
            "description": description,
            "url": service_url
        }
        gis = GIS("pro")
        added_item = gis.content.add(item)
        log.Message("Added item id : {}".format(added_item.id),
                    log.const_general_text)
        return added_item.id
    except Exception as e:
        log.Message("Error in adding item to the portal {}".format(str(e)),
                    log.const_critical_text)


def create_zip(input_data, output_folder, data_type, additional_properties,
               log):
    try:
        if input_data.startswith(CLOUD_PATH_PREFIXES):
            data_name = input_data
        elif '.acs' in input_data:
            data_name = input_data.split('.acs')[1].strip('/').strip('\\')
        else:
            data_name = os.path.basename(input_data)
        unzipped_folder_path = output_folder#os.path.join(output_folder,
                                          # os.path.basename(os.path.splitext(data_name)[0]))
        try:
            os.mkdir(unzipped_folder_path)
        except FileExistsError:
            pass
        properties_json = {'{}_name'.format(data_type): data_name}
        if additional_properties:
            properties_json['service_additional_properties'] = additional_properties
        if '.gdb' in input_data:
            gdb_path = '{}.gdb'.format(input_data.split('.gdb')[
                                       0]).strip('/').strip('\\')
            gdb_name = os.path.basename(gdb_path)
            try:
                connection_files = arcpy.Describe(input_data).ConnectionFiles
            except Exception as e:
                connection_files = None
            if connection_files:
                connection_file = connection_files[0]
                log.Message("Connection File Path.{}".format(connection_file),
                                    log.const_general_text)
                connection_file_name = os.path.basename(connection_file)
                if os.path.exists(connection_file):
                    shutil.copy(connection_files[0], unzipped_folder_path)
                    time_str = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
                    new_connection_file_path = r'C:\Image_Mgmt_Workflows\AIDE\{}\{}\{}'.format(
                     data_name, time_str, connection_file_name)
                    try:
                        arcpy.management.RepairMosaicDatasetPaths(
                            input_data,
                            "{} {}".format(connection_file, new_connection_file_path),
                            '')
                    except Exception as e:
                        arcpy.AddError("Repairing path of the connection file failed")
                        log.Message("Repairing path of the connection file failed.{}".format(str(e)),
                                    log.const_critical_text)
                        return
                    properties_json['connection_file'] = ''.join(['/arcgis/server/framework/',
                    'runtime/.wine/drive_c/Image_Mgmt_Workflows/AIDE/{}/{}/{}'.format(
                     data_name, time_str, connection_file_name)])

        elif '.acs' in input_data:
            shutil.copy('{}.acs'.format(
                input_data.split('.acs')[0]), unzipped_folder_path)
        else:
            # MRF
            aux_xml = '{}.aux.xml'.format(input_data)
            if os.path.exists(aux_xml):
                shutil.copy(aux_xml, unzipped_folder_path)
            if os.path.exists(input_data):
                shutil.copy(input_data, unzipped_folder_path)
        with open(os.path.join(unzipped_folder_path, 'properties.json'), 'w') as f:
            json.dump(properties_json, f)
        arcpy.ClearWorkspaceCache_management()
        filepaths = get_all_file_paths(unzipped_folder_path)
        with zipfile.ZipFile('{}.zmd'.format(unzipped_folder_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_dict in filepaths:
                zipf.write(file_dict['absname'], file_dict['arcname'])
        return '{}.zmd'.format(unzipped_folder_path)
    except Exception as e:
        arcpy.AddError("Error in zipping the dataset. Please check logs for more details")
        log.Message("Error in zipping the dataset:{}".format(str(e)),
                    log.const_critical_text)


def load_pods(username, pod_type='di'):
    try:
        curr_dir = os.path.dirname(__file__)
        refresh_fp = os.path.join(curr_dir, CACHED_PROFILES_FOLDER_NAME.format(pod_type),
                                  '{}.json'.format(username))
        with open(refresh_fp) as refresh_file:
            refresh_json = json.load(refresh_file)
        current_timestamp = datetime.datetime.now()
        if refresh_json['update_frequency'].lower() == 'none':
            return refresh_json['pods']
        elif refresh_json['update_frequency'].lower() == 'daily':
            no_days = 1
        elif refresh_json['update_frequency'].lower() == 'weekly':
            no_days = 7
        days_ago = (current_timestamp - datetime.timedelta(days=no_days)).date().strftime('%Y%m%d')
        if refresh_json['last_updated'].split('T')[0] <= days_ago:
            return []
        else:
            return refresh_json['pods']
    except:
        return []

def load_users(username, pod_id, pod_type='di'):
    try:
        curr_dir = os.path.dirname(__file__)
        refresh_fp = os.path.join(curr_dir, CACHED_PROFILES_FOLDER_NAME.format(pod_type),
                                  '{}.json'.format(username))
        with open(refresh_fp) as refresh_file:
            refresh_json = json.load(refresh_file)
        return refresh_json['users'][pod_id]
    except:
        return []

def update_pods_details(pods_details, username, pod_type='di'):
    try:
        curr_dir = os.path.dirname(__file__)
        profiles_dir = os.path.join(curr_dir, CACHED_PROFILES_FOLDER_NAME.format(pod_type))
        refresh_fp = os.path.join(profiles_dir, '{}.json'.format(username))
        if not os.path.exists(profiles_dir):
            os.makedirs(profiles_dir)
        refresh_json = {}
        if os.path.exists(refresh_fp):
            with open(refresh_fp) as refresh_file:
                refresh_json = json.load(refresh_file)
        else:
            refresh_json['update_frequency'] = 'daily'
            if pods_details:
                refresh_json['default_pod_id'] = pods_details[0]['pod_id']
        refresh_json['pods'] = pods_details
        refresh_json['last_updated'] = str(datetime.datetime.now().strftime("%Y%m%dT%H%M%S"))
        with open(refresh_fp, 'w') as refresh_file:
            json.dump(refresh_json, refresh_file)
    except Exception as e:
        pass

def update_users(users, username, pod_id, pod_type='di'):
    try:
        curr_dir = os.path.dirname(__file__)
        profiles_dir = os.path.join(curr_dir, CACHED_PROFILES_FOLDER_NAME.format(pod_type))
        refresh_fp = os.path.join(profiles_dir, '{}.json'.format(username))
        if not os.path.exists(profiles_dir):
            os.makedirs(profiles_dir)
        if os.path.exists(refresh_fp):
            with open(refresh_fp) as refresh_file:
                refresh_json = json.load(refresh_file)
                if not refresh_json.get('users'):
                    refresh_json['users'] = {}
                refresh_json['users'][pod_id] = users
            with open(refresh_fp, 'w') as refresh_file:
                json.dump(refresh_json, refresh_file)
    except Exception as e:
        pass

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "AID"

        # List of tool classes associated with this toolbox
        self.tools = [GetJobStatus, MAIDIS, MAIDTS, AIDISDP]


class GetJobStatus(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Get AID Job Status"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        global errorMessage
        errorMessage = ''
        global pods_details
        global pod
        """Define parameter definitions"""
        server = arcpy.Parameter(displayName="AID Server",
                              name="server",
                              datatype="GPString",
                              parameterType="Required",
                              direction="Input",
                              enabled=True)
        job_id = arcpy.Parameter(displayName="Job Id",
                                 name="job_id",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 enabled=True)
        job_status = arcpy.Parameter(displayName="Job Status",
                                     name="job_status",
                                     datatype="GPString",
                                     parameterType="Derived",
                                     direction="Output")
        searchorg = arcpy.Parameter(
            displayName="List all Job Ids for Server ",
            name="search_org",
            datatype='GPBoolean',
            parameterType="Optional",
            direction="Input")
        params = [server, job_id, job_status, searchorg]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def mapParams(self, parameters):
        params = {
            "pod": parameters[0],
            "job_id": parameters[1],
            "job_status": parameters[2],
            "searchorg": parameters[3]
        }
        return params

    def setFieldList(self, params, param_name, value_list):
        if not value_list:
            params[param_name].value = ''
            params[param_name].filter.list = []
        else:
            if params[param_name].valueAsText not in value_list:
                params[param_name].value = value_list[0]
            params[param_name].filter.list = value_list

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        global errorMessage
        global pods_details
        global pod
        params = self.mapParams(parameters)
        try:
            token = arcpy.GetSigninToken()['token']
        except:
            errorMessage = 'Please sign in to continue.'
            return
        customer_id = arcpy.GetPortalDescription()['id']
        pod_type = '*'
        if not params['pod'].altered:
            list_pods_response = utils.list_pods(token, customer_id, pod_type)
            pods_details = list_pods_response.get('pods')
            try:
                pod_alias = [pod.get('pod_alias') for pod in pods_details if pod.get('pod_alias')]
            except:
                errorMessage = "Unable to retrieve the server details. Please try after some time."
                if list_pods_response.get('error') and list_pods_response['error'].get('message'):
                    errorMessage = list_pods_response['error']['message']
                return
            self.setFieldList(params, 'pod', pod_alias)
        if params['pod'].altered and not params['pod'].hasBeenValidated:
            list_pods_response = utils.list_pods(token, customer_id, pod_type)
            pods_details = list_pods_response.get('pods')
            try:
                pod = [pod for pod in pods_details if params['pod'].valueAsText in pod['pod_alias']][0]
            except Exception as e:
                errorMessage = "Unable to retrieve the server details. Please try after some time."
                if list_pods_response.get('error') and list_pods_response['error'].get('message'):
                    errorMessage = list_pods_response['error']['message']
                return
            user_jobs = True
            if params['searchorg'].value:
                user_jobs = False
            list_jobs_response = utils.list_jobs(
                token, customer_id, pod['pod_id'], user_jobs)
            try:
                jobs = list_jobs_response.get('jobs')
                job_ids = [job['job_id'] for job in jobs]
                job_ids.sort(reverse=True)
                params['job_id'].filter.list = job_ids
            except Exception as e:
                errorMessage = 'Unable to retrive the jobs. Please try after some time.'
                if list_jobs_response.get('error') and list_jobs_response['error'].get('message'):
                    errorMessage = list_jobs_response['error']['message']
                return
        if params['searchorg'].altered and not params['searchorg'].hasBeenValidated:
            user_jobs = True
            if params['searchorg'].value:
                user_jobs = False
            list_jobs_response = utils.list_jobs(
                token, customer_id, pod['pod_id'], user_jobs)
            try:
                jobs = list_jobs_response.get('jobs')
                job_ids = [job['job_id'] for job in jobs]
                job_ids.sort(reverse=True)
                params['job_id'].filter.list = job_ids
            except Exception as e:
                errorMessage = 'Unable to retrive the jobs. Please try after some time.'
                if list_jobs_response.get('error') and list_jobs_response['error'].get('message'):
                    errorMessage = list_jobs_response['error']['message']
                return


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        global errorMessage
        params = self.mapParams(parameters)
        if errorMessage:
            parameters[0].setErrorMessage(errorMessage)
        else:
            parameters[0].clearMessage()
        if params['job_id'].altered and not params['job_id'].hasBeenValidated:
            job_ids = params['job_id'].filter.list
            if params['job_id'].value not in job_ids:
                params['job_id'].setErrorMessage("Job id does not exist.")
            else:
                params['job_id'].clearMessage()
        if params['searchorg'].altered and not params['searchorg'].hasBeenValidated:
            job_ids = params['job_id'].filter.list
            if params['job_id'].value not in job_ids:
                params['job_id'].setErrorMessage("Job id does not exist.")
            else:
                params['job_id'].clearMessage()

    def execute(self, parameters, messages):
        global pods_details
        log = initializeLog('GetJobStatus')
        try:
            params = self.mapParams(parameters)
            token = arcpy.GetSigninToken()['token']
            customer_id = arcpy.GetPortalDescription()['id']
            pod_dns = params['pod'].valueAsText
            try:
                pod_id = [pod['pod_id'] for pod in pods_details if pod_dns in pod['pod_alias']][0]
            except:
                arcpy.AddError("Could not retrieve the pod id")
                closeLog(log)
            job_id = params['job_id'].valueAsText
            if 'permission' in job_id:
                subject = 'service'
                action = job_id.split('_')[-1][:job_id.split('_')[-1].index('permission')]
            elif 'service' in job_id:
                subject = 'service'
                action = job_id.split('_')[-1][:job_id.split('_')[-1].index('service')]
            elif 'pod' in job_id:
                subject = 'pod'
                action = job_id.split('_')[-1][:job_id.split('_')[-1].index('pod')]
            check_words = ['delete','stop','permission', 'pod']
            if any(word in job_id for word in check_words):
                success_message_template = 'The '+ subject +' has been {}.'
            else:
                success_message_template = 'The '+ subject +' has been {} and the service url is below. \n {}'
            failure_message = 'Could not {} the {}.'.format(action, subject)
            action_verb = '{}{}ed'.format(action.lower().strip('e'),
                                          'p' if action.lower().endswith('p') else '')
            status_response = utils.get_job_status(
                token, customer_id, pod_id, job_id, log)
            jobs = status_response.get('jobs')
            job_status = [job['job_status']
                          for job in jobs if job['job_id'] == job_id]
            job_result = [job.get('job_result') for job in jobs if (
                job['job_id'] == job_id and job.get('job_result'))]
            list_pods_response = utils.list_pods(token, customer_id, '*')
            pods_details = list_pods_response.get('pods')
            pod_dns = [pod.get('dns')
                       for pod in pods_details if pod['pod_id'] == pod_id]
            dns = ''
            if pod_dns:
                dns = pod_dns[0].strip('/')
            arcpy.AddMessage('------------------------------------------------------')
            if not job_status:
                arcpy.AddWarning("Job not found!")
                log.Message("job {} not found".format(
                    job_id), log.const_critical_text)
                arcpy.SetParameter(parameters.index(params['job_status']), '')
            else:
                if job_status[0].lower() == 'success':
                    if job_result:
                        arcpy.AddMessage(success_message_template.format(action_verb,
                                                                     job_result[0].format(dns)))
                    else:
                        arcpy.AddMessage(success_message_template.format(action_verb))
                elif job_status[0].lower() == 'failed':
                    arcpy.AddMessage(failure_message)
                    if job_result and '{}' not in job_result[0]:
                        arcpy.AddMessage("Error: {}".format(job_result[0]))
                else:
                    arcpy.AddMessage("{} service status: {}".format(action,
                                                                        job_status[0]))
                arcpy.SetParameter(parameters.index(params['job_status']),
                                   job_status[0].lower())
            arcpy.AddMessage('------------------------------------------------------')
            closeLog(log)
        except Exception as e:
            arcpy.AddError("Error in get job status")
            log.Message("Error in get job status:{}".format(
                str(e)), log.const_critical_text)
            arcpy.SetParameter(parameters.index(params['job_status']),
                               'gptoolerror')
            closeLog(log)


class MAIDIS(object):

    actions = {
        "create": "Create Service",
        "update": "Update Service",
        "delete": "Delete Service",
        "start_stop": "Start/Stop Service",
        "update_permission": "Set Service Permission"
    }
    actions_list = list(actions.values())
    instance_types = ['Dedicated Instance', 'Shared Instance']
    user_permissions_list = ['Enabled', 'Disabled']

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Manage AID Image Services"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        global pods
        global pods_details
        global pods_services
        global pods_folders
        global errorMessages
        errorMessages = ['', '', '']
        """Define parameter definitions"""
        aid_is = arcpy.Parameter(displayName="AID Image Server",
                                 name="aid_is",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 enabled=True)
        action = arcpy.Parameter(displayName="Action",
                                 name="action",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 enabled=True)
        server_folder_name = arcpy.Parameter(displayName="Server Folder Name",
                                      name="server_folder_name",
                                      datatype="GPString",
                                      parameterType="Optional",
                                      direction="Input",
                                      enabled=True)
        instance_type = arcpy.Parameter(displayName="Instance Type",
                                        name="instance_type",
                                        datatype="GPString",
                                        parameterType="Optional",
                                        direction="Input",
                                        enabled=True)
        new_service_name = arcpy.Parameter(displayName="Image Service Name",
                                           name="new_service_name",
                                           datatype="GPString",
                                           parameterType="Required",
                                           direction="Input",
                                           enabled=True)
        existing_service_name = arcpy.Parameter(displayName="Image Service Name",
                                                name="existing_service_name",
                                                datatype="GPString",
                                                parameterType="Optional",
                                                direction="Input",
                                                enabled=True)
        service_definition_package = arcpy.Parameter(displayName="AID Image Service Definition Package",
                                          name="service_definition_package",
                                          datatype="DEFile",
                                          parameterType="Required",
                                          direction="Input",
                                          enabled=True)
        service_definition_package.filter.list = ['zmd']
        update_service_definition_package = arcpy.Parameter(displayName="AID Image Service Definition Package",
                                          name="update_service_definition_package",
                                          datatype="DEFile",
                                          parameterType="Optional",
                                          direction="Input",
                                          enabled=True)
        update_service_definition_package.filter.list = ['zmd']
        description = arcpy.Parameter(displayName="Description",
                                      name="description",
                                      datatype="GPString",
                                      parameterType="Optional",
                                      direction="Input",
                                      enabled=True)
        copyright = arcpy.Parameter(displayName="Copyright",
                                    name="copyright",
                                    datatype="GPString",
                                    parameterType="Optional",
                                    direction="Input",
                                    enabled=True)
        change_service_status = arcpy.Parameter(
            displayName="Change service status",
            name="change_service_status",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            enabled=False)
        delete_source = arcpy.Parameter(
            displayName="Delete Source",
            name="delete_source",
            datatype='GPBoolean',
            parameterType="Optional",
            direction="Input",
            enabled=False)
        create_portal_item = arcpy.Parameter(
            displayName="Create Portal Item",
            name="create_portal_item",
            datatype='GPBoolean',
            parameterType="Optional",
            direction="Input",
            enabled=True)
        enable_wms = arcpy.Parameter(
            displayName="Enable WMS",
            name="enable_wms",
            datatype='GPBoolean',
            parameterType="Optional",
            direction="Input",
            enabled=True)
        enable_wcs = arcpy.Parameter(
            displayName="Enable WCS",
            name="enable_wcs",
            datatype='GPBoolean',
            parameterType="Optional",
            direction="Input",
            enabled=True)
        set_service_permissions = arcpy.Parameter(
            displayName="Set service permissions",
            name="set_service_permissions",
            datatype='GPBoolean',
            parameterType="Optional",
            direction="Input",
            enabled=True)
        enable_tiled_imagery = arcpy.Parameter(
            displayName="Enable Tiled Imagery",
            name="enable_tiled_imagery",
            datatype='GPBoolean',
            parameterType="Optional",
            direction="Input",
            enabled=True)        
        users = arcpy.Parameter(
                displayName="Users to give or revoke permission",
                name="users",
                datatype="GPValueTable",
                parameterType="Optional",
                direction="Input",
                enabled=False)
        users.columns=[["GPString", "User"],["GPString", "Permission detail"]]
        users.filters[0].type = 'ValueList'
        users.filters[1].type = 'ValueList'
        users.filters[1].list = self.user_permissions_list
        create_portal_item.value = False
        delete_source.value = False
        action.filter.list = self.actions_list
        action.value = self.actions_list[0]
        instance_type.filter.list = self.instance_types
        instance_type.value = self.instance_types[0]
        params = [aid_is, action,
                  server_folder_name, new_service_name, existing_service_name,
                  service_definition_package, update_service_definition_package,
                  instance_type, description,
                  copyright, change_service_status,
                  delete_source,
                  create_portal_item, enable_wms,
                  enable_wcs, enable_tiled_imagery,
                  set_service_permissions,
                  users]
        return params

    def setFieldList(self, params, param_name, value_list):
        if not value_list:
            params[param_name].value = ''
            params[param_name].filter.list = []
        else:
            if params[param_name].valueAsText not in value_list:
                params[param_name].value = value_list[0]
            params[param_name].filter.list = value_list

    def enableParams(self, enable_list, all_parameters):
        for param in all_parameters:
            if param in enable_list:
                param.enabled = True
                if 'String' in param.datatype and param.parameterType == 'Required':
                    if param.valueAsText == "None":
                        param.value = ""
                if param.name == 'service_package':
                    param.value = ''
            else:
                if 'String' in param.datatype and param.parameterType == 'Required':
                    param.value = "None"
                if param.name == 'service_package':
                    param.value = "dummy.zmd"
                param.enabled = False

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def mapParams(self, parameters_list):
        return {
            "pod": parameters_list[0],
            "action": parameters_list[1],
            "folder_name": parameters_list[2],
            "new_service_name": parameters_list[3],
            "service_name": parameters_list[4],
            "service_package": parameters_list[5],            
            "update_service_package": parameters_list[6],
            "instance_type": parameters_list[7],
            "description": parameters_list[8],
            "copyright": parameters_list[9],
            "service_running_status": parameters_list[10],
            "delete_source": parameters_list[11],
            "add_item_to_portal": parameters_list[12],
            "enable_wms": parameters_list[13],
            "enable_wcs": parameters_list[14],
            "enable_tiled_imagery": parameters_list[15],
            "make_service_secure": parameters_list[16],
            "users": parameters_list[17]
        }

    def setServiceDetails(self, params, services):
        action = params['action'].valueAsText
        service_param = params['service_name']
        folder = params['folder_name'].valueAsText
        folder = '' if folder == '[root]' else folder
        if services:
            try:
                if folder:
                    service_details = [
                        service for service in services if service['name'] == '/'.join([folder, service_param.valueAsText])][0]
                else:
                    service_details = [
                        service for service in services if service['name'] == service_param.valueAsText][0]
            except Exception as e:
                return
            try:
                service_properties = json.loads(
                    service_details['service_properties']) or {}
            except Exception as e:
                service_properties = {}
            if action == self.actions['start_stop']:
                params['service_running_status'].value = service_details['service_status']
                params['service_running_status'].filter.list = [
                    'STARTED', 'STOPPED']
            if action == self.actions['update']:
                params['description'].value = service_properties.get(
                    'description')
                params['copyright'].value = service_properties.get('copyright')
            if action == self.actions['update_permission']:
                if service_details.get('permitted_users'):
                    users = service_details.get('permitted_users').split(',')
                    users = ['public' if user == 'esriEveryone' else user for user in users]
                    users = [[user, 'Enabled'] for user in users]
                    params['users'].value = users
                else:
                    params['users'].value = []

    def enable_params_by_action(self, params, parameters):
        new_service_param = params['new_service_name']
        service_param = params['service_name']
        data_param = params['service_package']
        update_data_param = params['update_service_package']
        if params['action'].valueAsText == self.actions['delete']:
            self.enableParams([params['pod'], service_param,
                               params['action'], params['folder_name']],
                              parameters)
        elif params['action'].valueAsText == self.actions['create']:
            self.enableParams(
                [new_service_param, params['folder_name'],
                 params['description'], params['action'],
                 params['copyright'], data_param,
                 params['pod'], params['instance_type'],
                 params['enable_tiled_imagery'],
                 params['add_item_to_portal'],
                 params['make_service_secure'],
                 params['enable_wms'], params['enable_wcs']],
                parameters)
            params['action'].filter.list = self.actions_list
        elif params['action'].valueAsText == self.actions['update']:
            self.enableParams(
                [service_param, params['description'],
                 params['folder_name'], params['pod'],
                 update_data_param, params['action'],
                 params['copyright'],
                 params['enable_wms'], params['enable_wcs']],
                parameters)
        elif params['action'].valueAsText == self.actions['start_stop']:
            self.enableParams([params['pod'], service_param,
                               params['action'], params['folder_name'],
                               params['service_running_status']],
                              parameters)
        elif params['action'].valueAsText == self.actions['update_permission']:
            self.enableParams([params['pod'], service_param, params['action'],
                               params['folder_name'], params['users']], parameters)

    def setDefaultParams(self, params, parameters):
        self.enableParams([params['new_service_name'], params['folder_name'],
                 params['description'], params['action'],
                 params['copyright'], params['service_package'],
                 params['pod'], params['instance_type'],
                 params['enable_tiled_imagery'],
                 params['add_item_to_portal'],
                 params['make_service_secure'],
                 params['enable_wms'], params['enable_wcs']], parameters)

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        global pods
        global pods_details
        global pods_services
        global pods_folders
        global users
        users = []
        global errorMessages
        pythonScriptExecution = False
        params = self.mapParams(parameters)
        executable_path = sys.executable
        if executable_path.lower().endswith("python.exe"):
            pythonScriptExecution = True
        if pythonScriptExecution:
            description = params['description'].valueAsText
            copyright = params['copyright'].valueAsText
            user_permissions = params['users'].value
            service_running_status = params['service_running_status'].valueAsText
            service_package = params['service_package'].valueAsText
            folder_name = params['folder_name'].valueAsText
            service_name = params['service_name'].valueAsText
        try:
            token = arcpy.GetSigninToken()['token']
            errorMessages[0] = ''
        except Exception as e:
            self.setDefaultParams(params, parameters)
            errorMessages[0] = "Please sign in to continue"
            return
        try:
            gis = GIS("Pro")
            customer_id = gis.properties['id']
            username = gis.users.me.username
            errorMessages[0] = ''
        except:
            self.setDefaultParams(params, parameters)
            errorMessages[0] = "Please sign in to continue"
            return
        if not params["pod"].altered or pythonScriptExecution:
            pods_details = load_pods(username)
            if pods_details:
                pod_alias = [pod.get('pod_alias') for pod in pods_details if pod.get('pod_alias')]
            else:
                pod_type = 'di'
                list_pods_response = utils.list_pods(token, customer_id, pod_type)
                pods_details = list_pods_response.get('pods')
                if pods_details != None:
                    pod_alias = [pod.get('pod_alias') for pod in pods_details if pod.get('pod_alias')]
                    update_pods_details(pods_details, username)
                    errorMessages[1] = ''
                else:
                    pod_alias = []
                    errorMessages[1] = "The API is temporarily not working. Please try after some time."
                    self.setDefaultParams(params, parameters)
                    if list_pods_response.get('error'):
                        errorMessages[1] = list_pods_response['error']['message']
                    return
            pods = pod_alias
            self.setFieldList(params, 'pod', pod_alias)
            if not params['pod'].value:
                self.setDefaultParams(params, parameters)
        if not params['action'].altered:
            params['action'].value = self.actions['create']
        if params['pod'].altered and not params['pod'].hasBeenValidated:
            try:
                if not pods_details:
                    errorMessages[1] = "Unable to retrieve the servers list. Please try reloading the tool."
                    self.setDefaultParams(params, parameters)
                    return
            except:
                errorMessages[1] = "Unable to retrieve the servers list. Please try reloading the tool."
                self.setDefaultParams(params, parameters)
                return
            if not params['action'].altered:
                params['action'].value = self.actions['create']
            try:
                pod = [pod for pod in pods_details if params['pod'].valueAsText == pod['pod_alias']][0]
            except:
                errorMessages[1] = "Unable to retrieve the servers list. Please try reloading the tool."
                self.setDefaultParams(params, parameters)
                return
            services_resp = utils.get_services(token, customer_id, pod['pod_id'],
                                               None)
            users = load_users(username, pod['pod_id'])
            if not users:
                list_users_response = utils.get_users(token, customer_id, pod['pod_id'])
                users = list_users_response.get('users')
                if users:
                    users.append('public')
                update_users(users, username, pod['pod_id'])
            if not params['users'].altered:
                params['users'].filters[0].list = users or ['public']
            pods_services = services_resp.get('services')
            if pods_services != None:
                errorMessages[2] = ''
            else:
                errorMessages[2] = "The API is temporarily not working. Please try after some time."
                if services_resp.get('error'):
                    errorMessages[2] = services_resp['error']['message']
                self.setDefaultParams(params, parameters)
                return
            pods_folders = list(
                set(service['server_folder'] for service in pods_services if service['server_folder']))
            self.setFieldList(params, 'folder_name', pods_folders)
            self.enable_params_by_action(params, parameters)
        if params['folder_name'].altered and not params['folder_name'].hasBeenValidated:
            folder_name = params['folder_name'].valueAsText
            if params['action'].value == self.actions['create']:
                if folder_name and folder_name not in pods_folders:
                    pods_folders.append(folder_name)
                    self.setFieldList(params, 'folder_name', pods_folders)
            else:
                try:
                    service_names = [service.get('name').split('/')[-1]
                                     for service in pods_services
                                     if service['server_folder'] == folder_name]
                except:
                    service_names = []
                self.setFieldList(params, 'service_name', service_names)
        if params['service_name'].altered and not params['service_name'].hasBeenValidated:
            if params['service_name'].valueAsText:
                self.setServiceDetails(params, pods_services)
        if params['action'].altered and not params['action'].hasBeenValidated:
            self.enable_params_by_action(params, parameters)
            if params['action'].value != self.actions['create']:
                try:
                    service_names = [service.get('name').split('/')[-1] for service in pods_services
                                     if service['server_folder'] == params['folder_name'].valueAsText]
                    self.setFieldList(params, 'service_name', service_names)
                    self.setServiceDetails(params, pods_services)
                except:
                    service_names = []
                    self.setFieldList(params, 'service_name', service_names)
        if (params['make_service_secure'].enabled and params['make_service_secure'].value) or \
           params['action'].valueAsText == self.actions['update_permission']:
            params['users'].enabled = True
        else:
            params['users'].enabled = False
        if not params['folder_name'].valueAsText:
            try:
                service_names = [service.get('name').split('/')[-1]
                                 for service in pods_services
                                 if service['server_folder'] == '[root]']
            except:
                service_names = []
            self.setFieldList(params, 'service_name', service_names)
        if pythonScriptExecution:
            if description:
                params['description'].value = description
            if copyright:
                params['copyright'].value = copyright
            if user_permissions:
                params['users'].value = user_permissions
            if service_running_status:
                params['service_running_status'].value = service_running_status
            if service_package:
                params['service_package'].value = service_package
            if service_name:
                params['service_name'].value = service_name
            if folder_name:
                folders = params['folder_name'].filter.list
                if folder_name not in folders:
                    folders.append(folder_name)
                    params['folder_name'].filter.list = folders
                params['folder_name'].value = folder_name

    def checkDataTypeUpdateMessage(self, param, match_string='.zmd'):
        message = ''
        if (param.enabled and
            param.valueAsText and
                match_string not in param.valueAsText):
            if match_string == '.zmd':
                message = "Data must be zmd format."
            param.setErrorMessage("Unsupported data. {}".format(message))
        else:
            param.clearMessage()

    def validateSpecialCharacters(self, param):
        if param.enabled:
            if param.altered and not param.hasBeenValidated:
                if not re.match("^[A-Za-z0-9_]*$", param.valueAsText):
                    param.setErrorMessage("The service name can contain only alpha numeric characters")
                else:
                    param.clearMessage()
            else:
                param.clearMessage()
        else:
            param.clearMessage()

    def validateListValue(self, param, err):
        if param.enabled:
            if param.altered and not param.hasBeenValidated:
                values = param.filter.list
                if param.value not in values:
                    param.setErrorMessage(err)
                else:
                    param.clearMessage()

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        global errorMessages
        global pods_services
        params = self.mapParams(parameters)
        for errorMessage in errorMessages:
            if errorMessage:
                parameters[0].setErrorMessage(errorMessage)
                return
        if all(not errorMessage for errorMessage in errorMessages):
            parameters[0].clearMessage()
        self.checkDataTypeUpdateMessage(params['service_package'])
        self.checkDataTypeUpdateMessage(params['update_service_package'])
        self.validateListValue(params['service_name'], 'The image service does not exist in this folder. Please select an existing image service.')
        if params['new_service_name'].valueAsText:
            try:
                service_names = [service.get('name').split('/')[-1] for service in pods_services
                             if service['server_folder'] == params['folder_name'].valueAsText]
            except:
                service_names = []
            if params['new_service_name'].valueAsText in service_names:
                params['new_service_name'].setErrorMessage("Service already exists in the selected folder. Please use a different name.")
            else:
                self.validateSpecialCharacters(params['new_service_name'])
        if params['service_name'].valueAsText and params['service_name'].enabled:
            if params['action'].valueAsText == self.actions['delete']:
                try:
                    service_names = [service.get('name').split('/')[-1] for service in pods_services
                                 if service['server_folder'] == params['folder_name'].valueAsText]
                except:
                    service_names = []
                if params['service_name'].valueAsText not in service_names:
                    params['service_name'].setErrorMessage("This service does not exist in this folder.")
                else:
                    params['service_name'].clearMessage()
        
        if params['action'].valueAsText == self.actions['start_stop']:
            if not params['service_running_status'].valueAsText:
                params['service_running_status'].setErrorMessage(
                    "Please set the service running status")
            else:
                params['service_running_status'].clearMessage()

    def is_valid_package(self, package_path, service_type):
        z = zipfile.ZipFile(package_path, "r")
        filenames = z.namelist()
        filenames_contain_acs = [filename for filename in filenames if '.acs' in filename]
        if service_type == 'Tile Service':
            for name in filenames:
                if name == 'properties.json':
                    with z.open(name) as f:
                        properties_json = json.load(f)
                    if properties_json.get('raster_name') and \
                       properties_json['raster_name'].lower().endswith('.crf'):
                        if filenames_contain_acs:
                            return False
                        return True
            return False
        return True


    def execute(self, parameters, messages):
        log = initializeLog("MAIDIS")
        global pods
        global pods_details
        global pods_services
        global pods_folders
        try:
            params = self.mapParams(parameters)
            token = arcpy.GetSigninToken()['token']
            action = params['action'].valueAsText
            added_item_id = None
            customer_id = arcpy.GetPortalDescription()['id']
            if not pods_details:
                list_pods_response = utils.list_pods(token, customer_id, 'di')
                pods_details = list_pods_response.get('pods')
            pod = [pod for pod in pods_details if params['pod'].valueAsText in pod['pod_alias']][0]
            pod_id = pod['pod_id']
            try:
                cloudstore = utils.get_cloudstore(token, customer_id, pod_id)['cloudStore']
            except Exception as e:
                log.Message("Error in getting cloud store: {}".format(str(e)), log.const_critical_text)
                cloudstore = None
            service_type = 'Tile Service' if params['enable_tiled_imagery'].value else 'Dynamic Image Service'
            if params['service_package'].enabled and params['service_package'].valueAsText:
                is_package_valid = self.is_valid_package(params['service_package'].valueAsText,
                                      service_type)
                if not is_package_valid:
                    log.Message("This package is invalid. For a tile service, the input data must be a crf. Also acs files are not supported in this workflow.",
                                log.const_critical_text)
                    arcpy.AddError("This package is invalid. For a tile service, the input data must be a crf. Also acs files are not supported in this workflow.")
                    closeLog(log)
                    return
                if 'tile' in service_type.lower() and not cloudstore:
                    log.Message("To publish a tile service, the pod should have a data bucket associated with it.",
                                log.const_critical_text)
                    arcpy.AddError("To publish a tile service, the pod should have a data bucket associated with it.")
                    closeLog(log)
                    return
            new_service_param = params['new_service_name']
            service_param = params['service_name']
            data_param = params['service_package']
            update_data_param = params['update_service_package']
            folder = params['folder_name'].valueAsText
            if folder and folder == '[root]':
                folder = ''
            service_name = service_param.valueAsText
            try:
                service = [pods_service for pods_service in pods_services if pods_service.get('name').split('/')[-1] == service_name][0]
            except:
                service = {}
            imagery_uploaded = False
            log.Message("Action:{}".format(action),
                        log.const_general_text)
            data_path = data_param.valueAsText
            wait_time = DEFAULT_WAIT_TIME
            if '/' not in action:
                short_action = action.split()[0].lower()
            else:
                short_actions = action.split()[0].lower().split('/')
                short_action = [sa for sa in short_actions if
                                sa.lower()[0:4] == params['service_running_status'].valueAsText.lower()[0:4]][0]
            action_verb = '{}{}ed'.format(short_action.lower().strip('e'),
                                          'p' if short_action.lower().endswith('p') else '')
            if 'permission' in action.lower():
                action_verb = 'set'
                success_message_template = 'The service permission has been {}'
            else:
                check_words = ['delete','stop']
                if any(word in action.lower() for word in check_words):
                    success_message_template = 'The service has been {}.'
                else:
                    success_message_template = 'The service has been {} and the service url is below. \n {}'
            failure_message = 'Could not {} the service.'.format(short_action)
            if action == self.actions['update']:
                data_path = update_data_param.valueAsText
            if action in (self.actions['create'], self.actions['update']):
                if data_path and not data_path.startswith('http'):
                    presigned_response = utils.get_presigned_url(token, customer_id, pod_id,
                                                                 os.path.basename(data_path), None, log)
                    if (not presigned_response) or (not presigned_response.get('url')):
                        log.Message("Error in getting presigned URL",
                                    log.const_critical_text)
                        arcpy.AddError("Error in uploading data")
                        closeLog(log)
                        return
                    upload_response = utils.upload_imagery(data_path, presigned_response['url'],
                                                           presigned_response['fields'], log)
                    if not upload_response:
                        log.Message("Error in uploading data",
                                    log.const_critical_text)
                        arcpy.AddError("Error in uploading data")
                        closeLog(log)
                        return
                    imagery_uploaded = True
                    data_path = os.path.basename(data_path)
            if action == self.actions['create']:
                wait_time = CREATE_WAIT_TIME
                service_name = new_service_param.valueAsText
                description = params['description'].valueAsText
                users_permissions = params['users'].value
                enabled_users = ['esriEveryone']
                disabled_users = []
                if users_permissions:
                    enabled_users = [user_permission[0] for user_permission in users_permissions if user_permission[1] == 'Enabled']
                    disabled_users = [user_permission[0] for user_permission in users_permissions if user_permission[1] == 'Disabled']
                    enabled_users = [user if user != 'public' else 'esriEveryone' for user in enabled_users]
                    disabled_users = [user if user != 'public' else 'esriEveryone' for user in disabled_users]
                    if 'esriEveryone' not in disabled_users:
                        enabled_users.append('esriEveryone')
                service_params = {
                    "serviceName": service_name,
                    "description": description,
                    "copyright": params["copyright"].valueAsText,
                    "dataPath": data_path,
                    "folder": folder,
                    "properties": None,
                    "imageryDataUploaded": imagery_uploaded,
                    "enabledUsers": enabled_users,
                    "disabledUsers": disabled_users,
                    "enableWms": params['enable_wms'].value,
                    "enableWcs": params['enable_wcs'].value,
                    "cloudstore": cloudstore,
                    "instanceType": params['instance_type'].valueAsText,
                    "serviceType": service_type
                }
                add_item_to_portal = params['add_item_to_portal'].value
                item_params = None
                if add_item_to_portal:
                    folder_service = service_name
                    if folder:
                        folder_service = '{}/{}'.format(folder, service_name)
                    service_url = ''.join([pod.get('dns').strip('/'),
                                           '/rest/services/{}/ImageServer'.format(
                                               folder_service)])
                    added_item_id = add_portal_item(service_name, description, service_url, log)
                    try:
                        if added_item_id:
                            item_params = {
                                                    "portal_token": arcpy.GetSigninToken()['token'],
                                                    "portal_username": arcpy.GetPortalDescription()[
                                                        'user']['username'],
                                                    "portal_url": arcpy.GetActivePortalURL(),
                                                    "id": added_item_id
                                                }
                    except Exception as e:
                        item_params = None
                log.Message("Service params:{}".format(
                    str(service_params)), log.const_general_text)
                resp_json = utils.create_service(
                    token, customer_id, pod_id, service_params, log, item_params)
            elif action == self.actions['update']:
                service_params = {
                    "serviceName": service_name,
                    "description": params['description'].valueAsText,
                    "copyright": params["copyright"].valueAsText,
                    "dataPath": data_path,
                    "folder": folder,
                    "serviceID": service['service_id'],
                    'properties': None,
                    "imageryDataUploaded": imagery_uploaded,
                    "enableWms": params['enable_wms'].value,
                    "enableWcs": params['enable_wcs'].value
                }
                log.Message("Service params:{}".format(
                    str(service_params)), log.const_general_text)
                delete_source = params['delete_source'].value
                resp_json = utils.update_service(token, customer_id, pod_id,
                                                 service_name,
                                                 service_params,
                                                 delete_source,
                                                 log)
            elif action == self.actions['delete']:
                wait_time = DELETE_WAIT_TIME
                delete_source = params['delete_source'].value
                resp_json = utils.delete_service(token, customer_id, pod_id,
                                                 service_name,
                                                 folder,
                                                 service['service_id'],
                                                 delete_source,
                                                 log)
            elif action == self.actions['start_stop']:
                start_service = False
                if params['service_running_status'].valueAsText == 'STARTED':
                    start_service = True
                resp_json = utils.start_stop_service(token, customer_id, pod_id,
                                                     service_name, folder,
                                                     service['service_id'],
                                                     log,
                                                     start_service=start_service)
            elif action == self.actions['update_permission']:
                users_permissions = params['users'].value
                enabled_users = []
                disabled_users = []
                if users_permissions:
                    enabled_users = [user_permission[0] for user_permission in users_permissions if user_permission[1] == 'Enabled']
                    disabled_users = [user_permission[0] for user_permission in users_permissions if user_permission[1] == 'Disabled']
                    enabled_users = [user if user != 'public' else 'esriEveryone' for user in enabled_users]
                    disabled_users = [user if user != 'public' else 'esriEveryone' for user in disabled_users]
                    resp_json = utils.update_permission_service(token, customer_id, pod_id, service_name, folder,
                                                                service['service_id'], log, enabled_users,
                                                                disabled_users)
            job_id = resp_json.get('jobID')
            log.Message('API response:{}'.format(resp_json), log.const_general_text)
            if not job_id:
                arcpy.AddError('{}. Please check the logs for more details'.format(failure_message))
                closeLog(log)
                return
            time.sleep(40)
            arcpy.AddMessage('------------------------------------------------------')
            arcpy.AddMessage("Job id: {}".format(job_id))
            log.Message("Job id:".format(job_id), log.const_general_text)

            status_response = utils.get_job_status(
                token, customer_id, pod_id, job_id, log)
            services_resp = utils.get_services(token, customer_id, pod_id,
                                               None)
            pods_services = services_resp.get('services')
            jobs = status_response.get('jobs')
            job_status = [job['job_status']
                          for job in jobs if job['job_id'] == job_id]
            job_result = [job.get('job_result') for job in jobs if (
                job['job_id'] == job_id and job.get('job_result'))]
            try:
                dns = pod['dns'].strip('/')
            except:
                dns = ''
            if job_status:
                if job_status[0].lower() == 'success':
                    if job_result:
                        arcpy.AddMessage(success_message_template.format(action_verb,
                                                                     job_result[0].format(dns)))
                    else:
                        arcpy.AddMessage(success_message_template.format(action_verb))
                    if added_item_id:
                        arcpy.AddMessage("Added item id is: {}".format(str(added_item_id)))
                elif job_status[0].lower() == 'failed':
                    arcpy.AddMessage(failure_message)
                    if job_result and '{}' not in job_result[0]:
                        arcpy.AddMessage("Error: {}".format(job_result[0]))
                else:
                    additional_message = 'Please check Get Job Status Tool for more info.'
                    arcpy.AddMessage("{} service status: {}. {}".format(short_action,
                                                                        job_status[0],
                                                                        additional_message))
            arcpy.AddMessage('------------------------------------------------------')
            closeLog(log)
        except Exception as e:
            arcpy.AddError("Error in manage image services")
            log.Message("Error in manage image services {}".format(
                str(e)), log.const_critical_text)
            closeLog(log)

class MAIDTS(object):

    actions = {
        "create": "Create Service",
        "update": "Update Service",
        "delete": "Delete Service"
    }
    actions_list = list(actions.values())

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Manage AID Tile Services"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        global pods
        global pods_details
        global pods_services
        global pods_folders
        global errorMessages
        errorMessages = ['', '', '']
        """Define parameter definitions"""
        pod = arcpy.Parameter(displayName="AID Tile Server",
                                 name="server",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 enabled=True)
        action = arcpy.Parameter(displayName="Action",
                                 name="action",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 enabled=True)
        folder_name = arcpy.Parameter(displayName="Server Folder Name",
                                      name="folder_name",
                                      datatype="GPString",
                                      parameterType="Optional",
                                      direction="Input",
                                      enabled=True)
        new_service_name = arcpy.Parameter(displayName="Tile Service Name",
                                           name="new_service_name",
                                           datatype="GPString",
                                           parameterType="Required",
                                           direction="Input",
                                           enabled=True)
        service_name = arcpy.Parameter(displayName="Tile Service Name",
                                       name="service_name",
                                       datatype="GPString",
                                       parameterType="Optional",
                                       direction="Input",
                                       enabled=True)
        data_path = arcpy.Parameter(displayName="Input Data Path",
                                    name="data_path",
                                    datatype="GPString",
                                    parameterType="Required",
                                    direction="Input",
                                    enabled=True)
        update_data_path = arcpy.Parameter(displayName="Input Data Path",
                                    name="update_data_path",
                                    datatype="GPString",
                                    parameterType="Optional",
                                    direction="Input",
                                    enabled=True)
        storage_keys = arcpy.Parameter(displayName="Storage keys",
                                            name="storage_keys",
                                            datatype="GPString",
                                            parameterType="Optional",
                                            direction="Input",
                                            enabled=False)
        description = arcpy.Parameter(displayName="Description",
                                      name="description",
                                      datatype="GPString",
                                      parameterType="Optional",
                                      direction="Input",
                                      enabled=True)
        copyright = arcpy.Parameter(displayName="Copyright",
                                    name="copyright",
                                    datatype="GPString",
                                    parameterType="Optional",
                                    direction="Input",
                                    enabled=True)
        create_portal_item = arcpy.Parameter(
            displayName="Create Portal Item",
            name="create_portal_item",
            datatype='GPBoolean',
            parameterType="Optional",
            direction="Input",
            enabled=True)
        action.filter.list = self.actions_list
        action.value = 'Create Service'
        params = [pod, action,
                  folder_name, new_service_name,
                  service_name, data_path,
                  update_data_path,
                  storage_keys, description,
                  copyright, create_portal_item]
        return params

    def setFieldList(self, params, param_name, value_list):
        if not value_list:
            params[param_name].value = ''
            params[param_name].filter.list = []
        else:
            if params[param_name].valueAsText not in value_list:
                params[param_name].value = value_list[0]
            params[param_name].filter.list = value_list

    def enableParams(self, enable_list, all_parameters):
        for param in all_parameters:
            if param in enable_list:
                param.enabled = True
                if 'String' in param.datatype and param.parameterType == 'Required':
                    if param.valueAsText == "None":
                        param.value = ""
            else:
                if 'String' in param.datatype and param.parameterType == 'Required':
                    param.value = "None"
                param.enabled = False

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def mapParams(self, parameters_list):
        return {
            "pod": parameters_list[0],
            "action": parameters_list[1],
            "folder_name": parameters_list[2],
            "new_service_name": parameters_list[3],
            "service_name": parameters_list[4],
            "data_path": parameters_list[5],
            "update_data_path": parameters_list[6],
            "storage_keys": parameters_list[7],
            "description": parameters_list[8],
            "copyright": parameters_list[9],
            "add_item_to_portal": parameters_list[10],
        }

    def setServiceDetails(self, params, services):
        action = params['action'].valueAsText
        folder = params['folder_name'].valueAsText
        folder = '' if folder == '[root]' else folder
        service_param = params['service_name']
        if services:
            try:
                if folder:
                    service_details = [
                      service for service in services if service['name'] == '/'.join([folder, service_param.valueAsText.split('(')[0]])][0]
                else:
                    service_details = [
                        service for service in services if service['name'] == service_param.valueAsText.split('(')[0]][0]
            except:
                return
            try:
                service_properties = json.loads(
                    service_details['service_properties']) or {}
            except:
                service_properties = {}
            if action == self.actions['update']:
                params['description'].value = service_properties.get(
                    'description')
                params['copyright'].value = service_properties.get('copyright')

    def enable_params_by_action(self, params, parameters):
        if params['action'].valueAsText == self.actions['delete']:
            self.enableParams([params['pod'], params['service_name'],
                               params['action'], params['folder_name']],
                              parameters)
        elif params['action'].valueAsText == self.actions['create']:
            self.enableParams(
                [params['new_service_name'], params['folder_name'],
                 params['description'], params['action'],
                 params['copyright'], params['data_path'],
                 params['pod'],
                 params['storage_keys'],
                 params['add_item_to_portal']],
                parameters)
            params['action'].filter.list = self.actions_list
        elif params['action'].valueAsText == self.actions['update']:
            self.enableParams(
                [params['service_name'], params['description'],
                 params['folder_name'], params['pod'],
                 params['update_data_path'], params['action'],
                 params['copyright']],
                parameters)

    def setDefaultParams(self, params, parameters):
        self.enableParams([params['service_name'], params['folder_name'],
                 params['description'], params['action'],
                 params['copyright'], params['service_package'],
                 params['pod'],
                 params['add_item_to_portal']], parameters)

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        global pods
        global pods_details
        global pods_services
        global pods_folders
        global errorMessages
        pythonScriptExecution = False
        params = self.mapParams(parameters)
        executable_path = sys.executable
        pod_type = 'ti'
        if executable_path.lower().endswith("python.exe"):
            pythonScriptExecution = True
        if pythonScriptExecution:
            description = params['description'].valueAsText
            copyright = params['copyright'].valueAsText
            data_path = params['data_path'].valueAsText
            folder_name = params['folder_name'].valueAsText
            service_name = params['service_name'].valueAsText
        try:
            token = arcpy.GetSigninToken()['token']
            errorMessages[0] = ''
        except Exception as e:
            self.setDefaultParams(params, parameters)
            errorMessages[0] = "Please sign in to continue"
            return
        try:
            gis = GIS("Pro")
            customer_id = gis.properties['id']
            username = gis.users.me.username
            errorMessages[0] = ''
        except:
            self.setDefaultParams(params, parameters)
            errorMessages[0] = "Please sign in to continue"
            return
        if not params["pod"].altered or pythonScriptExecution:
            pods_details = load_pods(username, pod_type)
            if pods_details:
                pod_alias = [pod['pod_alias'] for pod in pods_details]
            else:
                list_pods_response = utils.list_pods(token, customer_id, pod_type)
                pods_details = list_pods_response.get('pods')
                if pods_details != None:
                    pod_alias = [pod['pod_alias'] for pod in pods_details]
                    update_pods_details(pods_details, username, pod_type)
                    errorMessages[1] = ''
                else:
                    pod_alias = []
                    errorMessages[1] = "The API is temporarily not working. Please try after some time."
                    self.setDefaultParams(params, parameters)
                    if list_pods_response.get('error'):
                        errorMessages[1] = list_pods_response['error']['message']
                    return
            pods = pod_alias
            self.setFieldList(params, 'pod', pod_alias)
            if not params['pod'].value:
                self.setDefaultParams(params, parameters)
            pods_services = []
        if not params['action'].altered:
            params['action'].value = self.actions['create']
        if params['pod'].altered and not params['pod'].hasBeenValidated:
            if not pods_details:
                errorMessages[1] = "Either the token is invalid or user does not have access to AID"
                self.setDefaultParams(params, parameters)
                return
            if not params['action'].altered:
                params['action'].value = self.actions['create']
            pod = [pod for pod in pods_details if params['pod'].valueAsText == pod['pod_alias']][0]
            services_resp = utils.get_services(token, customer_id, pod['pod_id'],
                                               None)
            pods_services = services_resp.get('services')
            if pods_services != None:
                errorMessages[2] = ''
            else:
                errorMessages[2] = "The API is temporarily not working. Please try after some time."
                if services_resp.get('error'):
                    errorMessages[2] = services_resp['error']['message']
                self.setDefaultParams(params, parameters)
                return
            pods_folders = list(
                set(service['server_folder'] for service in pods_services if service['server_folder']))
            self.setFieldList(params, 'folder_name', pods_folders)
            self.enable_params_by_action(params, parameters)
        if params['folder_name'].altered and not params['folder_name'].hasBeenValidated:
            if params['action'].value == self.actions['create']:
                if params['folder_name'].valueAsText and params['folder_name'].valueAsText not in pods_folders:
                    pods_folders.append(params['folder_name'].valueAsText)
                    self.setFieldList(params, 'folder_name', pods_folders)
            try:
                service_names = ['{}({})'.format(service.get('name').split('/')[-1],service.get('type'))
                                 for service in pods_services
                                 if service['server_folder'] == params['folder_name'].valueAsText]
            except:
                service_names = []
            self.setFieldList(params, 'service_name', service_names)
        if params['service_name'].altered and not params['service_name'].hasBeenValidated:
            if params['action'].value != self.actions['create']:
                self.setServiceDetails(params, pods_services)
        if params['action'].altered and not params['action'].hasBeenValidated:
            self.enable_params_by_action(params, parameters)
            try:
                service_names = ['{}({})'.format(service.get('name').split('/')[-1],service.get('type')) for service in pods_services
                                 if service['server_folder'] == params['folder_name'].valueAsText]
            except:
                service_names = []
            self.setFieldList(params, 'service_name', service_names)
            self.setServiceDetails(params, pods_services)
        if not params['folder_name'].valueAsText:
            try:
                service_names = ['{}({})'.format(service.get('name').split('/')[-1],service.get('type')) for service in pods_services
                                 if service['server_folder'] == '[root]']
            except:
                service_names = []
            self.setFieldList(params, 'service_name', service_names)
        if pythonScriptExecution:
            if description:
                params['description'].value = description
            if copyright:
                params['copyright'].value = copyright
            if data_path:
                params['data_path'].value = data_path
            if service_name:
                params['service_name'].value = service_name
            if folder_name:
                folders = params['folder_name'].filter.list
                if folder_name not in folders:
                    folders.append(folder_name)
                    params['folder_name'].filter.list = folders
                params['folder_name'].value = folder_name

    def validateSpecialCharacters(self, param):
        if param.enabled:
            if param.altered and not param.hasBeenValidated:
                if not re.match("^[A-Za-z0-9_]*$", param.valueAsText):
                    param.setErrorMessage("The service name can contain only alpha numeric characters")
                else:
                    param.clearMessage()
            else:
                param.clearMessage()
        else:
            param.clearMessage()

    def validateExtension(self, param):
        if not param.valueAsText.endswith(TILE_PACKAGE_EXTENSIONS):
            param.setErrorMessage("The data should either be a tile package or scene layer package.")
        else:
            param.clearMessage()

    def validateNewService(self, pods_services, params, param):
        try:
            service_names = ['{}({})'.format(service.get('name').split('/')[-1], service.get('type')) for service in pods_services
                                 if service['server_folder'] == params['folder_name'].valueAsText]
        except:
            service_names = []
        if params['data_path'].value:
            ext = os.path.splitext(params['data_path'].valueAsText)[1]
            if ext:
                ext = ext.strip('.')
                if '{}({})'.format(param.valueAsText, ext) in service_names:
                    param.setErrorMessage("Service already exists in the selected folder.")
                else:
                    self.validateSpecialCharacters(param)

    def validateExistingService(self, pods_services, params, param):
        if params['action'].valueAsText == self.actions['delete']:
            try:
                service_names = ['{}({})'.format(service.get('name').split('/')[-1], service.get('type')) for service in pods_services
                                 if service['server_folder'] == params['folder_name'].valueAsText]
            except:
                service_names = []
            if param.valueAsText not in service_names:
                param.setErrorMessage("This service does not exist in this folder.")
            else:
                param.clearMessage()

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        global errorMessages
        global pods_services
        params = self.mapParams(parameters)
        new_service_param = params['new_service_name']
        service_param = params['service_name']
        data_param = params['data_path']
        update_data_param = params['update_data_path']
        for errorMessage in errorMessages:
            if errorMessage:
                parameters[0].setErrorMessage(errorMessage)
                return
        if all(not errorMessage for errorMessage in errorMessages):
            parameters[0].clearMessage()
        if new_service_param.altered and not new_service_param.hasBeenValidated\
           and new_service_param.enabled:
            self.validateNewService(pods_services, params, new_service_param)
        if service_param.value and service_param.enabled:
            self.validateExistingService(pods_services, params, service_param)
        if data_param.altered and not data_param.hasBeenValidated and data_param.enabled:
            self.validateExtension(data_param)
            self.validateNewService(pods_services, params, new_service_param)
        if update_data_param.altered and not update_data_param.hasBeenValidated and update_data_param.enabled:
            self.validateExtension(update_data_param)
        if new_service_param.value and new_service_param.enabled:
            self.validateNewService(pods_services, params, new_service_param)


    def execute(self, parameters, messages):
        log = initializeLog("MAIDTS")
        global pods
        global pods_details
        global pods_services
        global pods_folders
        try:
            params = self.mapParams(parameters)
            token = arcpy.GetSigninToken()['token']
            action = params['action'].valueAsText
            added_item_id = None
            customer_id = arcpy.GetPortalDescription()['id']
            new_service_param = params['new_service_name']
            service_param = params['service_name']
            if service_param.valueAsText:
                service_name = service_param.valueAsText.split('(')[0]
            data_param = params['data_path']
            update_data_param = params['update_data_path']
            folder = params['folder_name'].valueAsText
            item_params = None
            if folder and folder == '[root]':
                folder = ''
            try:
                service = [pods_service for pods_service in pods_services if pods_service.get('name').split('/')[-1] == service_name][0]
            except:
                service = {}
            pod = [pod for pod in pods_details if params['pod'].valueAsText in pod['pod_alias']][0]
            pod_id = pod.get('pod_id')
            pod_type = 'ti'
            imagery_uploaded = False
            log.Message("Action:{}".format(action),
                        log.const_general_text)
            data_path = data_param.valueAsText
            wait_time = 4
            short_action = action.split()[0].lower()
            action_verb = '{}{}ed'.format(short_action.lower().strip('e'),
                                          'p' if short_action.lower().endswith('p') else '')
            check_words = ['delete','stop']
            if any(word in action.lower() for word in check_words):
                success_message_template = 'The service has been {}.'
            else:
                success_message_template = 'The service has been {} and the service url is below. \n {}'
            failure_message = 'Could not {} the service.'.format(short_action)
            if action == self.actions['update']:
                data_path = update_data_param.valueAsText
            if action == self.actions['create']:
                wait_time = 34
                service_name = new_service_param.valueAsText.split('(')[0]
                description = params['description'].valueAsText
                service_params = {
                    "serviceName": service_name,
                    "description": description,
                    "copyright": params["copyright"].valueAsText,
                    "dataPath": data_path,
                    "folder": folder,
                    "storageKeys": params['storage_keys'].valueAsText
                }
                add_item_to_portal = params['add_item_to_portal'].value
                if add_item_to_portal:
                    folder_service = service_name
                    if folder:
                        folder_service = '{}/{}'.format(folder, service_name)
                    if data_param.valueAsText.endswith('.tpkx'):
                        service_type = 'MapServer'
                        portal_service_type = 'Map Service'
                        dns = '{}/arcgis'.format(pod.get('dns').strip('/'))
                    else:
                        service_type = 'SceneServer'
                        portal_service_type = 'Scene Service'
                        dns = pod.get('dns').strip('/')
                    service_url = ''.join([dns,
                                           '/rest/services/{}/{}'.format(
                                               folder_service, service_type)])
                    added_item_id = add_portal_item(service_name, description, service_url, log,
                                                    portal_service_type, service_type)
                    try:
                        if added_item_id:
                            item_params = {
                                                    "portal_token": arcpy.GetSigninToken()['token'],
                                                    "portal_username": arcpy.GetPortalDescription()[
                                                        'user']['username'],
                                                    "portal_url": arcpy.GetActivePortalURL(),
                                                    "id": added_item_id
                                                }
                    except Exception as e:
                        item_params = None
                log.Message("Service params:{}".format(
                    str(service_params)), log.const_general_text)
                resp_json = utils.create_service(
                    token, customer_id, pod_id, service_params, log, item_params)
            elif action == self.actions['update']:
                service_name = service_param.valueAsText.split('(')[0]
                service_params = {
                    "serviceName": service_name,
                    "description": params['description'].valueAsText,
                    "copyright": params["copyright"].valueAsText,
                    "dataPath": data_path,
                    "folder": folder,
                    "serviceID": service['service_id']
                }
                log.Message("Service params:{}".format(
                    str(service_params)), log.const_general_text)
                resp_json = utils.update_service(token, customer_id, pod_id,
                                                 service_name,
                                                 service_params,
                                                 False,
                                                 log)
            elif action == self.actions['delete']:
                wait_time = 14
                resp_json = utils.delete_service(token, customer_id, pod_id,
                                                 service_name,
                                                 folder,
                                                 service['service_id'],
                                                 False,
                                                 log)
            job_id = resp_json.get('jobID')
            log.Message('API response:{}'.format(resp_json), log.const_general_text)
            if not job_id:
                arcpy.AddError('{}. Please check the logs for more details'.format(failure_message))
                closeLog(log)
                return
            time.sleep(wait_time)
            arcpy.AddMessage('------------------------------------------------------')
            arcpy.AddMessage("Job id: {}".format(job_id))
            log.Message("Job id:".format(job_id), log.const_general_text)
            list_pods_response = utils.list_pods(token, customer_id, '*')
            pods = list_pods_response.get('pods')
            pod_dns = [pod.get('dns')
                       for pod in pods if pod['pod_id'] == pod_id]
            dns = ''
            if pod_dns:
                dns = pod_dns[0].strip('/')
            if pods:
                pod_ids = [pod['pod_id'] for pod in pods]
            else:
                pod_ids = []
            pods = pod_ids
            services_resp = utils.get_services(token, customer_id, pod_id,
                                               None)
            pods_services = services_resp.get('services')
            pods_folders = list(
                set(service['server_folder'] for service in pods_services))
            status_response = utils.get_job_status(
                token, customer_id, pod_id, job_id, log)

            jobs = status_response.get('jobs')
            job_status = [job['job_status']
                          for job in jobs if job['job_id'] == job_id]
            job_result = [job.get('job_result') for job in jobs if (
                job['job_id'] == job_id and job.get('job_result'))]
            if job_status:
                if job_status[0].lower() == 'success':
                    if job_result:
                        arcpy.AddMessage(success_message_template.format(action_verb,
                                                                     job_result[0].format(dns)))
                    else:
                        arcpy.AddMessage(success_message_template.format(action_verb))
                    if added_item_id:
                        arcpy.AddMessage("Added item id is: {}".format(str(added_item_id)))
                elif job_status[0].lower() == 'failed':
                    arcpy.AddMessage(failure_message)
                    if job_result and '{}' not in job_result[0]:
                        arcpy.AddMessage("Error: {}".format(job_result[0]))
                else:
                    additional_message = 'Please check Get Job Status Tool for more info.'
                    arcpy.AddMessage("{} service status: {}. {}".format(short_action,
                                                                        job_status[0],
                                                                        additional_message))
            arcpy.AddMessage('------------------------------------------------------')
            closeLog(log)
        except Exception as e:
            arcpy.AddError("Error in manage image services")
            log.Message("Error in manage image services {}".format(
                str(e)), log.const_critical_text)
            closeLog(log)


class AIDISDP(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create AID Image Service Definition Package"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_data = arcpy.Parameter(displayName="Input Mosaic Dataset / Raster Dataset",
                                     name="input_data",
                                     datatype=["DEMosaicDataset", "DERasterDataset",
                                               "DEFile"],
                                     parameterType="Required",
                                     direction="Input",
                                     enabled=True)
        service_package = arcpy.Parameter(displayName="AID Image Service Definition package",
                                        name="service_package",
                                        datatype="DEFile",
                                        parameterType="Required",
                                        direction="Output",
                                        enabled=True)
        service_package.filter.list = ['zmd']
        service_additional_properties = arcpy.Parameter(
                                        displayName="Service additional properties",
                                        name="service_additional_properties",
                                        datatype="DEFile",
                                        parameterType="Optional",
                                        direction="Input",
                                        enabled=False)
        output_path = arcpy.Parameter(displayName="Output Path",
                                      name="output_path",
                                      datatype="GPString",
                                      parameterType="Derived",
                                      direction="Output")
        params = [input_data, service_package, service_additional_properties, output_path]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def mapParams(self, parameters):
        params = {
            "input_data": parameters[0],
            "service_package": parameters[1],
            "service_additional_properties": parameters[2],
            "output_path": parameters[3]
        }
        return params

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        pass

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        params = self.mapParams(parameters)
        if params['service_additional_properties'].altered and not \
           params['service_additional_properties'].hasBeenValidated:
            path = params['service_additional_properties'].valueAsText
            if not path.endswith('.json'):
                params['service_additional_properties'].setErrorMessage("Only json files are supported!")
            elif self.get_additional_properties_json(path) == {}:
                params['service_additional_properties'].setErrorMessage("Please check if the input file is of valid format.")
            else:
                params['service_additional_properties'].clearMessage()
        else:
            params['service_additional_properties'].clearMessage()
        if params['service_package'].altered and not params['service_package'].hasBeenValidated:
            if not params['service_package'].valueAsText.endswith(".zmd"):
                params['service_package'].setErrorMessage("Output file should end with .zmd")
            else:
                params["service_package"].clearMessage()

    def get_additional_properties_json(self, path):
        try:
            with open(path) as f:
                try:
                    additional_properties = json.load(f)
                except:
                    additional_properties = {}
            return additional_properties
        except Exception as e:
            return {}

    def execute(self, parameters, messages):
        log = initializeLog('CreateAIDImageServiceDefinitionPackage')
        try:
            params = self.mapParams(parameters)
            input_data = params['input_data'].valueAsText
            output_file = params['service_package'].valueAsText
            data_type = get_data_type(input_data)
            pixel_cache_location = None
            unzipped_folder_path = os.path.splitext(output_file)[0]
            if data_type['type'] == 'mosaic':
                log.Message("input is Mosaic Dataset",log.const_general_text)
                md_tools_exe = os.path.join(arcpy.GetInstallInfo()['InstallDir'],'bin',
                                            'mdtools.exe')
                if not os.path.exists(md_tools_exe):
                    arcpy.AddError("MDTools does not exist. Install MDTools from https://github.com/Esri/mdcs-py/raw/master/MDTools_Setup.zip")
                    log.Message("MDTools does not exist. Install MDTools from https://github.com/Esri/mdcs-py/raw/master/MDTools_Setup.zip", log.const_critical_text)
                    arcpy.SetParameter(parameters.index(params['output_path']), "")
                    closeLog(log)
                    return False
                raster = arcpy.Raster(input_data, True)
                pixel_cache_location = raster.properties.get('PixelCacheLocation')
                in_wks_name = data_type['wks_name']
                md_name = data_type['name']
                if not os.path.exists(unzipped_folder_path):
                    os.mkdir(unzipped_folder_path)
                log.Message("Copying data to temp path",log.const_general_text)
                in_wks_name = '{}_{}{}'.format(os.path.splitext(in_wks_name)[0],
                                          datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                                          os.path.splitext(in_wks_name)[1])
                cp = copy_mosaic(input_data,in_wks_name,unzipped_folder_path,md_name,log)
                if cp:
                    input_data = os.path.join(unzipped_folder_path,
                                           in_wks_name,
                                           md_name)
                else:
                    if os.path.exists(unzipped_folder_path):
                        shutil.rmtree(unzipped_folder_path)
                    arcpy.SetParameter(parameters.index(params['output_path']), "")
                    closeLog(log)
                    return
                paths = get_all_raster_paths_mdtools(input_data, log)
                if not paths:
                    arcpy.AddError("No rasters found in the mosaic")
                    log.Message("No rasters found in the mosaic", log.const_general_text)
                    if os.path.exists(unzipped_folder_path):
                        shutil.rmtree(unzipped_folder_path)
                    arcpy.SetParameter(parameters.index(params['output_path']), "")
                    closeLog(log)
                    return
                drives = []
                i= 0
                num_path = len(paths)
                for path in paths:
                    if len(path) == 0:
                        continue
                    if path.startswith(CLOUD_PATH_PREFIXES):
                        i = i + 1
                    drive = get_drive_letter(path)
                    if drive:
                        drives.append(drive)
                if num_path != i:
                    drives = set(drives)
                    if drives:
                        log.Message("Replacing paths using mdtools", log.const_general_text)
                    if len(drives) > 0:
##                        log.Message("All local drives:{}".format("driveexist"),
##                                log.const_general_text)
                        for drive in drives:
                            replace_paths(input_data, drive, r'z:\mrfcache', log)
                    paths = get_all_raster_paths_mdtools(input_data, log)
                    if not paths:
                        arcpy.SetParameter(parameters.index(params['output_path']), "")
                        closeLog(log)
                        return
                    for path in paths:
                        path_valid, message = validate_path(path)
                        if not path_valid:
                            arcpy.AddError("Invalid path. {}: {}".format(message, path))
                            log.Message("Invalid path. {}: {}".format(message, path),
                                        log.const_critical_text)
                            if os.path.exists(unzipped_folder_path):
                                shutil.rmtree(unzipped_folder_path)
                            arcpy.SetParameter(parameters.index(params['output_path']), "")
                            closeLog(log)
                            return
                        if path.startswith(CLOUD_PATH_PREFIXES):
                            arcpy.AddWarning("There won't be any caching for the raster {} and there may be a drop in performance".format(
                                path))
                            log.Message("There won't be any caching for the raster {} and there may be a drop in performance".format(
                                path), log.const_warning_text)

            elif (data_type['type'] == 'cloudraster'):
                log.Message("cloud raster", log.const_general_text)

            else:
                if data_type['format'] == 'MRF':
                    log.Message("input data is MRF",log.const_general_text)
                    outmrf = mrfstring(input_data)
                    path_valid, message = validate_path(outmrf)
                    if not path_valid:
                        arcpy.AddError("Invalid path. {}: {}".format(message, input_data))
                        log.Message("Invalid path. {}: {}".format(message, input_data),
                                log.const_critical_text)
                        if os.path.exists(unzipped_folder_path):
                            shutil.rmtree(unzipped_folder_path)
                        closeLog(log)
                        arcpy.SetParameter(parameters.index(params['output_path']), "")
                        return
                else:
                    log.Message("Invalid format. {}: {}".format(data_type['format'], input_data),
                                log.const_critical_text)
                    if os.path.exists(unzipped_folder_path):
                        shutil.rmtree(unzipped_folder_path)
                    arcpy.SetParameter(parameters.index(params['output_path']), "")
                    closeLog(log)
                    return
            dtype = data_type['dtype']
            log.Message("Creating Zip Package",log.const_general_text)
            additional_properties = None
            if params['service_additional_properties'].valueAsText:
                additional_properties = self.get_additional_properties_json(
                    params['service_additional_properties'].valueAsText)
            local_zip_file = create_zip(input_data, unzipped_folder_path,
                                        dtype, additional_properties, log)
            arcpy.AddMessage("Zip file path-{}".format(local_zip_file))
            delete_exported_mosaic_json(input_data)
            if os.path.exists(unzipped_folder_path):
                shutil.rmtree(unzipped_folder_path)
            arcpy.SetParameter(parameters.index(params['output_path']), local_zip_file)
            closeLog(log)
        except Exception as e:
            arcpy.AddError('Error in package mosaic dataset. '
                             'Please check the logs for details')
            log.Message("Error in package mosaic dataset.{}".format(str(e)),
                        log.const_critical_text)
            arcpy.SetParameter(parameters.index(params['output_path']), "")
            closeLog(log)