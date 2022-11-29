# This script generates the batch files for the three services generated from the watermap products
# then runs them in sequence

import datetime
import os
import subprocess
import keyring

import arcpy

os.chdir(r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\batchFiles')

today = datetime.datetime.now(datetime.timezone.utc).strftime("%y%m%d_%H%M")
s3tag = 'Honduras'
projtag = 'Honduras'
crftag_wm = projtag+'_WatermapExtent'
crftag_rgb = projtag+'_RGB'
crftag_rtc = projtag+'_RTC'
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
crf_rgb = r'set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri''\\'\
          +crftag_rgb+'_'+today+'.crf'
crf_rtc = r'set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri''\\'\
          +crftag_rtc+'_'+today+'.crf'

batfile_wm = 'Honduras_wm.bat'
batfile_rgb = 'Honduras_rgb.bat'
batfile_rtc = 'Honduras_rtc.bat'

vars_wm = [r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_mosaic.xml '
           r'-m:%gdbwks%\watermap_extent -s:%acspath%%s3tag%\ -p:%cachepath%\$cachelocation '
           r'-p:USE_PIXEL_CACHE$pixelcache -p:%s3tag%$stag -c:CM+AF+AR+UpdateFieldsWM+BF+BB+SP+CC',
           r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_overviews.xml '
           r'-m:%gdbwks%\watermap_extent -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf']

vars_rgb = [r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rgb_mosaic.xml '
            r'-m:%gdbwks%\rgb -s:%acspath%%s3tag%\ -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache '
            r'-p:%s3tag%$stag -c:CM+AF+AR+UpdateFieldsRGB+BF+BB+SP+CC',
            r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rgb_overviews.xml '
            r'-m:%gdbwks%\rgb -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf']

vars_rtc = [r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rtc_mosaic_s1.xml '
            r'-m:%gdbwks%\sar_s1 -s:%acspath%%s3tag%\ -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache '
            r'-c:CM+AF+AR+UpdateFieldsRTC+BF+BB+SP+CC',
            r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rtc_mosaic_comp.xml '
            r'-m:%gdbwks%\sar_comp -s:%gdbwks%\sar_s1 -p:CompositeVV_VH_32.art.xml$art '
            r'-p:%s3tag%$stag -c:CM+AR+UpdateNameFieldRTC+BB+SP+CC',
            r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rtc_overviews.xml '
            r'-m:%gdbwks%\sar_comp -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf']

batfiles = [batfile_wm, batfile_rgb, batfile_rtc]

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
        if bat == 'Honduras_wm.bat':
            print(crf_wm, file=f)
            print('\nREM ---------- Using ACS File -------------------------', file=f)
            for vb in vars_wm:
                print(vb, file=f)
        elif bat == 'Honduras_rgb.bat':
            print(crf_rgb, file=f)
            print('\nREM ---------- Using ACS File -------------------------', file=f)
            for vb in vars_rgb:
                print(vb, file=f)
        elif bat == 'Honduras_rtc.bat':
            print(crf_rtc, file=f)
            print('\nREM ---------- Using ACS File -------------------------', file=f)
            for vb in vars_rtc:
                print(vb, file=f)
        else:
            print('No valid file.')

# run the batch files

subprocess.call([batfile_wm])
print('Watermap Extent mosaic dataset complete.')
subprocess.call([batfile_rgb])
print('RGB mosaic dataset complete.')
subprocess.call([batfile_rtc])
print('RTC mosaic dataset complete.')

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

print('Generating RGB AID package...')
md_rgb = gdb+'\\'+'rgb'
aid_rgb = aid_path+'\\'+projtag+'_RGB_'+today+'.zmd'
with arcpy.EnvManager(scratchWorkspace=scratch_ws, workspace=scratch_ws):
    try:
        arcpy.AID.AIDISDP(md_rgb, aid_rgb, None)
    except:
        print("AID errors generated and ignored.")
        pass
print('RGB AID package complete.')

print('Generating RTC AID package...')
md_rtc = gdb+'\\'+'sar_comp'
aid_rtc = aid_path+'\\'+projtag+'_RTC_'+today+'.zmd'
with arcpy.EnvManager(scratchWorkspace=scratch_ws, workspace=scratch_ws):
    try:
        arcpy.AID.AIDISDP(md_rtc, aid_rtc, None)
    except:
        print("AID errors generated and ignored.")
        pass
print('RTC AID package complete.')

#  create/update image services
pw = keyring.get_password("portal_creds", "hkristenson_ASF")
arcpy.SignInToPortal(r'https://asf-daac.maps.arcgis.com/', 'hkristenson_ASF', pw)

credit_statement = "Products processed by ASF DAAC HyP3 2022 using GAMMA software. " \
                   "Contains modified Copernicus Sentinel data 2020-2021, processed by ESA."

# generate watermap extent service
service_desc = "**TEST OF WATERMAP EXTENT PRODUCT IN A REGION OTHER THAN WHERE IT WAS VALIDATED** Watermap Extent " \
               "products generated from Sentinel-1 SAR imagery over an AOI in Honduras from April 15, 2020 to " \
               "April 15, 2021, processed by ASF."

# print('Updating Watermap Extent Image Service...')
# arcpy.AID.MAIDIS("asf-daac", "Update Service", "test", "None", "Honduras_WM", None, aid_wm, "Dedicated Instance",
#                  service_desc, credit_statement, '', False, False, True, None, None, None, None)
# print('Watermap Extent Image Service updated.')

print('Creating Watermap Extent Image Service...')
arcpy.AID.MAIDIS("asf-daac", "Create Service", "test", "Honduras_WM", '', aid_wm, None, "Dedicated Instance",
                 service_desc, credit_statement, '', False, False, True, None, None, None, None)
print('Watermap Extent Image Service created.')

# generate RGB service
service_desc = "Sentinel-1 RGB Decomposition of RTC VV and VH imagery over an AOI in Honduras from April 15, 2020 to " \
                 "April 15, 2021, processed by ASF. Blue areas have low returns in VV and VH (smooth surfaces such " \
                 "as calm water, but also frozen/crusted soil or dry sand), green areas have high returns in VH " \
                 "(volume scatterers such as vegetation or some types of snow/ice), and red areas have relatively " \
                 "high VV returns and relatively low VH returns (such as urban or sparsely vegetated areas)."

# print('Updating RGB Image Service...')
# arcpy.AID.MAIDIS("asf-daac", "Update Service", "test", "None", "Honduras_RGB", None, aid_rgb, "Dedicated Instance",
#                  service_desc, credit_statement, '', False, False, True, None, None, None, None)
# print('RGB Image Service updated.')

print('Creating RGB Image Service...')
arcpy.AID.MAIDIS("asf-daac", "Create Service", "test", "Honduras_RGB", '', aid_rgb, None, "Dedicated Instance",
                 service_desc, credit_statement, '', False, False, True, None, None, None, None)
print('RGB Image Service created.')

# generate RTC service
service_desc = "Radiometric Terrain Corrected (RTC) products generated from Sentinel-1 SAR imagery over an AOI in " \
                 "Honduras from April 15, 2020 to April 15, 2021, processed by ASF. Surface water appears very dark " \
                 "under calm conditions, as signal bounces off the surface away from the sensor. High VV values " \
                 "are commonly driven by surface roughness and/or high soil moisture, and high VH values " \
                 "commonly indicate the presence of vegetation."

# print('Updating RTC Image Service...')
# arcpy.AID.MAIDIS("asf-daac", "Update Service", "test", "None", "Honduras_RTC", None, aid_rtc, "Dedicated Instance",
#                  service_desc, credit_statement, '', False, False, True, None, None, None, None)
# print('RTC Image Service updated.')

print('Creating RTC Image Service...')
arcpy.AID.MAIDIS("asf-daac", "Create Service", "test", "Honduras_RTC", '', aid_rtc, None, "Dedicated Instance",
                 service_desc, credit_statement, '', False, False, True, None, None, None, None)
print('RTC Image Service created.')
