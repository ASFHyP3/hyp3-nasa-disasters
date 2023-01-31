import arcpy

print('Generating draft service definition...')
arcpy.CreateImageSDDraft(
    r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD\GLO30_HAND\
    GLO30_HAND_221205_2153.gdb\GLO30_HAND',
    r'G:\Projects\2209_ImageServices\HAND\SD\GLO30_HAND_230131.sddraft', "GLO30_HAND", "ARCGIS_SERVER",
    r'G:\Projects\2209_ImageServices\ImageServices\arcgis on gis.asf.alaska.edu.ags', "FALSE", "GlobalHAND",
    r"Height Above Nearest Drainage (HAND) is a terrain model that normalizes topography to the relative heights "
    r"along the drainage network and is used to describe the relative soil gravitational potentials or the local "
    r"drainage potentials. Each pixel value represents the vertical distance to the nearest drainage. The HAND "
    r"data provides near-worldwide land coverage at 30 meters and was produced from the 2021 release of the Copernicus "
    r"GLO-30 Public DEM as distributed in the Registry of Open Data on AWS "
    r"(https://registry.opendata.aws/copernicus-dem/) using the the ASF Tools Python Package "
    r"(https://hyp3-docs.asf.alaska.edu/tools/asf_tools_api/#asf_tools.hand.calculate) and the PySheds Python library "
    r"(https://github.com/mdbartos/pysheds). The HAND data are provided as a tiled set of Cloud Optimized GeoTIFFs "
    r"(COGs) with 30-meter (1 arcsecond) pixel spacing. The COGs are organized into the same 1 degree by 1 degree "
    r"grid tiles as the GLO-30 DEM, and individual tiles are pixel-aligned to the corresponding COG DEM tile.",
    "HAND, Height Above Nearest Drainage, ASF, Alaska Satellite Facility, Copernicus DEM, GLO-30")
print('Draft service definition has been generated.')

print('Staging service definition...')
arcpy.server.StageService(
    r"G:\Projects\2209_ImageServices\HAND\SD\GLO30_HAND_230131.sddraft",
    r"G:\Projects\2209_ImageServices\HAND\SD\GLO30_HAND_230131.sd", 209)
print('Service definition has been staged.')
