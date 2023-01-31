# ------------------------------------------------------------------------------
# Name: populate_xml_with_data.py
# Description: This program will take in a csv file of 1 column and no header
# 	and a config XML file for MDCS and populate the csv entries into the 
#	"data_path" region of the XML config file. It will delete all previous 
# 	"data_path"s that were in the file.
# Date: 28-Sept-2022
# Requirements: Python 3.9.12
# Required Arguments: csv file, xml file
# Author: Sheridan Moore, Imagery and Remote Sensing, Advanced Analytics, 
#	      Professional Services, Esri (sheridanmoore@esri.com)
#
# HK Note: this script requires a python installation of at least 3.9
# ------------------------------------------------------------------------------

# necessary python modules
import pandas as pd
import xml.etree.ElementTree as et

# remove all children from parent
def kill_children(parent_et_element, child_tag):
	"""
	Removes all children from parent in XML file

	Keyword Arguments:
	parent_et_element -- element tree element of the parent
	child_tag -- string of the tag for the child
	"""

	# find all children with specified tag
	children = parent_et_element.findall(child_tag)

	# remove all of the children
	for child in children:
		parent_et_element.remove(child)


# read csv file
def csv_to_list(csv_file):
	"""
	Reads a csv of data and converts to a list of data strings

	Keyword arguments:
	csv_file -- csv file containing the data needed to add to the XML file
		should be formatted such that there is 1 column of data with a header
	csv_data_col_name -- the header of data column/name of the column that 
		data is in

	Returns:
	csv_list_of_data -- a list of strings where data paths
	"""

	# read csv file
	df = pd.read_csv(csv_file, header=None) 
	
	# create empty list
	csv_list_of_data = []

	# loop through csv data and add to list
	for element in df[0]:
		element = str(element) #convert each element to string if not already
		csv_list_of_data.append(element)

	return csv_list_of_data


# write to xml file
def write_to_xml(csv_data, new_xml_file_name, export_bool):
	"""
	Writes data from csv to xml file.

	Keyword arguments:
	csv_data -- a list of strings where data paths
	export -- a boolean on if a new XML file should be written out
	new_xml_file_name -- a string ending with .xml as the new filename

	Returns:
	num_csv_data_files -- the number of data paths added to the XML file
	"""

	# find sources, add csv data as a new data_path
	for element in root.iter():
		if element.tag == "Sources":
			for data in csv_data:
				et.indent(tree, "	")
				et.SubElement(element, "data_path").text = data
				et.indent(tree, "	")

	# export
	if export_bool:
		tree.write(new_xml_file_name, "UTF-8")

	# get number of added files
	num_csv_data_files = len(csv_data)

	return num_csv_data_files


# iterate through the parent
def iterate_parent(parent, tag):
	"""
	Iterates through a parent XML directory to get the location of the 
	specified child

	Keyword Arguments:
	parent -- the parent directory in the XML file
	tag -- the name of the specified child

	Returns:
	et_element -- the location of the element in the XML file
	"""

	# identify zeros for increment
	i = 0

	# loop through parent and find the location of the child
	for child in parent:
		if child.tag == tag:
			et_element = parent[i]

		i = i + 1

	return et_element


# get location of sources
def find_sources(root):
	"""
	Iterates through each branch of the XML file to find the location of Sources

	Keyword Arguments:
	root -- the root of the XML file; defined below at the start of the code

	Returns:
	sources_et_element -- the location in the file that takes you to the branch 
		of sources
	"""

	# finds the location of sources within xml file
	# Application.Workspace.MosaicDataset.AddRasters.AddRaster.Sources
	worspace_et_element = iterate_parent(root, "Workspace")
	mosaic_dataset_et_element = iterate_parent(worspace_et_element, "MosaicDataset")
	add_rasters_et_element = iterate_parent(mosaic_dataset_et_element, "AddRasters")
	add_raster_et_element = iterate_parent(add_rasters_et_element, "AddRaster")
	sources_et_element = iterate_parent(add_raster_et_element, "Sources")

	return sources_et_element


def add_source_child(root):
	"""
	Iterates through each branch of the XML file to find the location of 
	AddRaster to then add a Source tag.

	Keyword Arguments:
	root -- the root of the XML file; defined below at the start of the code

	Returns:
	N/A
	"""

	for element in root.iter():
		if element.tag == "AddRaster":
			et.indent(tree, "	")
			et.SubElement(element, "Sources")
			et.indent(tree, "	")


# start the code
if __name__ == '__main__':

	# input variables needed / things to change
	csv_file = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\config_population\source_raster_lists\COH12_test_sample_urls.txt'
	export_bool = True
	xml_original_file = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\config_population\config_templates\COH12_VV_JJA_template.xml'
	#new_xml_file_name = "../ConfigFiles/test_output.xml"
	new_xml_file_name = r'C:\Users\hjkristenson\PycharmProjects\hyp3-nasa-disasters\config_population\config_templates\test_output.xml'

	# read xml file
	tree = et.parse(xml_original_file)
	root = tree.getroot()

	try:
		# get xml sources
		sources_et_element = find_sources(root)
		sources_str = et.tostring(sources_et_element).decode("utf-8")

	# if there is no source element
	except UnboundLocalError:
		add_source_child(root)
		csv_data = csv_to_list(csv_file)
		num_csv_data_files = write_to_xml(csv_data, new_xml_file_name, export_bool)
		print("{num_csv_data_files} data_path record(s) have been added.".format(num_csv_data_files = num_csv_data_files))

	# if there is a source element
	else:
		kill_children(sources_et_element, "data_path")
		csv_data = csv_to_list(csv_file)
		num_csv_data_files = write_to_xml(csv_data, new_xml_file_name, export_bool)
		print("{num_csv_data_files} data_path record(s) have been added.".format(num_csv_data_files = num_csv_data_files))
