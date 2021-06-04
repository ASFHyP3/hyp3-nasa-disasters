import json
from argparse import ArgumentParser

import boto3
import hyp3_sdk
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

S3 = boto3.resource('s3')


def object_exists(bucket, key):
    try:
        S3.Object(bucket, key).load()
    except ClientError:
        return False
    return True


def copy_object(source_bucket, source_key, target_bucket, target_key, chunk_size=104857600):
    print(f'copying {source_bucket + "/" + source_key} to {target_bucket + "/" + target_key}')
    bucket = S3.Bucket(target_bucket)
    copy_source = {'Bucket': source_bucket, 'Key': source_key}
    transfer_config = TransferConfig(multipart_threshold=chunk_size, multipart_chunksize=chunk_size)
    bucket.copy(CopySource=copy_source, Key=target_key, Config=transfer_config)


def hyp3_transfer_script(config_file: str, prompt: bool = False):
    with open(config_file) as f:
        config = json.load(f)

    hyp3 = hyp3_sdk.HyP3(config['host'], prompt=prompt)

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
    for job in jobs:
        if not job.succeeded():
            continue
        source_bucket = job.files[0]['s3']['bucket']
        zip_key = job.files[0]['s3']['key']
        for ext in config["transfer_spec"]["extensions"]:
            source_key = zip_key.replace('.zip', ext)
            target_key = source_key.replace(job.job_id, target_prefix)
            if not object_exists(target_bucket, target_key):
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

    hyp3_transfer_script(args.cofig_file, prompt=args.yes)

