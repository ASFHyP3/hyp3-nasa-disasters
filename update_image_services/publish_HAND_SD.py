# This script takes as input a geodatabase generated using the MDCS scripts,
# generates the draft service definition for each referenced MD,
# and stages a service definition.
#
# For each of the services to be published:
# 1. A draft service definition is generated from the source mosaic dataset
# 2. A final service definition is staged
#
# This script must be run on the input geodatabase after it has been uploaded to the server.
#
# The service definition (.sd) files can be published using /arcgis/server/tools/admin/createservice, e.g.:
# createservice -u <user> -p <password> -s "http://localhost/arcgis" -f ASF_S1_RGB.sd -F ASF_S1 -n ASF_S1_RGB

# import tempfile

import arcpy

md = '/home/arcgis/GLO30_HAND/GLO30_HAND_221205_2153.gdb/GLO30_HAND'

# Format source, derived and referenced mosaic datasets for each service

# Generate service definition from the dataset
print(f'Generating draft service definition for {md}')
arcpy.CreateImageSDDraft(md, '/home/arcgis/GLO30_HAND/GLO30_HAND.sdd', 'GLO30_HAND')
print(f'Generating final service definition for {md}')
arcpy.server.StageService('/home/arcgis/GLO30_HAND/GLO30_HAND.sddraft', '/home/arcgis/GLO30_HAND/GLO30_HAND.sd')

