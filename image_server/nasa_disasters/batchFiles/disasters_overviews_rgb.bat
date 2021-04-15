set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" 
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\nasa_disasters
set gdbwks=C:\Users\ASF\Documents\COVID19\Disasters\Esri\MosaicDatasets\missouri_disasters_mosaics_rgb.gdb
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\missouri_disasters_mosaics_rgb.crf

REM ---------- Using ACS File -------------------------

%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_ovr_rgb.xml -m:%gdbwks%\rgb -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf

REM (to add only) %ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_ovr.xml -m:%gdbwks%\sar_comp -s:%outcrf% -c:AR+UpdateOverviewFields -p:%outcrf%$outcrf
