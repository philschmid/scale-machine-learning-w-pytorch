try:
    import unzip_requirements
except ImportError:
    pass
from requests_toolbelt.multipart import decoder
import torch
import torchvision
import torchvision.transforms as transforms
from PIL import Image

import boto3
import os
import tarfile
import io
import base64
import json


# define env variables if there are not existing
S3_BUCKET = os.environ['S3_BUCKET'] if 'S3_BUCKET' in os.environ else 'philschmid-models'
MODEL_PATH = os.environ['MODEL_PATH'] if 'MODEL_PATH' in os.environ else './model/cardamage.tar.gz'  # 'image_classifier/cardamage.tar.gz'
# class list for predicition

# load the S3 client when lambda execution context is created
s3 = boto3.client('s3')


def load_model_from_s3():
    # # Load tensor from io.BytesIO object
    # >>> with open('tensor.pt', 'rb') as f:
    #         buffer = io.BytesIO(f.read())
    # >>> torch.load(buffer)
    try:
        if os.path.isfile(MODEL_PATH) != True:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=MODEL_PATH)
            bytestream = io.BytesIO(obj['Body'].read())
            tar = tarfile.open(fileobj=bytestream, mode="r:gz")
        else:
            tar = tarfile.open('./model/cardamage.tar.gz')
        for member in tar.getmembers():
            if member.name.endswith(".txt"):
                print("Classes file is :", member.name)
                f = tar.extractfile(member)
                classes = [classes.decode() for classes in f.read().splitlines()]
                print(classes)
            if member.name.endswith(".pth"):
                print("Model file is :", member.name)
                f = tar.extractfile(member)
                print("Loading PyTorch model")
                # model = torch.jit.load(io.BytesIO(f.read()), map_location=torch.device('cpu')).eval()
                model = torch.load(io.BytesIO(f.read()), map_location=lambda storage, loc: storage)
        return model, classes
    except Exception as e:
        print(repr(e))
        raise(e)


model, classes = load_model_from_s3()


def transform_image(image_bytes):
    try:
        transformations = transforms.Compose([
            transforms.Resize(255),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
        image = Image.open(io.BytesIO(image_bytes))
        return transformations(image).unsqueeze(0)
    except Exception as e:
        print(repr(e))
        raise(e)


def get_prediction(image_bytes):
    tensor = transform_image(image_bytes=image_bytes)
    outputs = model.forward(tensor)
    _, y_hat = outputs.max(1)
    predicted_idx = y_hat.item()
    return classes[predicted_idx]


def detect_damage(event, context):
    try:
            # content_type_header = event['headers']['content-type']
        content_type_header = 'multipart/form-data; boundary=X-INSOMNIA-BOUNDARY'

        body = base64.b64decode(event["body"])

        picture = decoder.MultipartDecoder(body, content_type_header).parts[0]
        prediction = get_prediction(image_bytes=picture.content)

        filename = picture.headers[b'Content-Disposition'].decode().split(';')[1].split('=')[1]
        if len(filename) < 4:
            filename = picture.headers[b'Content-Disposition'].decode().split(';')[2].split('=')[1]

        return {
            "statusCode": 200,
            "headers": {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                "Access-Control-Allow-Credentials": True

            },
            "body": json.dumps({'file': filename.replace('"', ''), 'predicted': prediction})
        }
    except Exception as e:
        print(repr(e))
        return {
            "statusCode": 500,
            "headers": {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                "Access-Control-Allow-Credentials": True
            },
            "body": event['body']
            # "body": json.dumps({"error": repr(e)})
        }
