# pull out tile names for a desired AOI
#
# Select for northern hemisphere
def n_hemi(in_csv, out_file_path):

    out_file_nh = open(nh_out_file_path, 'w')

    with open(in_csv) as in_file:
        for line in in_file:
            if r'tiles/N' in line:
                out_file_nh.write(line)
            else:
                pass

    out_file_nh.close()

# Select for CONUS
def select_conus(conus_out_file_path):

    out_file_conus = open(conus_out_file_path, 'w')

    #long_list = ['W053', 	'W054', 	'W055', 	'W056', 	'W057', 	'W058', 	'W059', 	'W060', 	'W061', 	'W062', 	'W063', 	'W064', 	'W065', 	'W066', 	'W067', 	'W068', 	'W069', 	'W070', 	'W071', 	'W072', 	'W073', 	'W074', 	'W075', 	'W076', 	'W077', 	'W078', 	'W079', 	'W080', 	'W081', 	'W082', 	'W083', 	'W084', 	'W085', 	'W086', 	'W087', 	'W088', 	'W089', 	'W090', 	'W091', 	'W092', 	'W093', 	'W094', 	'W095', 	'W096', 	'W097', 	'W098', 	'W099', 	'W100', 	'W101', 	'W102', 	'W103', 	'W104', 	'W105', 	'W106', 	'W107', 	'W108', 	'W109', 	'W110', 	'W111', 	'W112', 	'W113', 	'W114', 	'W115', 	'W116', 	'W117', 	'W118', 	'W119', 	'W120', 	'W121', 	'W122', 	'W123', 	'W124', 	'W125', 	'W126', 	'W127', 	'W128', 	'W129', 	'W130', 	'W131', 	'W132', 	'W133', 	'W134', 	'W135', 	'W136', 	'W137', 	'W138', 	'W139', 	'W140', 	'W141', 	'W142', 	'W143', 	'W144', 	'W145', 	'W146', 	'W147', 	'W148', 	'W149', 	'W150', 	'W151', 	'W152', 	'W153', 	'W154', 	'W155', 	'W156', 	'W157', 	'W158', 	'W159', 	'W160', 	'W161', 	'W162', 	'W163', 	'W164', 	'W165', 	'W166', 	'W167', 	'W168']
    #long_list = ['W053', 	'W054', 	'W055', 	'W056', 	'W057', 	'W058', 	'W059', 	'W060', 	'W061', 	'W062', 	'W063', 	'W064', 	'W065', 	'W066', 	'W067', 	'W068', 	'W069', 	'W070', 	'W071', 	'W072', 	'W073', 	'W074', 	'W075', 	'W076', 	'W077', 	'W078', 	'W079', 	'W080', 	'W081', 	'W082', 	'W083', 	'W084', 	'W085', 	'W086', 	'W087', 	'W088', 	'W089', 	'W090', 	'W091', 	'W092', 	'W093', 	'W094', 	'W095', 	'W096', 	'W097', 	'W098', 	'W099', 	'W100', 	'W101', 	'W102', 	'W103', 	'W104', 	'W105', 	'W106', 	'W107', 	'W108', 	'W109', 	'W110', 	'W111', 	'W112', 	'W113', 	'W114', 	'W115', 	'W116', 	'W117', 	'W118', 	'W119', 	'W120', 	'W121', 	'W122', 	'W123', 	'W124', 	'W125', 	'W126', 	'W127', 	'W128', 	'W129', 	'W130', 	'W131', 	'W132', 	'W133', 	'W134', 	'W135', 	'W136', 	'W137', 	'W138', 	'W139', 	'W140', 	'W141']
    long_list = ['W053', 	'W054', 	'W055', 	'W056', 	'W057', 	'W058', 	'W059', 	'W060', 	'W061', 	'W062', 	'W063', 	'W064', 	'W065', 	'W066', 	'W067', 	'W068', 	'W069', 	'W070', 	'W071', 	'W072', 	'W073', 	'W074', 	'W075', 	'W076', 	'W077', 	'W078', 	'W079', 	'W080', 	'W081', 	'W082', 	'W083', 	'W084', 	'W085', 	'W086', 	'W087', 	'W088', 	'W089', 	'W090', 	'W091', 	'W092', 	'W093', 	'W094', 	'W095', 	'W096', 	'W097', 	'W098', 	'W099', 	'W100', 	'W101', 	'W102', 	'W103', 	'W104', 	'W105', 	'W106', 	'W107', 	'W108', 	'W109', 	'W110', 	'W111', 	'W112', 	'W113', 	'W114', 	'W115', 	'W116', 	'W117', 	'W118', 	'W119', 	'W120', 	'W121', 	'W122', 	'W123', 	'W124', 	'W125']

    with open(nh_out_file_path) as in_file:
        for line in in_file:
            for long in long_list:
                if long in line:
                    print(line)
                    out_file_conus.write(line)
            else:
                pass

    out_file_conus.close()


# Select for France
def select_france(fr_out_file_path):

    out_file_france = open(fr_out_file_path, 'w')

    france_lat_list = ["N42", "N43", "N44", "N45", "N46", "N47", "N48", "N49", "N50", "N51"]
    france_lat_outlist = []
    france_long_list = ["W000", "W001", "W002", "W003", "W004", "W005", "E000", "E001", "E002", "E003", "E004", "E005", "E006", "E007", "E008", "E009"]

    with open(nh_out_file_path) as in_file:
        for line in in_file:
            for lat in france_lat_list:
                if lat in line:
                    print(line)
                    france_lat_outlist.append(line)
                else:
                    pass

    for lo in france_lat_outlist:
        for long in france_long_list:
            if long in lo:
                print(lo)
                out_file_france.write(lo)
            else:
                pass

    out_file_france.close()


# run the code
if __name__ == '__main__':

    # input variables needed / things to change
    in_csv = r'C:\Users\hjkristenson\PycharmProjects\Python39test\ConfigPopulation\InputURLs\vv_COH12_urls_summer.txt'
    nh_out_file_path = r'C:\Users\hjkristenson\PycharmProjects\Python39test\ConfigPopulation\InputURLs\vv_COH12_urls_summer_N.txt'
    conus_out_file_path = r'C:\Users\hjkristenson\PycharmProjects\Python39test\ConfigPopulation\InputURLs\vv_COH12_urls_summer_NW.txt'
    fr_out_file_path = r'C:\Users\hjkristenson\PycharmProjects\Python39test\ConfigPopulation\InputURLs\vv_COH12_urls_summer_France.txt'

    run_nh = 'False'
    run_conus = 'False'
    run_france = 'True'

    if run_nh == 'True':
        print('running n_hemi script')
        n_hemi(in_csv, nh_out_file_path)
    else:
        pass
    if run_conus == 'True':
        print('running select_conus script')
        select_conus(conus_out_file_path)
    else:
        pass
    if run_france == 'True':
        print('running select_france script')
        select_france(fr_out_file_path)
    else:
        pass


