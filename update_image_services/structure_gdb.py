import arcpy

# Set geodatabase to use as starting point
ingdb = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\image_server\asf_services\MD\... .gdb'

# Format source, derived and referenced mosaic datasets for each service
for md in ['rgb', 'sar_comp', 'watermap_extent']:
    mdpath = ingdb + '\\' + md
    md_der = mdpath + '_derived'
    md_ref = mdpath + '_referenced'

    # Generate derived mosaic dataset from original source mosaic dataset
    arcpy.management.Copy(mdpath, md_der)
    arcpy.AddMessage('Created ' + md_der + ' from ' + mdpath)
    print('Created ' + md_der + ' from ' + mdpath)
    arcpy.management.RemoveRastersFromMosaicDataset(mdpath, "Category = 2", "NO_BOUNDARY",
                                                    "MARK_OVERVIEW_ITEMS", "DELETE_OVERVIEW_IMAGES",
                                                    "DELETE_ITEM_CACHE", "REMOVE_MOSAICDATASET_ITEMS",
                                                    "NO_CELL_SIZES")

    # Remove overviews from original source mosaic dataset
    arcpy.AddMessage('Removed overviews from ' + md + ' source mosaic dataset')
    print('Removed overviews from ' + md + ' source mosaic dataset')
    arcpy.management.CreateReferencedMosaicDataset(md_der, md_ref,
                                                   'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",'
                                                   'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
                                                   'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
                                                   'PRIMEM["Greenwich",0.0],'
                                                   'UNIT["Degree",0.0174532925199433]],'
                                                   'PROJECTION["Mercator_Auxiliary_Sphere"],'
                                                   'PARAMETER["False_Easting",0.0],'
                                                   'PARAMETER["False_Northing",0.0],'
                                                   'PARAMETER["Central_Meridian",0.0],'
                                                   'PARAMETER["Standard_Parallel_1",0.0],'
                                                   'PARAMETER["Auxiliary_Sphere_Type",0.0],'
                                                   'UNIT["Meter",1.0]]',
                                                   None, '', '', None, None, "SELECT_USING_FEATURES", None, None, None,
                                                   None, "BUILD_BOUNDARY")

    # Create referenced mosaic dataset from derived mosaic dataset
    arcpy.AddMessage('Created reference mosaic dataset from ' + md_der)
    print('Created reference mosaic dataset from ' + md_der)
