# ------------------------------------------------------------------------------
# Copyright 2018 Esri
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
# Name: cis_utils.py
# Description: Utility class for ACIS GPTools
# Version: 20200520
# Requirements: python.exe 3.6, solutionlog
# Required Arguments: N/A
# Optional Arguments: N/A
# Usage:
# Author: Esri Imagery Workflows Team
# ------------------------------------------------------------------------------
import json
import requests

API_URL = 'https://aid-aws-api.img.arcgis.com'

def get_supported_environments(token, pod_input_type):
    try:
        pod_type = 'DynamicImagery'
        if 'tiled' in pod_input_type.lower():
            pod_type = 'TiledImagery'
        params = {"token": token, "podType": pod_type}
        resp = requests.get('{}/supportedenvironments'.format(API_URL), params)
        respJSON = resp.json()
        return respJSON
    except Exception as e:
        return {'supportedEnvs': []}


def delete_pod(token, pod_id, customer_id, log):
    try:
        params = {"token": token, "podID": pod_id, "customerID": customer_id}
        resp = requests.post('{}/deletepod'.format(API_URL), json.dumps(params))
        respJSON = resp.json()
        log.Message("Delete pod API response: {}".format(
            str(respJSON)), log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in delete pod API. {}".format(str(e)),
                    log.const_critical_text)


def get_job_status(token, customer_id, pod_id, job_id, log):
    try:
        params = {"token": token, "customerID": customer_id,
                  "podID": pod_id, "jobID": job_id}
        resp = requests.get('{}/jobinfo'.format(API_URL), params)
        respJSON = resp.json()
        log.Message("Get job status API response: {}".format(
            str(respJSON)), log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in get job status API. {}".format(str(e)),
                    log.const_critical_text)


def create_pod(token, customer_id, pod_input_type, instance_type, cloud_type,
               region, data_bucket, log_bucket, storage_keys, min_instances,
               max_instances, item_id, dns, log, alias=None):
    try:
        pod_type = 'DynamicImagery'
        if 'tiled' in pod_input_type.lower():
            pod_type = 'TiledImagery'
        params = {"token": token,
                  "customerID": customer_id,
                  "pod": {
                             "type": pod_type,
                             "dataBucket": data_bucket,
                             "instanceType": instance_type,
                             "cloudType": cloud_type,
                             "region": region,
                             "logBucket": log_bucket,
                             "storageKeys": storage_keys,
                             "minInstances": min_instances,
                             "maxInstances": max_instances,
                             "itemID": item_id,
                             "dns": dns,
                             "alias": alias
                         }}
        log.Message("Create pod request:{}".format(str(params)), log.const_general_text)
        resp = requests.post('{}/createpod'.format(API_URL), json.dumps(params))
        respJSON = resp.json()
        log.Message("Create pod API response {}".format(str(respJSON)),
                    log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in create pod API. {}".format(str(e)),
                    log.const_critical_text)


def list_pods(token, customer_id, pod_type):
    try:
        params = {"token": token,
                  "customerID": customer_id,
                  "podType": pod_type}
        resp = requests.get('{}/podinfo'.format(API_URL), params)
        respJSON = resp.json()
        return respJSON
    except Exception as e:
        return {'pods': []}


def list_jobs(token, customer_id, pod_id, user_jobs=True):
    try:
        params = {"token": token, "customerID": customer_id,
                  "podID": pod_id, 'jobID': '*', 'userJobs': user_jobs}
        resp = requests.get('{}/jobinfo'.format(API_URL), params)
        respJSON = resp.json()
        return respJSON
    except Exception as e:
        return {'jobs': []}

def get_cloudstore(token, customer_id, pod_id):
    try:
        params = {"token": token, "customerID": customer_id,
                  "podID": pod_id}
        resp = requests.get('{}/cloudstore'.format(API_URL), params)
        respJSON = resp.json()
        return respJSON
    except Exception as e:
        return {'cloudStore': ""}


def create_service(token, customer_id, pod_id, service_params, log,
                   item_params=None):
    try:
        if service_params.get('folder') and service_params['folder'] == '[root]':
            service_params['folder'] = ''
        params = {"token": token,
                  "customerID": customer_id,
                  "podID": pod_id,
                  "service": service_params,
                  "item": {}
                  }
        if item_params:
            params['item'] = item_params
        log.Message(str(params), log.const_general_text)
        resp = requests.post('{}/createservice'.format(API_URL),
                             json.dumps(params))
        respJSON = resp.json()
        log.Message("Create service API response {}".format(str(respJSON)),
                    log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in create service API. {}".format(str(e)),
                    log.const_critical_text)


def update_service(token, customer_id, pod_id, service_name, service_params,
                   delete_source, log, item_params=None):
    try:
        params = {"token": token,
                  "customerID": customer_id,
                  "podID": pod_id,
                  "service": service_params,
                  "item": {},
                  "deleteSource": delete_source
                  }
        log.Message(str(params), log.const_general_text)
        resp = requests.post('{}/updateservice'.format(API_URL),
                             json.dumps(params))
        respJSON = resp.json()
        log.Message("Update service API response {}".format(str(respJSON)),
                    log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in update service API. {}".format(str(e)),
                    log.const_critical_text)


