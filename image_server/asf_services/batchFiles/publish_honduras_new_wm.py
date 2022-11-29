# This script generates the batch files for the three services generated from the watermap products
# then runs them in sequence

import datetime
import os
import subprocess
import keyring

import arcpy

os.chdir(r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\batchFiles')

today = datetime.datetime.now(datetime.timezone.utc).strftime("%y%m%d_%H%M")
s3tag = r'Honduras\New_WM'
projtag = 'Honduras'
crftag_wm = projtag+'_WatermapExtentNEW'
scratch_ws = r"C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\scratch\
ImageServerScratch.gdb"

genvars = [r'set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"',
           r'set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services',
           r'set cachepath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services'
           r'\PixelCache']

vars = [r'set gdbwks=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD''\\'
        +projtag+'\\'+projtag+'_'+today+'.gdb',
        r'set acspath=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs''\\',
        r'set s3tag='+s3tag]

crf_wm = r'set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri''\\'\
         +crftag_wm+'_'+today+'.crf'

batfile_wm = 'Honduras_wm_new.bat'

vars_wm = [r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_mosaic_nozeros.xml '
           r'-m:%gdbwks%\watermap_extent -s:%acspath%%s3tag%\ -p:%cachepath%\$cachelocation '
           r'-p:USE_PIXEL_CACHE$pixelcache -p:%s3tag%$stag -c:CM+AF+AR+UpdateFieldsWM+BF+BB+SP+CC',
           r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_nozeros_overviews.xml '
           r'-m:%gdbwks%\watermap_extent -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf']

batfiles = [batfile_wm]

for bat in batfiles:
    with open(bat, 'w') as f:
        # write general reference variables
        for gv in genvars:
            print(gv, file=f)
        print('\nREM ---------- Set output gdb and source s3 bucket-----', file=f)
        # write gdb output and acs connection specifications
        for v in vars:
            print(v, file=f)
        # write the service-specific variables and batch commands
        if bat == 'Honduras_wm_new.bat':
            print(crf_wm, file=f)
            print('\nREM ---------- Using ACS File -------------------------', file=f)
            for vb in vars_wm:
                print(vb, file=f)
        else:
            print('No valid file.')

# run the batch files

subprocess.call([batfile_wm])
print('Watermap Extent mosaic dataset complete.')

# create AID packages
aid_path = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\AID''\\'+projtag
arcpy.ImportToolbox(r"C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\AID"
                    r"\AID_GPtools\AID_Management.pyt")
gdb = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD''\\'\
        +projtag+'\\'+projtag+'_'+today+'.gdb'

print('Generating watermap extent AID package...')
md_wm = gdb+'\\'+'watermap_extent'
aid_wm = aid_path+'\\'+projtag+'_WatermapExtent_'+today+'.zmd'

with arcpy.EnvManager(scratchWorkspace=scratch_ws, workspace=scratch_ws):
    try:
        arcpy.AID.AIDISDP(md_wm, aid_wm, None)
    except:
        print("AID errors generated and ignored.")
        pass
print('Watermap extent AID package complete.')

#  create/update image services
pw = keyring.get_password("portal_creds", "hkristenson_ASF")
arcpy.SignInToPortal(r'https://asf-daac.maps.arcgis.com/', 'hkristenson_ASF', pw)

credit_statement = "Products processed by ASF DAAC HyP3 2022 using GAMMA software. " \
                   "Contains modified Copernicus Sentinel data 2020-2021, processed by ESA."

# generate watermap extent service
service_desc = "**TEST OF WATERMAP EXTENT PRODUCT IN A REGION OTHER THAN WHERE IT WAS VALIDATED** Watermap Extent " \
               "products generated from Sentinel-1 SAR imagery over an AOI in Honduras from April 15, 2020 to " \
               "April 15, 2021, processed by ASF. Areas identified as water have a pixel value of 1, all other " \
               "pixels have a value of 0."

# print('Updating Watermap Extent Image Service...')
# arcpy.AID.MAIDIS("asf-daac", "Update Service", "test", "None", "Honduras_WM", None, aid_wm, "Dedicated Instance",
#                  service_desc, credit_statement, '', False, False, True, None, None, None, None)
# print('Watermap Extent Image Service updated.')

print('Creating Watermap Extent Image Service...')
arcpy.AID.MAIDIS("asf-daac", "Create Service", "test", "Honduras_WM_NEW", '', aid_wm, None, "Dedicated Instance",
                 service_desc, credit_statement, '', False, False, True, None, None, None, None)
print('Watermap Extent Image Service created.')


