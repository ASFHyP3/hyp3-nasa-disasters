set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services
set cachepath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\PixelCache

REM ---------- Set output gdb and source s3 bucket-----
set gdbwks=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD\HKH\HKH_220622_0830.gdb
set acspath=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\
set s3tag=HKHwatermaps
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\HKH_WatermapExtent_220622_0830.crf

REM ---------- Using ACS File -------------------------
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_mosaic.xml -m:%gdbwks%\watermap_extent -s:%acspath%%s3tag%\ -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -p:%s3tag%$stag -c:CM+AF+AR+UpdateFieldsWM+BF+BB+SP+CC
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\wm_overviews.xml -m:%gdbwks%\watermap_extent -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf
