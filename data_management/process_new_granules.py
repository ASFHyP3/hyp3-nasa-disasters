import copy
import json
import traceback
from argparse import ArgumentParser
from os import environ
from pprint import pprint

import asf_search
import hyp3_sdk
from hyp3_sdk.exceptions import HyP3SDKError


def chunks(itr, n=200):
    for i in range(0, len(itr), n):
        yield itr[i:i + n]


def process_new_granules(config_file: str, prompt: bool = False, watch: bool = False):
    with open(config_file) as f:
        config = json.load(f)

    print(f'Processing new granules for project {config["project_name"]}\n')

    hyp3 = hyp3_sdk.HyP3(
        config['host'], username=environ.get('EDL_USERNAME'), password=environ.get('EDL_PASSWORD'), prompt=prompt
    )
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
    if prompt:
        input('\nPress Enter to proceed, or Ctrl-c to cancel')

    prepared_jobs = []
    for granule in granules_to_submit:
        job_dict = copy.deepcopy(config['job_spec'])
        job_dict['name'] = config['project_name']
        job_dict['job_parameters']['granules'] = [granule]
        prepared_jobs.append(job_dict)

    submitted = hyp3_sdk.Batch()
    for batch in chunks(prepared_jobs):
        try:
            submitted += hyp3.submit_prepared_jobs(batch)
        except HyP3SDKError:
            traceback.print_exc()
            pprint(batch)

    print(f'submitted {len(submitted)} jobs to {config["host"]}')
    if watch:
        submitted = hyp3.watch(submitted)

    return submitted


def main():
    parser = ArgumentParser()
    parser.add_argument('config_file')
    parser.add_argument('-y', '--yes', action='store_false',
                        help='Provide a yes response to all prompts to always proceed')
    parser.add_argument('-w', '--watch', action='store_true',
                        help='Watch all submitted jobs until completion')
    args = parser.parse_args()

    process_new_granules(args.config_file, prompt=args.yes, watch=args.watch)


if __name__ == '__main__':
    main()
