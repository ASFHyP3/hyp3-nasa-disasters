set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services
set cachepath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\PixelCache

REM ---------- Set output gdb and source s3 bucket-----
set gdbwks=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD\RTCservices\RTCservices_211004.gdb
set acspath=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\RTC_services\
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\RTCservices_RTC_211004B.crf

REM ---------- Using ACS File -------------------------
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rtc_mosaic_s1.xml -m:%gdbwks%\sar_s1 -s:%acspath% -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+BF+BB+SP+CC+CV
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rtc_mosaic_comp.xml -m:%gdbwks%\sar_comp -s:%gdbwks%\sar_s1 -p:CompositeVV_VH_32.art.xml$art -c:CM+AR+UpdateNameField+BB+SP+CC
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\rtc_overviews.xml -m:%gdbwks%\sar_comp -s:%outcrf% -c:SE+CRA+AR+UpdateOverviewFields -p:%outcrf%$outcrf
