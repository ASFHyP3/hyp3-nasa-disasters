# This script generates a batch file, runs it, and publishes the MD to a GSSICB image service

import datetime
import keyring
import os
import subprocess

import arcpy

today = datetime.date.today().strftime("%d %B %Y")

# enter the name of the service to generate
service = 'COH12_VV_SON_France'
# enter the description of the service
service_desc = "Fall (September/October/November) median COH12 (12-day coherence) in VV polarization over France " \
               "from the Global Seasonal Sentinel-1 Interferometric Coherence and Backscatter Data Set " \
               "(https://registry.opendata.aws/ebd-sentinel-1-global-coherence-backscatter/)"
# enter the credit description for the service
credit_statement = "Global Seasonal Sentinel-1 Interferometric Coherence and Backscatter Data Set was accessed on " \
                   "{} from https://registry.opendata.aws/ebd-sentinel-1-global-coherence-backscatter.".format(today)
# select one of the two publishing type options:
# publish_type = 'create'
publish_type = 'update'

print('Starting process to {} the {} service...'.format(publish_type, service))

os.chdir(r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\batchFiles')

today = datetime.datetime.now(datetime.timezone.utc).strftime("%y%m%d_%H%M")
projtag = 'GSSICB'
md_config = service+'.xml'
ovr_config = service+'_ovr.xml'
scratch_ws = r"C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\scratch\
ImageServerScratch.gdb"

# set general variables for the batch file
gdb = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD''\\'+projtag+'\\'+projtag+'_'+service+'_'+today+'.gdb'
md = gdb+'\\'+service

genvars = [r'set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"',
           r'set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services',
           r'set cachepath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services'
           r'\PixelCache']

vars = [r'set gdbwks='+gdb,
        r'set outcrf=G:\Projects\2209_ImageServices\ImageServices\NASA_Disasters_AWS.acs\esri''\\'
        +projtag+'_'+service+'_'+today+'.crf']

md_cmd = r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\'+md_config+r' -m:%gdbwks%\\'+service+\
         r' -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+UpdateFieldsCoh+BF+BB+SP+CC'
ovr_cmd = r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\'+ovr_config+r' -m:%gdbwks%\\'+service+\
          r' -s:%outcrf% -c:SE+CRA+AR+UpdateCohOverviewFields -p:%outcrf%$outcrf'

# generate batch file
batfile = service+'.bat'

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
aid_path = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\AID''\\'+projtag
arcpy.ImportToolbox(r"C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\AID"
                    r"\AID_GPtools\AID_Management.pyt")

print('Generating {} AID package...'.format(service))
aid = aid_path+'\\'+projtag+'_'+service+'_'+today+'.zmd'

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
    arcpy.AID.MAIDIS("asf-daac", "Create Service", "GSSICB", service, '', aid, None, "Dedicated Instance", service_desc,
                     credit_statement, '', False, False, True, None, None, None, None)
    print('{} Image Service published.'.format(service))
elif publish_type == 'update':
    # update image services
    print('Updating {} Image Service...'.format(service))
    arcpy.AID.MAIDIS("asf-daac", "Update Service", "GSSICB", "None", service, None, aid, "Dedicated Instance",
                     service_desc, credit_statement, '', False, False, True, None, None, None, None)
else:
    print('No valid publish type designated')
