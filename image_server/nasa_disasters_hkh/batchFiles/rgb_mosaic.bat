set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" 
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\nasa_disasters_hkh
set cachepath=C:\Users\ASF\Documents\COVID19\Disasters\Esri\MosaicDatasets\PixelCache

REM ---------- Set output gdb and source s3 bucket-----
set gdbwks=C:\Users\ASF\Documents\COVID19\Disasters\Watermaps\MosaicDatasets\HKH\HKH.gdb
set acspath=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\HKHwatermaps\
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\HKH_RGB.crf

REM ---------- Using ACS File -------------------------
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rgb_mosaic.xml -m:%gdbwks%\rgb -s:%acspath% -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+BF+BB+SP+CC+CV
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rgb_overviews.xml -m:%gdbwks%\rgb -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf
