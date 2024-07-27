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
