import torch
import boto3


def upload_model(model_path='', s3_bucket='', key_prefix='', aws_profile='default'):
    s3 = boto3.session.Session(profile_name=aws_profile)
    client = s3.client('s3')
    client.upload_file(model_path, s3_bucket, key_prefix)


if __name__ == "__main__":
    model_path = './cardamage.tar.gz'
    s3_bucket = 'philschmid-models'
    key_prefix = 'image_classifier/cardamage.tar.gz'
    upload_model(model_path, s3_bucket, key_prefix)
