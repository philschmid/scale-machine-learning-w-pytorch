try:
    import unzip_requirements
except ImportError:
    pass
from requests_toolbelt.multipart import decoder
import json
import torch
import torchvision
import torchvision.transforms as transforms
from PIL import Image
import io
import base64
import boto3
import os

# define env variables if there are not existing
BUCKET_NAME = os.environ['BUCKET_NAME'] if 'BUCKET_NAME' in os.environ else 'philschmid-models'
ITEM_NAME = os.environ['ITEM_NAME'] if 'ITEM_NAME' in os.environ else 'image_classifier/cardamage.pth'
MODEL_PATH = os.environ['MODEL_PATH'] if 'MODEL_PATH' in os.environ else './model/cardamage.pth'  # '/tmp/cardamage.pth'
# class list for predicition
CLASS_INDEX = ['damaged', 'not-damaged']


def get_model_from_s3():
    try:
        # checks if model already exists otherwise downloads it from s3
        if os.path.isfile(MODEL_PATH) != True:
            s3 = boto3.client('s3')
            s3.download_file(BUCKET_NAME, ITEM_NAME, MODEL_PATH)
        # loading pytorch model
        model = torch.load(MODEL_PATH, map_location=lambda storage, loc: storage)
        return model
    except Exception as e:
        raise(e)


model = get_model_from_s3()


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
    return CLASS_INDEX[predicted_idx]


# def detect_damage(event, context):

#     # content_type_header = event['headers']['content-type']
#     content_type_header = 'multipart/form-data; boundary=X-INSOMNIA-BOUNDARY'

#     post_data = base64.b64decode(event["body"])

#     # file = decoder.MultipartDecoder(body, content_type_header).parts[0].content
#     img_bytes = decoder.MultipartDecoder(
#         post_data, content_type_header).parts[0].content

#     prediction = get_prediction(image_bytes=img_bytes)
#     # print(response)
#     return {
#         'statusCode': 200,
#         'body': response
#     }


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
