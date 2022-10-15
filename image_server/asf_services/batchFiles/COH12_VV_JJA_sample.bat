set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services
set cachepath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\PixelCache

REM ---------- Set output gdb and source s3 bucket-----
set gdbwks=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD\GSSICB\GSSICB_COH12_VV_JJA_sample_221005_0815.gdb
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\GSSICB_COH12_VV_JJA_sample_221005_0815.crf

REM ---------- Using ACS File -------------------------
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\COH12_VV_JJA_sample.xml -m:%gdbwks%\\COH12_VV_JJA_sample -p:%cachepath%\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+UpdateFieldsCoh+BF+BB+SP+CC
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\\COH12_VV_JJA_sample_ovr.xml -m:%gdbwks%\\COH12_VV_JJA_sample -s:%outcrf% -c:SE+CRA+AR+UpdateCohOverviewFields -p:%outcrf%$outcrf
