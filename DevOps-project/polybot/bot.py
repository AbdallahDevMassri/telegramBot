import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
import boto3
import requests

class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    @staticmethod
    def is_current_msg_photo(msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ObjectDetectionBot(Bot):
    def __init__(self, token, telegram_chat_url):
        super().__init__(token, telegram_chat_url)
        self.aws_bucket = os.environ['BUCKET_NAME']
        self.yolo_ip_addr = os.environ['YOLO_IP_SERVICE']

    def upload_photo_to_s3(self, image_path, images_bucket, image_name):
        s3 = boto3.client('s3')
        try:
            s3.upload_file(image_path, images_bucket, image_name)
            logger.info('image uploaded successfuly!')
        except Exception as e :
            logger.info(f"Error downloading image '{image_path}': {e}")
    
    def formated_msg(self, lst_of_dct):
        res_dct = {}
        for i in lst_of_dct:
            if i['class'] in res_dct:
                res_dct[i['class']] += 1
            else:
                res_dct[i['class']] = 1
        return res_dct
    
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if ObjectDetectionBot.is_current_msg_photo(msg):
            
            # TODO download the user photo (utilize download_user_photo)
            photo_path = self.download_user_photo(msg)
            
            # TODO upload the photo to S3
            image_name = f"{msg['photo'][-1]['file_unique_id']}.jpg"
            self.upload_photo_to_s3(photo_path, self.aws_bucket, image_name)
            
            logger.info(f'FROM BOT: IMAGE UPLOADED SUCCESSFULY!')
            # TODO send a request to the `yolo5` service for prediction
            URL = f"http://{self.yolo_ip_addr}:8081/predict"

            PARAMS = {'imgName' : image_name}
                        
            time_out = 15
            
            i = 3
            while i != 0:
                try:
                    response = requests.post(URL, params=PARAMS, timeout=time_out)
                    if response.status_code == 200:
                        logger.info('FROM BOT: REQUEST SENT TO YOLO SERVICE SUCCESSFULY!')
                        data = response.json()

                        logger.info('TRYING TO PARSE PREDICTED DATA TO JSON!')
                        
                        objects_in_photo = self.formated_msg(data['labels'])
                        
                        res = ""
                        for i in objects_in_photo:
                            res += f'{i}: {objects_in_photo[i]}\n' 
                        
                        self.send_text(msg['chat']['id'], f'Detected objects: \n{res}')
                    break
                except Exception as e:
                    i -= 1
                    logger.info(f"Failed to connect to yolo service! Error: {e}")
                    if i != 0 :
                        logger.info("trying again ...")

            else:
                logger.info('FAILED TO CONNECT TO YOLO SERVICE!')
            # TODO send results to the Telegram end-user
                self.send_text(msg['chat']['id'], "Sorry somthing went wrong with our servers, pls try again.")
        else:
            self.send_text(msg['chat']['id'], "Sorry I can handle just messages as images!.")