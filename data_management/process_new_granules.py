import json
from argparse import ArgumentParser
from pprint import pprint

import asf_search
from hyp3_sdk import HyP3


parser = ArgumentParser()
parser.add_argument('-y', action='store_true')
parser.add_argument('config_file')
args = parser.parse_args()

with open(args.config_file) as f:
    config = json.load(f)

print(f'Processing new granules for project {config["project_name"]}\n')


hyp3 = HyP3(config['host'], prompt=True) if not args.y else HyP3(config['host'])

search_results = asf_search.geo_search(**config['search_parameters'])
all_granules = {result.geojson()['properties']['sceneName'] for result in search_results}

processed_jobs = hyp3.find_jobs(name=config['project_name'])
processed_granules = {job.job_parameters['granules'][0] for job in processed_jobs}

granules_to_submit = all_granules - processed_granules
print(f'\nFound {len(granules_to_submit)} new granules:')
for granule in granules_to_submit:
    print(granule)

print(f'\nFound {len(all_granules)} search results')
print(f'Found {len(processed_granules)} granules already processed')
print(f'\nSubmitting {len(granules_to_submit)} new {config["job_spec"]["job_type"]} jobs to HyP3 with parameters:')

pprint(config['job_spec']['job_parameters'])
if not args.y:
    input('\nPress Enter to proceed, Ctrl-c to cancel')


jobs = []
for granule in granules_to_submit:
    job_dict = config['job_spec'].copy()
    job_dict['name'] = config['project_name']
    job_dict['job_parameters']['granules'] = [granule]
    jobs.append(job_dict)
pprint(jobs)

exit()
def chunks(itr, n=200):
    for i in range(0, len(itr), n):
        yield itr[i:i + n]


for sub_list in chunks(jobs):
    batch = hyp3.submit_prepared_jobs(sub_list)

print(f'submitted {len(jobs)} jobs to hyp3')
