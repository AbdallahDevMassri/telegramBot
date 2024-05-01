import time
from pathlib import Path
from flask import Flask, request, jsonify
from detect import run
from json import JSONEncoder
import uuid
import yaml
from loguru import logger
import os
import boto3
from flask_pymongo import PyMongo
from pymongo import MongoClient


images_bucket = os.environ['BUCKET_NAME']
image_name = ""


# connect to s3 and download an img 
def download_image_from_s3(image_key):
    s3 = boto3.client('s3')

    global image_name
    image_name = image_key
    
    local_path = f'{image_key}'
    try:
        s3.download_file(images_bucket, image_key, local_path)
        logger.info(f"Image '{image_key}' downloaded successfully to '{local_path}'")
        return local_path
    except Exception as e:
        logger.info(f"Error downloading image '{image_key}': {e}")

def upload_img_to_s3(image_path, prefix):
    s3 = boto3.client('s3')
    try:
        s3.upload_file(image_path, images_bucket, prefix+image_name)
        logger.info('image uploaded successfuly!')
    except Exception as e :
        logger.info(f"Error downloading image '{image_path}': {e}")

with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

app = Flask(__name__)

@app.route('/', methods=['POST'])
def index():
	return 'from index , with success'

@app.route('/predict', methods=['POST'])
def predict():
    # Generates a UUID for this current prediction HTTP request. This id can be used as a reference in logs to identify and track individual prediction requests.
    prediction_id = str(uuid.uuid4())

    logger.info(f'prediction: {prediction_id}. start processing')

    # Receives a URL parameter representing the image to download from S3
    img_name = request.args.get('imgName')
    # original_img_path = ...

    # TODO download img_name from S3, store the local image path in original_img_path
    original_img_path = download_image_from_s3(img_name)
    
    #  The bucket name should be provided as an env var BUCKET_NAME.

    logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')

    # Predicts the objects in the image
    run(
        weights='yolov5s.pt',
        data='data/coco128.yaml',
        source=original_img_path,
        project='static/data',
        name=prediction_id,
        save_txt=True
    )

    logger.info(f'prediction: {prediction_id}/{original_img_path}. done')

    # This is the path for the predicted image with labels
    # The predicted image typically includes bounding boxes drawn around the detected objects, along with class labels and possibly confidence scores.
    predicted_img_path = Path(f'static/data/{prediction_id}/{original_img_path}')

    # TODO Uploads the predicted image (predicted_img_path) to S3 (be careful not to override the original image).
    upload_img_to_s3(predicted_img_path, "predicted_")

    # Parse prediction labels and create a summary
    pred_summary_path = Path(f'static/data/{prediction_id}/labels/{original_img_path.split(".")[0]}.txt')
    if pred_summary_path.exists():
        with open(pred_summary_path) as f:
            labels = f.read().splitlines()
            labels = [line.split(' ') for line in labels]
            labels = [{
                'class': names[int(l[0])],
                'cx': float(l[1]),
                'cy': float(l[2]),
                'width': float(l[3]),
                'height': float(l[4]),
            } for l in labels]

        logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')

        prediction_summary = {
            'prediction_id': f'{prediction_id}',
            'original_img_path': f'{original_img_path}',
            'predicted_img_path': f'{predicted_img_path}',
            'labels': labels,
            'time': time.time()
        }
        

        members = ["mongo1:27017", "mongo2:27018", "mongo3:27019"]
        inserted_id = ""

        for member in members :
            try:
                logger.info("start adding files to mongo db")
                client = MongoClient(f"mongodb://{member}/yolo?replicaSet=myReplicaSet&timeoutMS=10000")
                db = client["yolo"]
                collection = db["predicted"]
                inserted_id = collection.insert_one(prediction_summary).inserted_id
                prediction_summary['_id'] = str(inserted_id)
                logger.info(f'prediction: {prediction_id}/{original_img_path}. Prediction summary stored SUCCESSFULY in MongoDB.')
                
                try:
                    logger.info(f"inserted object {collection.find({'prediction_id':prediction_id})}")
                except:
                    logger.info("Failed to find object in mongoDB!")
                break

            except Exception as e:
                logger.error(f"Failed to store prediction summary in MongoDB: {e}")

        return prediction_summary

    else:
        response = jsonify(message=f'prediction: {prediction_id}/{original_img_path}. prediction result not found')
        response.status_code = 404
        return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
