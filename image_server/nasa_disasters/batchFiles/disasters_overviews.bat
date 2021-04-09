set ppath="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" 
set mdcspath=C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\nasa_disasters
set gdbwks=C:\Users\ASF\Documents\COVID19\Disasters\Esri\MosaicDatasets\missouri_disasters_mosaic_210402.gdb
set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\esri\missouri_disasters_mosaic_210409.crf
REM set outcrf=C:\Users\ASF\Documents\COVID19\Disasters\Esri\MosaicDatasets\missouri_disasters_mosaic_210409.crf
REM ---------- Using ACS File -------------------------

REM %ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_s1.xml -m:%gdbwks%\sar_s1 -s:C:\Users\ASF\Documents\COVID19\Disasters\FloodAreas\NASA_Disasters_AWS.acs\Missouri_UTM\ -p:C:\Users\ASF\Documents\COVID19\Disasters\Esri\MosaicDatasets\PixelCache\$cachelocation -p:USE_PIXEL_CACHE$pixelcache -c:CM+AF+AR+BF+BB+SP+CC+CV
REM %ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_comp.xml -m:%gdbwks%\sar_comp_210406B -s:%gdbwks%\sar_s1 -p:CompositeVV_VH_32.art.xml$art -c:CM+AR+UpdateNameField+BB+SP+CC+SE+CRA -p:%outcrf%$outcrf

REM %ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_comp.xml -m:%gdbwks%\sar_comp_210409 -s:%gdbwks%\sar_s1 -p:CompositeVV_VH_32.art.xml$art -c:CM+AR+UpdateNameField+BB+SP+CC
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_comp.xml -m:%gdbwks%\sar_comp_210409 -c:SE+CRA -p:%outcrf%$outcrf

REM %ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_comp.xml -m:%gdbwks%\sar_comp -s:%gdbwks%\sar_s1 -p:CompositeVV_VH_32.art.xml$art -c:SE+CRA -p:%outcrf%$outcrf
%ppath% %mdcspath%\scripts\MDCS.py -i:%mdcspath%\Parameter\Config\disasters_mosaics_ovr.xml -m:%gdbwks%\sar_comp -c:SE+CP+AR
