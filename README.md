# Cross-account notification & download of S3 objects.
A demo of downloading S3 objects in response to SNS messages via an SQS queue.

By following these instructions you will subscribe an SQS queue in one
AWS account to an SNS topic in a separate AWS account. You will then run
a Python script to monitor the SQS queue for S3 events and download the
corresponding objects from the S3 bucket.

## Pre-requisites

* An AWS account containing an S3 bucket and an SNS topic that publishes
  object creation events from that S3 bucket. This AWS account will be
  referred to as the "publishing account".
* Another AWS account where you can create a new SQS queue and IAM user.
  This account will be referred to as the "subscribing account".
* A Python 3 environment containing the boto3 library.

## Getting started

1. [Request access](#request-access) to the S3 objects and SNS topic in
   the publishing account. This will require the subscribing account ID.
   Once the publishing account has configured the correct access they
   will reply with:
   - the S3 bucket name,
   - the SNS topic ARN.
2. [Create an SQS queue](#create-sqs-queue) in the subscribing account,
   with a policy that allows the publishing account's SNS topic to send
   messages to the queue.
3. [Configure access](#configure-access) credentials and permissions in
   the subscribing account.
4. [Start polling the SQS queue](#polling-the-sqs-queue)
5. [Subscribe the SQS queue to the SNS topic](#subscribe-to-the-sns-topic).

### Request access

The publishing account will:

- Update the S3 bucket policy to give the subscribing account read
  access:
```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::<subscribing-account-ID>:root"
  },
  "Action": [
    "s3:GetBucketLocation"
  ],
  "Resource": [
    "arn:aws:s3:::<bucket-name>"
  ]
},
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::<subscribing-account-ID>:root"
  },
  "Action": [
    "s3:GetObject"
  ],
  "Resource": [
    "arn:aws:s3:::<bucket-name>/*"
  ]
}
```
- Update the SNS topic policy to give the subscribing account permission
  to subscribe:
```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS":"<subscribing-account-ID>"
  },
  "Action": "sns:Subscribe",
  "Resource": "<topic-ARN>"
}
```
- Provide you with the S3 bucket name and the SNS topic ARN. These are
  shown in the following descriptions by `<bucket-name>` and
  `<topic-ARN>` respectively.


### Create SQS queue

Create an SQS queue in the subscribing account. Ensure the SQS queue's
access policy includes the following statement:

```json
{
  "Effect": "Allow",
  "Principal": "*",
  "Action": "SQS:SendMessage",
  "Resource": "arn:aws:sqs:eu-west-2:<subscribing-account-ID>:<queue-name>",
  "Condition": {
    "StringEquals": {
      "aws:SourceArn": "<topic-ARN>"
    }
  }
}
```

### Configure access

Create an IAM user in the subscribing account with an access key ID and
secret access key. [Configure boto3](http://boto3.readthedocs.io/en/latest/guide/configuration.html)
to use these new credentials.

Ensure the IAM user has the following permissions:
- `s3:GetBucketLocation`
- `s3:GetObject` for the S3 bucket in the publishing account.
- `sns:Subscribe` for the SNS topic in the publishing account.
- `sqs:DeleteMessage` and `sqs:ReceiveMessage` for the SQS queue.

As a short-term measure, you can attach the AWS managed policies
`AmazonS3ReadOnlyAccess`, `AmazonSNSFullAccess` and
`AmazonSQSFullAccess` to the IAM user, but this gives the IAM user more
privileges than are strictly necessary, so it is not recommended for
ongoing usage.


### Polling the SQS queue

Clone this repository and ensure it is the current directory. Execute
the `download.py` script, passing it the name of the SQS queue, to begin
polling the SQS queue. No events are being delivered to the SQS queue
yet so no files will be downloaded.

```
$ python download.py <queue-name> -v -k
Using: https://eu-west-2.queue.amazonaws.com/<subscribing-account-ID>/<queue-name>
Checking...
Checking...
Checking...
```


### Subscribe to the SNS topic

Subscribe the SQS queue to the SNS topic. This can be done through the
AWS console or via the command line:

```
aws sns subscribe --topic-arn <topic-ARN> --protocol sqs --notification-endpoint <queue-ARN>
```

As soon as the subscription is complete, any events being published to
the SNS topic will start to arrive in the SQS queue and be processed by
the `download.py` script.
