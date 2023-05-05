import boto3
import sys

aws_profile = "devops-sunvi"

aws_access_key_id = None
aws_secret_access_key = None
aws_region = "us-east-1"

boto3_client_s3 = None

bucket_name = "ourfancybucketsite"
index_file = "/tmp/index.html"

s3_site_endpoint = None
s3_bucket_name = None


def get_aws_credentials():
    import configparser
    import os

    global aws_profile

    global aws_access_key_id
    global aws_secret_access_key

    path = os.path.expanduser(
        "~") + os.path.join(os.sep, ".aws", "credentials")

    config = configparser.ConfigParser()
    config.read(path)

    if aws_profile in config.sections():
        aws_access_key_id = config[aws_profile]["aws_access_key_id"]
        aws_secret_access_key = config[aws_profile]["aws_secret_access_key"]
    else:
        print("Cannot find profile '{}' in {}".format(aws_profile, path), True)
        sys.exit()

    if aws_access_key_id is None or aws_secret_access_key is None:
        print("AWS config values not set in '{}' in {}".format(
            aws_profile, path), True)
        sys.exit()


def make_boto3_client():
    global boto3_client_s3

    try:
        boto3_client_s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )
    except Exception as e:
        print(e)
        sys.exit()


def create_bucket():
    global s3_site_endpoint
    global s3_bucket_name
    global bucket_name
    global index_file

    try:
        response = boto3_client_s3.create_bucket(
            ACL="public-read",
            Bucket=bucket_name,
            ObjectOwnership='ObjectWriter',
        )
    except boto3_client_s3.exceptions.BucketAlreadyExists as err:
        print("Bucket {} already exists.".format(
            err.response['Error']['BucketName']))
        sys.exit()

    policy = """{
        "Version": "2008-10-17",
        "Id": "PolicyForPublicWebsiteContent",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "*"
                },
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::ourfancybucketsite/*"
            }
        ]
    }""" % (bucket_name)

    try:
        boto3_client_s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=policy
        )
    except Exception as e:
        print(e)
        sys.exit()

    try:
        boto3_client_s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'ErrorDocument': {
                    'Key': 'index.html'
                },
                'IndexDocument': {
                    'Suffix': 'index.html'
                }
            }
        )
    except Exception as e:
        print(e)
        sys.exit()

    try:
        boto3_client_s3.get_bucket_website(Bucket=bucket_name)
    except Exception as e:
        print(e)
        sys.exit()

    s3_bucket_name = bucket_name + ".s3.amazonaws.com"
    boto3_client_s3.upload_file(
        index_file,
        bucket_name,
        "index.html",
        ExtraArgs={'ContentType': "text/html", 'ACL': "public-read"}
    )

    s3_site_endpoint = bucket_name + ".s3-website-" + aws_region + ".amazonaws.com"

    print(s3_site_endpoint)


def main():
    get_aws_credentials()
    make_boto3_client()
    create_bucket()

    get_website = boto3_client_s3.get_bucket_website(Bucket=bucket_name)
    print(get_website)


if __name__ == '__main__':
    main()
