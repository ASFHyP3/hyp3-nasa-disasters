set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" 
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\nasa_disasters
set cachepath=C:\Users\ASF\Documents\COVID19\Disasters\Esri\MosaicDatasets\PixelCache

REM ---------- Set output gdb and source s3 bucket-----
set gdbwks=C:\Users\ASF\Documents\COVID19\Disasters\GlobalHAND\GlobalHAND\MosaicDatasets\COP30_GlobalHAND_210610.gdb
set acspath=C:\Users\ASF\Documents\COVID19\Disasters\GlobalHAND\GlobalHAND\GlobalHand.acs
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\COP30_GlobalHAND_210610.crf

REM ---------- Using ACS File -------------------------
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\copernicus_hand.xml -m:%gdbwks%\COP30_GlobalHAND -s:%acspath% -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+BF+BB+SP+CC+CV
REM %ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\copernicus_hand_ovr.xml -m:%gdbwks%\COP30_GlobalHAND -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf
