# This script generates the batch files for the three services generated from the watermap products
# then runs them in sequence

import datetime
import keyring
import os
import subprocess

import arcpy

os.chdir(r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\batchFiles')

# enter the name of the service to generate
service = 'COP30_HAND'
# enter the description of the service
service_desc = "Height Above Nearest Drainage (HAND) is a terrain model that normalizes topography to the relative " \
               "heights along the drainage network and is used to describe the relative soil gravitational potentials " \
               "or the local drainage potentials. Each pixel value represents the vertical distance to the nearest " \
               "drainage. The HAND data provides near-worldwide land coverage at 30 meters and was produced from " \
               "the 2021 release of the Copernicus GLO-30 Public DEM as distributed in the Registry of Open Data on " \
               "AWS (https://registry.opendata.aws/copernicus-dem/) using the the ASF Tools Python Package " \
               "(https://hyp3-docs.asf.alaska.edu/tools/asf_tools_api/#asf_tools.hand.calculate) and the PySheds " \
               "Python library (https://github.com/mdbartos/pysheds). The HAND data are provided as a tiled set of " \
               "Cloud Optimized GeoTIFFs (COGs) with 30-meter (1 arcsecond) pixel spacing. The COGs are organized " \
               "into the same 1 degree by 1 degree grid tiles as the GLO-30 DEM, and individual tiles are " \
               "pixel-aligned to the corresponding COG DEM tile."
# enter the credit description for the service
credit_statement = "Copyright 2022 Alaska Satellite Facility (ASF). Produced using the Copernicus WorldDEM(TM)-30 " \
                   "(c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 provided under " \
                   "COPERNICUS by the European Union and ESA; all rights reserved. The use of the HAND data falls " \
                   "under the terms and conditions of the Creative Commons Attribution 4.0 " \
                   "International Public License."
# select one of the two publishing type options:
# publish_type = 'create'
publish_type = 'update'

today = datetime.datetime.now(datetime.timezone.utc).strftime("%y%m%d_%H%M")
s3tag = r'v1/2021'

md_config = service + '.xml'
ovr_config = service + '_ovr.xml'

scratch_ws = r"C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\scratch\
ImageServerScratch.gdb"

# set general variables for the batch file
gdb = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD''\\' + service + '\\' \
      + service + '_' + today + '.gdb'
md = gdb + '\\' + service

genvars = [r'set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"',
           r'set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services',
           r'set cachepath=G:\Projects\2209_ImageServices\ImageServices\PixelCache']

vars = [r'set gdbwks=' + gdb,
        r'set acspath=G:\Projects\2209_ImageServices\ImageServices\COP30_HAND.acs''\\',
        r'set s3tag=' + s3tag,
        r'set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri''\\'
        + service + '_' + today + '.crf'
        ]

md_cmd = r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\' + md_config + r' -m:%gdbwks%\\' \
         + service + r' -s:%acspath%%s3tag%\ -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache ' \
         r'-c:CM+AF+AR+UpdateFieldsHAND+BF+BB+SP+CC'
ovr_cmd = r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\' + ovr_config + r' -m:%gdbwks%\\' \
          + service + r' -s:%outcrf% -c:SE+CRA+AR+UpdateHANDOverviewFields -p:%outcrf%$outcrf'

# generate batch file
batfile = service + '.bat'

with open(batfile, 'w') as f:
    # write general reference variables
    for gv in genvars:
        print(gv, file=f)
    print('\nREM ---------- Set output gdb and source s3 bucket-----', file=f)
    # write gdb output specifications
    for v in vars:
        print(v, file=f)
    # write the service-specific variables and batch commands
    print('\nREM ---------- Using ACS File -------------------------', file=f)
    print(md_cmd, file=f)
    print(ovr_cmd, file=f)

# run the batch files
subprocess.call(batfile)
print('{} mosaic dataset complete.'.format(service))

# create AID packages
aid_path = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\AID''\\' + service
arcpy.ImportToolbox(r"C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\AID"
                    r"\AID_GPtools\AID_Management.pyt")

print('Generating {} AID package...'.format(service))
aid = aid_path + '\\' + service + '_' + today + '.zmd'

with arcpy.EnvManager(scratchWorkspace=scratch_ws, workspace=scratch_ws):
    try:
        arcpy.AID.AIDISDP(md, aid, None)
    except:
        print("AID errors generated and ignored.")
        pass
print('{} AID package complete.'.format(service))

# portal login
pw = keyring.get_password("portal_creds", "hkristenson_ASF")
arcpy.SignInToPortal(r'https://asf-daac.maps.arcgis.com/', 'hkristenson_ASF', pw)

# publish service
if publish_type == 'create':
    # create image service
    print('Generating {} Image Service...'.format(service))
    arcpy.AID.MAIDIS("asf-daac", "Create Service", "GlobalHAND", service, '', aid, None, "Dedicated Instance",
                     service_desc, credit_statement, '', False, False, True, None, None, None, None)
    print('{} Image Service published.'.format(service))
elif publish_type == 'update':
    # update image services
    print('Updating {} Image Service...'.format(service))
    arcpy.AID.MAIDIS("asf-daac", "Update Service", "GlobalHAND", "None", service, None, aid, "Dedicated Instance",
                     service_desc, credit_statement, '', False, False, True, None, None, None, None)
else:
    print('No valid publish type designated')
