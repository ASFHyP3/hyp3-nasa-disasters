set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services
set cachepath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\PixelCache

REM ---------- Set output gdb and source s3 bucket-----
set gdbwks=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD\Honduras\Honduras_221123_2139.gdb
set acspath=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\
set s3tag=Honduras
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\Honduras_RGB_221123_2139.crf

REM ---------- Using ACS File -------------------------
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rgb_mosaic.xml -m:%gdbwks%\rgb -s:%acspath%%s3tag%\ -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -p:%s3tag%$stag -c:CM+AF+AR+UpdateFieldsRGB+BF+BB+SP+CC
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rgb_overviews.xml -m:%gdbwks%\rgb -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf
