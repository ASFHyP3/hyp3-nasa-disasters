# Service Definition Files

Service definition files are used to publish services to the image server. They can be generated in ArcGIS Pro or programmatically. 

The ASF_SampleData directory contains the service definitions for the services used in StoryMap tutorials. They were generated using notebooks in ArcGIS Pro, and generally publish a single GeoTIFF, rather than a mosaic dataset. Publishing the service definitions is a 2-step process, starting with a draft (.ssd file), and finishing with a packaged service definition (.sd file).

Services published to the ArcGIS Image Dedicated (AID) server using the MDCS workflow have a python wrapper script that includes the generation of the service definition in the format required for the AID services. These service definitions are packaged in a .zmd file, and output to the AID directory inside the MDCS directory structure. 

