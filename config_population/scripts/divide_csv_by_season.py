# Read through the csv with all vv_COH12 urls and pull out a single season

in_file_path = r'C:\Users\hjkristenson\PycharmProjects\Python39test\ConfigPopulation\InputURLs\vv_COH12_urls.txt'
out_file_path = r'C:\Users\hjkristenson\PycharmProjects\Python39test\ConfigPopulation\InputURLs\vv_COH12_urls_summer.txt'

out_file = open(out_file_path, 'w')

with open(in_file_path) as in_file:
    for line in in_file:
        if "summer" in line:
            out_file.write(line)
        else:
            pass

out_file.close()
