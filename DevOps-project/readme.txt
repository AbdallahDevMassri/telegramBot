This Docker image contains a YOLO (You Only Look Once) object detection service.
The service processes images to detect objects and returns the results.
It downloads images from an AWS S3 bucket, performs object detection using YOLOv5, and uploads the results back to the S3 bucket.
The service also logs prediction summaries to a MongoDB replica set.

Features:
- YOLOv5-based object detection.
- Flask-based API server for handling prediction requests.
- Integration with AWS S3 for image storage and retrieval.
- Logs prediction results to MongoDB for tracking and analysis.
- Dockerized for easy deployment and scalability.


#you need to create a file .env to declare the enviroment variable 

TELEGRAM_APP_URL= 
BUCKET_NAME=
YOLO_IP_SERVICE=yolo_service
TELEGRAM_TOKEN=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

#run this command to apply the variables 
docker-compose --env-file .env up --build
#this command is to start ngrok 
ngrok http 8443
