import hyp3_sdk as sdk
import boto3


hyp3 = sdk.HyP3(prompt=True)

print('input project name to copy:')
project_name = input()
jobs = hyp3.find_jobs(name=project_name)
print(f'found {len(jobs)} jobs to copy')

print('input destination bucket:')
DEST_BUCKET = input()
S3 = boto3.client('s3')

for job in jobs:
    job_bucket = job.files[0]['s3']['bucket']
    job_key = job.files[0]['s3']['key']
    for ext in ('_VV.tif', '_VH.tif', '_rgb.tif', '_VV.tif.xml'):
        file_key = job_key.replace('.zip', ext)
        dest_key = file_key.replace(job.job_id, job.name)
        print(f'copying {job_bucket + "/" + job_key} to {DEST_BUCKET + "/" + dest_key}')
        S3.copy_object(Bucket=DEST_BUCKET, Key= dest_key,
                       CopySource={'Bucket': job_bucket, 'Key': file_key})