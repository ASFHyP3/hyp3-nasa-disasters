from argparse import ArgumentParser

import boto3
import hyp3_sdk
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

S3 = boto3.resource('s3')


def get_args():
    parser = ArgumentParser()
    parser.add_argument('--target-bucket', default='hyp3-nasa-disasters')
    parser.add_argument('project_name')
    return parser.parse_args()


def object_exists(bucket, key):
    try:
        S3.Object(bucket, key).load()
    except ClientError:
        return False
    return True


def copy_object(source_bucket, source_key, target_bucket, target_key, chunk_size=104857600):
    bucket = S3.Bucket(target_bucket)
    copy_source = {'Bucket': source_bucket, 'Key': source_key}
    transfer_config = TransferConfig(multipart_threshold=chunk_size, multipart_chunksize=chunk_size)
    bucket.copy(CopySource=copy_source, Key=target_key, Config=transfer_config)


def main():
    args = get_args()

    hyp3 = hyp3_sdk.HyP3(prompt=True)
    jobs = hyp3.find_jobs(name=args.project_name)
    print(jobs)
    print(f'Found {len(jobs)} jobs to copy')

    for job in jobs:
        source_bucket = job.files[0]['s3']['bucket']
        zip_key = job.files[0]['s3']['key']
        for ext in ('_VV.tif', '_VH.tif', '_rgb.tif', '_VV.tif.xml'):
            source_key = zip_key.replace('.zip', ext)
            target_key = source_key.replace(job.job_id, job.name)
            if object_exists(args.target_bucket, target_key):
                print(f'{args.target_bucket + "/" + target_key} already exists, skipping')
            else:
                print(f'copying {source_bucket + "/" + source_key} to {args.target_bucket + "/" + target_key}')
                copy_object(source_bucket, source_key, args.target_bucket, target_key)


if __name__ == '__main__':
    main()
