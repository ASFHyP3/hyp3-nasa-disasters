set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services
set cachepath=G:\Projects\2209_ImageServices\ImageServices\PixelCache

REM ---------- Set output gdb and source s3 bucket-----
set gdbwks=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD\GLO30_HAND\GLO30_HAND_221205_2153.gdb
set acspath=G:\Projects\2209_ImageServices\ImageServices\COP30_HAND.acs\
set s3tag=v1/2021
set outcrf=G:\Projects\2209_ImageServices\ImageServices\NASA_Disasters_AWS.acs\esri\GLO30_HAND_221205_2153.crf

REM ---------- Using ACS File -------------------------
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\GLO30_HAND.xml -m:%gdbwks%\\GLO30_HAND -s:%acspath%%s3tag%\ -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+UpdateFieldsHAND+BF+BB+SP+CC
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\GLO30_HAND_ovr.xml -m:%gdbwks%\\GLO30_HAND -s:%outcrf% -c:SE+CRA+AR+UpdateHANDOverviewFields -p:%outcrf%$outcrf
