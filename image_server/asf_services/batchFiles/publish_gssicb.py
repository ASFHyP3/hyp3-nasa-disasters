# This script generates a batch file, runs it, and publishes the MD to a GSSICB image service

import datetime
import keyring
import os
import subprocess

import arcpy

# enter the name of the service to generate
service = 'COH12_VV_JJA_sample'
# enter the description of the service
service_desc = "Enter a description of the service"

os.chdir(r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\batchFiles')

today = datetime.datetime.now(datetime.timezone.utc).strftime("%y%m%d_%H%M")
projtag = 'GSSICB'
md_config = service+'.xml'
ovr_config = service+'_ovr.xml'
scratch_ws = r"C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\scratch\
ImageServerScratch.gdb"

# set general variables for the batch file
genvars = [r'set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"',
           r'set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services',
           r'set cachepath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services'
           r'\PixelCache']
gdb = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD''\\'+projtag+'\\'+projtag+'_'+service+'_'+today+'.gdb'
md = gdb+'\\'+service

vars = [r'set gdbwks='+gdb,
        r'set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri''\\'
        +projtag+'_'+service+'_'+today+'.crf']

md_cmd = r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\'+md_config+r' -m:%gdbwks%\\'+service+r' -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+UpdateFieldsCoh+BF+BB+SP+CC'
ovr_cmd = r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\'+ovr_config+r' -m:%gdbwks%\\'+service+r' -s:%outcrf% -c:SE+CRA+AR+UpdateCohOverviewFields -p:%outcrf%$outcrf'

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

# update image services
pw = keyring.get_password("portal_creds", "hkristenson_ASF")
arcpy.SignInToPortal(r'https://asf-daac.maps.arcgis.com/', 'hkristenson_ASF', pw)

print('Generating {} Image Service...'.format(service))
arcpy.AID.MAIDIS("asf-daac", "Create Service", "test", service, '', aid, None, "Dedicated Instance", service_desc,
                 "Credits for the GSSICB images", '', False, False, True, None, None, None, None)
print('{} Image Service updated.'.format(service))