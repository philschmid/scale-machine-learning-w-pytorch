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
class_index = ['damaged', 'not-damaged']


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
    return class_index[predicted_idx]


def detect_damage(event, context):

    # content_type_header = event['headers']['content-type']
    # body = event["body"].encode()
    content_type_header = 'multipart/form-data; boundary=X-INSOMNIA-BOUNDARY'

    post_data = base64.b64decode(event["body"])

    # file = decoder.MultipartDecoder(body, content_type_header).parts[0].content
    img_bytes = decoder.MultipartDecoder(
        post_data, content_type_header).parts[0].content

    prediction = get_prediction(image_bytes=event["body2"])
    prediction = get_prediction(image_bytes=img_bytes)
    # print(response)
    return {
        'statusCode': 200,
        'body': response
    }

# def detect_damage(event, context):
#     try:
#         file = event['body']
#         print(img_bytes)
#         prediction = get_prediction(image_bytes=img_bytes)
#         return {
#             "statusCode": 200,
#             "headers": {
#                 'Content-Type': 'application/json',
#                 'Access-Control-Allow-Origin': '*',
#                 "Access-Control-Allow-Credentials": True

#             },
#             "body": json.dumps({'predicted': prediction})
#         }
#     except Exception as e:
#         print(repr(e))
#         return {
#             "statusCode": 500,
#             "headers": {
#                 'Content-Type': 'application/json',
#                 'Access-Control-Allow-Origin': '*',
#                 "Access-Control-Allow-Credentials": True
#             },
#             "body": event['body']
#             # "body": json.dumps({"error": repr(e)})
#         }
