# (C) British Crown Copyright 2017, Met Office
"""
A command-line utility to poll an SQS queue for S3 events delivered via
SNS, and download the corresponding objects.

"""
import argparse
import json
import os.path

import boto3


DOWNLOAD_DIR = 'objects'
S3 = boto3.client('s3')


def download_object(bucket_name, object_key, verbose):
    if not os.path.exists(DOWNLOAD_DIR):
        os.mkdir(DOWNLOAD_DIR)
    target_path = os.path.join(DOWNLOAD_DIR, object_key)
    if verbose:
        print('Downloading s://{}/{} to {}'.format(bucket_name, object_key,
                                                   target_path))
    bucket_region = S3.get_bucket_location(
        Bucket=bucket_name)['LocationConstraint']
    regional_s3 = boto3.client('s3', region_name=bucket_region)
    regional_s3.download_file(bucket_name, object_key, target_path)


def download_from_queue(queue_name, keep_messages, verbose):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    if verbose:
        print("Using: {}".format(queue.url))
    while True:
        if verbose:
            print("Checking...")
        for message in queue.receive_messages(WaitTimeSeconds=2):
            sns_notification = json.loads(message.body)

            # Production code should verify the SNS signature before
            # proceeding.

            s3_event = json.loads(sns_notification['Message'])
            for record in s3_event['Records']:
                bucket_name = record['s3']['bucket']['name']
                object_key = record['s3']['object']['key']
                download_object(bucket_name, object_key, verbose)

            if not keep_messages:
                message.delete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download objects identified in S3 events delivered'
                    ' to an SQS queue.')
    parser.add_argument('queue_name')
    parser.add_argument('-k', '--keep', action='store_true',
                        help='Retain messages in SQS queue after processing.'
                             ' (Useful when debugging.)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on verbose output.')
    args = parser.parse_args()
    download_from_queue(args.queue_name, args.keep, args.verbose)
