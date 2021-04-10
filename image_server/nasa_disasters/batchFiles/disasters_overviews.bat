set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" 
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\nasa_disasters
set gdbwks=C:\Users\ASF\Documents\COVID19\Disasters\Esri\MosaicDatasets\missouri_disasters_mosaic.gdb
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\missouri_disasters_mosaic.crf

REM ---------- Using ACS File -------------------------

%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_ovr.xml -m:%gdbwks%\sar_comp -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf
