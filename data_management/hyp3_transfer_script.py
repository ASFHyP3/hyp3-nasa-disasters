import json
from argparse import ArgumentParser
from os import environ

import boto3
import hyp3_sdk
from boto3.s3.transfer import TransferConfig

S3 = boto3.resource('s3')


def get_project_contents(bucket, prefix) -> set:
    project_contents = set()
    for o in S3.Bucket(bucket).objects.filter(Prefix=f'{prefix}/'):
        project_contents.add(o.key)
    return project_contents


def copy_object(source_bucket, source_key, target_bucket, target_key, chunk_size=104857600):
    print(f'copying {source_bucket + "/" + source_key} to {target_bucket + "/" + target_key}')
    bucket = S3.Bucket(target_bucket)
    copy_source = {'Bucket': source_bucket, 'Key': source_key}
    transfer_config = TransferConfig(multipart_threshold=chunk_size, multipart_chunksize=chunk_size)
    bucket.copy(CopySource=copy_source, Key=target_key, Config=transfer_config)


def hyp3_transfer_script(config_file: str, prompt: bool = False):
    with open(config_file) as f:
        config = json.load(f)

    hyp3 = hyp3_sdk.HyP3(
        config['host'], username=environ.get('EDL_USERNAME'), password=environ.get('EDL_PASSWORD'), prompt=prompt
    )

    project_name = config["project_name"]
    target_bucket = config["transfer_spec"]["target_bucket"]
    target_prefix = config["transfer_spec"].get("target_prefix", project_name)
    if prompt:
        project_name = input(f'HyP3 project name [{project_name}]: ') or project_name
        target_bucket = input(f'Destination bucket: [{target_bucket}]') or target_bucket
        target_prefix = input(f'Destination prefix: [{target_prefix}]') or target_prefix

    jobs = hyp3.find_jobs(name=project_name)
    print('\n' + project_name)
    print(jobs)

    print('\nLooking for new files to copy...')

    objects_to_copy = []
    project_contents = get_project_contents(target_bucket, target_prefix)
    for job in jobs:
        if not job.succeeded():
            continue
        source_bucket = job.files[0]['s3']['bucket']
        zip_key = job.files[0]['s3']['key']
        for ext in config["transfer_spec"]["extensions"]:
            source_key = zip_key.replace('.zip', ext)
            target_key = source_key.replace(job.job_id, target_prefix)
            if target_key not in project_contents:
                objects_to_copy.append({
                    'source_bucket': source_bucket,
                    'source_key': source_key,
                    'target_bucket': target_bucket,
                    'target_key': target_key,
                })

    print(f'\nFound {len(objects_to_copy)} new files to copy to s3://{target_bucket}/{target_prefix}/')
    input('Press Enter to continue, Ctrl-c to cancel')

    for object_to_copy in objects_to_copy:
        copy_object(**object_to_copy)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('config_file')
    parser.add_argument('-y', '--yes', action='store_false',
                        help='Provide a yes response to all prompts to always proceed')
    args = parser.parse_args()

    hyp3_transfer_script(args.config_file, prompt=args.yes)

