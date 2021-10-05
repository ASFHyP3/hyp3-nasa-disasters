set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services
set cachepath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\PixelCache

REM ---------- Set output gdb and source s3 bucket-----
set gdbwks=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD\HKH\HKH_211004.gdb
set acspath=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\HKHwatermaps\
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\HKH_WatermapExtent_211004B.crf

REM ---------- Using ACS File -------------------------
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_mosaic.xml -m:%gdbwks%\watermap_extent -s:%acspath% -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+BF+BB+SP+CC+CV
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_overviews.xml -m:%gdbwks%\watermap_extent -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf
