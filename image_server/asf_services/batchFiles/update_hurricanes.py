# This script generates the batch files for the three services generated from the watermap products
# then runs them in sequence

import os
from datetime import date, timedelta
import subprocess
import arcpy

os.chdir(r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\batchFiles')

today = str(date.today().strftime("%y%m%d"))
s3tag = 'RTC_services'
dirtag = 'Hurricanes'
projtag = 'RTCservices'
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
        r'set acspath=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs''\\'''+s3tag+'\\']

crf_wm = r'set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri''\\'\
         +crftag_wm+'_'+today+'B.crf'
crf_rgb = r'set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri''\\'\
          +crftag_rgb+'_'+today+'B.crf'
crf_rtc = r'set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri''\\'\
          +crftag_rtc+'_'+today+'B.crf'

batfile_wm = 'RTCservices_wm.bat'
batfile_rgb = 'RTCservices_rgb.bat'
batfile_rtc = 'RTCservices_rtc.bat'

vars_wm = [r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_mosaic.xml '
           r'-m:%gdbwks%\watermap_extent -s:%acspath% -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache '
           r'-c:CM+AF+AR+BF+BB+SP+CC+CV',
           r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_overviews.xml '
           r'-m:%gdbwks%\watermap_extent -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf']

vars_rgb = [r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rgb_mosaic.xml '
            r'-m:%gdbwks%\rgb -s:%acspath% -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache '
            r'-c:CM+AF+AR+BF+BB+SP+CC+CV',
            r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rgb_overviews.xml '
            r'-m:%gdbwks%\rgb -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf']

vars_rtc = [r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rtc_mosaic_s1.xml '
            r'-m:%gdbwks%\sar_s1 -s:%acspath% -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache '
            r'-c:CM+AF+AR+BF+BB+SP+CC+CV',
            r'%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rtc_mosaic_comp.xml '
            r'-m:%gdbwks%\sar_comp -s:%gdbwks%\sar_s1 -p:CompositeVV_VH_32.art.xml$art '
            r'-c:CM+AR+UpdateNameField+BB+SP+CC',
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
        if bat == 'RTCservices_wm.bat':
            print(crf_wm, file=f)
            print('\nREM ---------- Using ACS File -------------------------', file=f)
            for vb in vars_wm:
                print(vb, file=f)
        elif bat == 'RTCservices_rgb.bat':
            print(crf_rgb, file=f)
            print('\nREM ---------- Using ACS File -------------------------', file=f)
            for vb in vars_rgb:
                print(vb, file=f)
        elif bat == 'RTCservices_rtc.bat':
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

#  update image services
import keyring
pw = keyring.get_password("portal_creds", "hkristenson_ASF")
arcpy.SignInToPortal(r'https://asf-daac.maps.arcgis.com/', 'hkristenson_ASF', pw)

print('Updating Watermap Extent Image Service...')
arcpy.AID.MAIDIS("asf-daac", "Update Service", "test", "None", "CONUS_watermaps", None, aid_wm, "Dedicated Instance",
                 "Watermap Extent products generated from Sentinel-1 SAR imagery over eastern CONUS for the 2021 "
                 "hurricane season, generated by ASF.", "Imagery products processed by ASF DAAC HyP3 2021 using "
                 "GAMMA software. Contains modified Copernicus Sentinel data 2021, processed by ESA.", '',
                 False, False, True, None, None, None, None)
print('Watermap Extent Image Service updated.')
print('Updating RGB Image Service...')
arcpy.AID.MAIDIS("asf-daac", "Update Service", "ASF_RTC", "None", "ASF_S1_RGB", None, aid_rgb, "Dedicated Instance",
                 "Sentinel-1 RGB Decomposition of RTC VV and VH imagery over eastern CONUS for the 2021 hurricane "
                 "season, processed by ASF. Blue areas have low returns in VV and VH (smooth surfaces such as calm "
                 "water, but also frozen/crusted soil or dry sand), green areas have high returns in VH (volume "
                 "scatterers such as vegetation or some types of snow/ice), and red areas have relatively high VV "
                 "returns and relatively low VH returns (such as urban or sparsely vegetated areas).", "RGB "
                 "Decomposition products processed by ASF DAAC HyP3 2021 using GAMMA software. Contains modified "
                 "Copernicus Sentinel data 2021, processed by ESA.", '', False, False, True, None, None, None, None)
print('RGB Image Service updated.')
print('Updating RTC Image Service...')
arcpy.AID.MAIDIS("asf-daac", "Update Service", "ASF_RTC", "None", "ASF_S1_RTC", None, aid_rtc, "Dedicated Instance",
                 "Radiometric Terrain Corrected (RTC) products generated from Sentinel-1 SAR imagery over eastern "
                 "CONUS for the 2021 hurricane season, processed by ASF. Surface water appears very dark under calm "
                 "conditions, as signal bounces off the surface away from the sensor. High VV values are commonly "
                 "driven by surface roughness and/or high soil moisture, and high VH values commonly indicate the "
                 "presence of vegetation.", "RTC products processed by ASF DAAC HyP3 2021 using GAMMA software. "
                                            "Contains modified Copernicus Sentinel data 2021, processed by ESA.", '',
                 False, False, True, None, None, None, None)
print('RTC Image Service updated.')

#
# # delete previous version of the gdb and zmd files
# yesterday = str((date.today()-timedelta(days=1)).strftime("%y%m%d"))
#
# del_gdb = r'C:\Users\ASF\Documents\COVID19\Disasters\Watermaps\MosaicDatasets''\\'+projtag+'\\'+projtag+'_'+yesterday+'.gdb'
# if os.path.exists(del_gdb):
#   os.remove(del_gdb)
# else:
#   print("The gdb does not exist")
#
# del_aid_wm = r'C:\Users\ASF\Documents\COVID19\Disasters\Watermaps\AID_Packages\HKH_WatermapExtent_'+yesterday+'.zmd'
# del_aid_rgb = r'C:\Users\ASF\Documents\COVID19\Disasters\Watermaps\AID_Packages\HKH_RGB_'+yesterday+'.zmd'
# del_aid_rtc = r'C:\Users\ASF\Documents\COVID19\Disasters\Watermaps\AID_Packages\HKH_RTC_'+yesterday+'.zmd'
#
# del_list = [del_aid_wm, del_aid_rgb, del_aid_rtc]
# for dl in del_list:
#     if os.path.exists(dl):
#         os.remove(dl)
#     else:
#         print("The zmd file does not exist")
