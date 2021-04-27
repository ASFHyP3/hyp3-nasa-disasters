import json
from argparse import ArgumentParser
from pprint import pprint

import asf_search
from hyp3_sdk import HyP3


parser = ArgumentParser()
parser.add_argument('config_file')
args = parser.parse_args()

with open(args.config_file) as f:
    config = json.load(f)

print(f'Processing new granules for project {config["project_name"]}\n')

hyp3 = HyP3(prompt=True)

search_results = asf_search.geo_search(**config['search_parameters'])
all_granules = {result.geojson()['properties']['sceneName'] for result in search_results}

processed_jobs = hyp3.find_jobs(name=config['project_name'])
processed_granules = {job.job_parameters['granules'][0] for job in processed_jobs.jobs}

granules_to_submit = all_granules - processed_granules
print(f'\nFound {len(granules_to_submit)} new granules:')
for granule in granules_to_submit:
    print(granule)

print(f'\nFound {len(all_granules)} search results')
print(f'Found {len(processed_granules)} granules already processed')
print(f'\nSubmitting {len(granules_to_submit)} new RTC jobs to HyP3 with parameters:')
pprint(config['job_parameters'])
input('\nPress Enter to proceed, Ctrl-c to cancel')

for granule in granules_to_submit:
    batch = hyp3.submit_rtc_job(
        granule=granule,
        name=config['project_name'],
        **config['job_parameters'],
    )
    print(f'Submitted RTC job for {granule}')