def delete_service(token, customer_id, pod_id, service_name, folder,
                   service_id, delete_source, log):
    try:
        params = {"token": token,
                  "customerID": customer_id,
                  "podID": pod_id,
                  "serviceName": service_name,
                  "folder": folder,
                  "deleteSource": delete_source,
                  "serviceID": service_id
                  }
        log.Message(str(params), log.const_general_text)
        resp = requests.post('{}/deleteservice'.format(API_URL),
                             json.dumps(params))
        respJSON = resp.json()
        log.Message("Delete service API response {}".format(str(respJSON)),
                    log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in delete service API. {}".format(str(e)),
                    log.const_critical_text)


def start_stop_service(token, customer_id, pod_id, service_name,
                       folder, service_id, log, start_service=True):
    try:
        endpoint = 'stopservice'
        if start_service:
            endpoint = 'startservice'
        params = {"token": token,
                  "customerID": customer_id,
                  "podID": pod_id,
                  "serviceName": service_name,
                  "folder": folder,
                  "serviceID": service_id
                  }
        log.Message(str(params), log.const_general_text)
        resp = requests.post('{}/{}'.format(API_URL, endpoint),
                             json.dumps(params))
        respJSON = resp.json()
        log.Message("{} API response {}".format(endpoint, str(respJSON)),
                    log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in {} API. {}".format(endpoint, str(e)),
                    log.const_critical_text)


def update_permission_service(token, customer_id, pod_id, service_name,
                       folder, service_id, log, enabled_users, disabled_users):
    try:
        params = {"token": token,
                  "customerID": customer_id,
                  "podID": pod_id,
                  "serviceName": service_name,
                  "folder": folder,
                  "serviceID": service_id,
                  "enabled_users": enabled_users,
                  "disabled_users": disabled_users
                  }
        log.Message(str(params), log.const_general_text)
        resp = requests.post('{}/updatepermission'.format(API_URL),
                             json.dumps(params))
        respJSON = resp.json()
        log.Message("{} API response {}".format('{}/updatepermission'.format(API_URL), str(respJSON)),
                    log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in {} API. {}".format(endpoint, str(e)),
                    log.const_critical_text)


def get_folders(token, customer_id, pod_id, folder, response_type, log):
    try:
        params = {"token": token,
                  "customerID": customer_id,
                  "folder": folder,
                  "podID": pod_id,
                  "type": response_type}
        log.Message(str(params), log.const_general_text)
        resp = requests.get('{}/folderinfo'.format(API_URL), params)
        respJSON = resp.json()
        log.Message("Get folders API response {}".format(str(respJSON)),
                    log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in get folders API. {}".format(str(e)),
                    log.const_critical_text)


def get_services(token, customer_id, pod_id, folder_name,
                 service_id='*', response_type='detailed'):
    try:
        params = {"token": token,
                  "customerID": customer_id,
                  "podID": pod_id,
                  "serviceID": service_id,
                  "type": response_type}
        if folder_name:
            params.update({"serviceFolder": folder_name})
        resp = requests.get('{}/serviceinfo'.format(API_URL), params)
        respJSON = resp.json()
        return respJSON
    except Exception as e:
        return {'services': []}

def get_presigned_url(token, customer_id, pod_id, file_name,
                      file_size, log):
    try:
        params = {
                      "token": token,
                      "customerID": customer_id,
                      "podID": pod_id,
                      "imageryFileName": file_name,
                      'fileSize': file_size
                 }
        log.Message(str(params), log.const_general_text)
        resp = requests.get('{}/uploadimagery'.format(API_URL), params)
        respJSON = resp.json()
        log.Message("Get presigned URL API response {}".format(str(respJSON)),
                    log.const_general_text)
        return respJSON
    except Exception as e:
        log.Message("Error in get presigned URL API. {}".format(str(e)),
                    log.const_critical_text)


def upload_imagery(input_file, presigned_url, fields, log):
    try:
        with open(input_file, 'rb') as f:
            files = {'file': (input_file, f)}
            log.Message(str(fields), log.const_general_text)
            http_response = requests.post(presigned_url, data=fields, files=files)
            log.Message("Upload imagery response status_code:{}".format(
            http_response.status_code), log.const_general_text)
            if http_response.status_code == 200 or http_response.status_code == 204:
                return True
        return False
    except Exception as e:
        log.Message("Error in upload imagery {}".format(str(e)),
                    log.const_critical_text)
        return False

def get_users(token, customer_id, pod_id):
    try:
        params = {
                      "token": token,
                      "customerID": customer_id,
                      "podID": pod_id
                 }
        resp = requests.get('{}/getuser'.format(API_URL), params)
        respJSON = resp.json()
        return respJSON
    except Exception as e:
        return []
