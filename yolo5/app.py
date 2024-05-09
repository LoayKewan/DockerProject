import time
from pathlib import Path
import json
from flask import Flask, request
from detect import run
import uuid
import yaml
from loguru import logger
import os
import boto3
from pymongo import MongoClient
from bson import json_util



import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def connect_to_mongodb(connection_string):
    try:
        client = MongoClient(connection_string)
        logger.info("Connected to MongoDB successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def get_primary_node():
    try:
        # Connect to one of the nodes in the replica set
        client = MongoClient('mongodb://mongo_1:27017,mongo_2:27017,mongo_3:27017/?replicaSet=myReplicaSet')

        # Get the admin database
        admin_db = client.admin

        # Run the isMaster command to get the replica set status
        ismaster_result = admin_db.command('ismaster')

        # Check if the current node is the primary
        if ismaster_result['ismaster']:
            return client
        else:
            return None
    except Exception as e:
        logger.error(f"An error occurred while determining the primary node: {e}")
        return None

def create_collection(db, collection_name):
    try:
        if collection_name in db.list_collection_names():
            logger.info(f"Collection '{collection_name}' already exists. Dropping...")
            db.drop_collection(collection_name)
            logger.info(f"Collection '{collection_name}' dropped.")
        db.create_collection(collection_name)
        logger.info(f"Collection '{collection_name}' created.")
    except Exception as e:
        logger.error(f"Failed to create collection '{collection_name}': {e}")
        raise



def insert_data(collection, data):
    try:
        collection.insert_one(data)
        logger.info("Data inserted successfully.")
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
        raise





images_bucket = os.environ['BUCKET_NAME']

with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route('/predict', methods=['POST'])
def predict():
    # Generates a UUID for this current prediction HTTP request. This id can be used as a reference in logs to identify and track individual prediction requests.
    prediction_id = str(uuid.uuid4())
    logger.info(f'prediction: {prediction_id}. start processing')
    # Receives a URL parameter representing the image to download from S3
    img_name = request.json.get('imgName')
    logger.info(f'img_name is recived is {img_name}')
    photo_S3_name = img_name.split("/")


    file_path_pic_download = os.getcwd() + "/" + str(photo_S3_name[1])
    logger.info(file_path_pic_download)
    client = boto3.client('s3')
    client.download_file(images_bucket, str(photo_S3_name[1]) , file_path_pic_download)
    


    # TODO download img_name from S3, store the local image path in the original_img_path variable.
    #  The bucket name is provided as an env var BUCKET_NAME.

    #original_img_path = file_path_pic_download
    original_img_path = file_path_pic_download
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
    path = Path(f'static/data/{prediction_id}/{str(photo_S3_name[1])}')
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        pass
    predicted_img_path = Path(f'static/data/{prediction_id}/{str(photo_S3_name[1])}')
    path_str = str(predicted_img_path)
    json_str = json.dumps({"path": path_str})
    json_data = json.loads(json_str)
    unique_filename = str(uuid.uuid4()) + '.jpeg'
    client.upload_file(json_data["path"], images_bucket, unique_filename)
    # TODO Uploads the predicted image (predicted_img_path) to S3 (be careful not to override the original image).
    


    




    # Parse prediction labels and create a summary
    path = Path(f'static/data/{prediction_id}/labels/{photo_S3_name[1].split(".")[0]}.txt')
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        pass
    pred_summary_path = Path(f'static/data/{prediction_id}/labels/{photo_S3_name[1].split(".")[0]}.txt')
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

            logger.info(f'prediction: {prediction_id}/{photo_S3_name[1]}. prediction summary:\n\n{labels}')

            prediction_summary = {
                'prediction_id': prediction_id,
                'original_img_path': photo_S3_name[1],
                'predicted_img_path': json_data["path"],
                'labels': labels,
                'time': time.time()
            }


            primary_client = None  # Initialize primary_client variable outside try block


            try:
                logger.info("Determining the primary node...")
                primary_client = get_primary_node()
                logger.info(f'*****{primary_client}*****')
                if primary_client:
                    logger.info("Primary node found.")
                    db = primary_client['mydatabase']
                    collection_name = 'prediction'
                            
                    create_collection(db, collection_name)
                    
                    collection = db[collection_name]
                    logger.info("Inserting data...")
                
            
                    insert_data(collection, prediction_summary)

                    doc = collection.find_one({})
                    json_doc = json.dumps(doc, default=json_util.default)

                    return json_doc


                else:
                    logger.error("Primary node not found.")
            except Exception as e:
                logger.info(f"An error occurred: {e}")
            finally:
                if primary_client:
                    primary_client.close()            

            logger.info(prediction_summary)

             

            #return prediction_summary
    else:
        return f'prediction: {prediction_id}/{photo_S3_name[1]}. prediction result not found', 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
