🖼️ This Docker image contains a YOLO (You Only Look Once) object detection service.

The service processes images to detect objects and returns the results. It downloads images from an AWS S3 bucket, performs object detection using YOLOv5, and uploads the results back to the S3 bucket. 
The service also logs prediction summaries to a MongoDB replica set.

🔍 Features:

🦾 YOLOv5-based object detection.
🌐 Flask-based API server for handling prediction requests.
☁️ Integration with AWS S3 for image storage and retrieval.
📊 Logs prediction results to MongoDB for tracking and analysis.
🐳 Dockerized for easy deployment and scalability.
