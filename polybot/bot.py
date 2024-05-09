import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
import requests
import boto3
import requests
import json
from polybot.img_proc import Img

images_bucket = os.environ['BUCKET_NAME']


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

    def is_current_msg_photo(self, msg):
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

        self.telegram_bot_client.send_photo(chat_id, InputFile(img_path))

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class ObjectDetectionBot(Bot):

    def __init__(self, token, telegram_chat_url):
        super().__init__(token, telegram_chat_url)

    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if "text" in msg and msg["text"] == "hi":
            self.send_text(msg['chat']['id'],
                           f'Hi : {msg["first_name"]} {msg["last_name"]} , how i can help you ?  \n ')

        elif msg["text"] != "hi":
            self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')
        else:
            if "caption" in msg:
                try:
                    img_path = self.download_user_photo(msg)
                    if msg["caption"] == "Blur":
                        self.send_text(msg['chat']['id'], "Blur filter in progress")
                        new_img = Img(img_path)
                        new_img.blur()
                        new_path = new_img.save_img()
                        self.send_photo(msg["chat"]["id"], new_path)
                        self.send_text(msg['chat']['id'], "Blur filter applied")
                    elif msg["caption"] == "Contour":
                        self.send_text(msg['chat']['id'], "Contour filter in progress")
                        new_img = Img(img_path)
                        new_img.contour()
                        new_path = new_img.save_img()
                        self.send_photo(msg["chat"]["id"], new_path)
                        self.send_text(msg['chat']['id'], "Contour filter applied")
                    elif msg["caption"] == "Salt and pepper":
                        self.send_text(msg['chat']['id'], "Salt and pepper filter in progress")
                        new_img = Img(img_path)
                        new_img.salt_n_pepper()
                        new_path = new_img.save_img()
                        self.send_photo(msg["chat"]["id"], new_path)
                        self.send_text(msg['chat']['id'], "Salt and pepper filter applied")
                    elif msg["caption"] == "rotate":
                        self.send_text(msg['chat']['id'], "rotate filter in progress")
                        new_img = Img(img_path)
                        new_img.rotate()
                        new_path = new_img.save_img()
                        self.send_photo(msg["chat"]["id"], new_path)
                        self.send_text(msg['chat']['id'], "rotate filter applied")

                    else:
                        self.send_text(msg['chat']['id'], f'error , Need to choose a valid caption')
                except Exception as e:
                    logger.info(f"Error {e}")
                    self.send_text(msg['chat']['id'], f'failed - try again later')
            else:
                self.send_text(msg['chat']['id'], f'failed - Please Provide Caption')

        if self.is_current_msg_photo(msg) and msg["caption"] == "predict": :
            photo_path = self.download_user_photo(msg)
            logger.info(f'Photo downloaded to: {photo_path}')
            photo_S3_name = photo_path.split("/")
            # Upload the photo to S3
            client = boto3.client('s3')
            client.upload_file(photo_path, images_bucket, photo_S3_name[1])

            # Send an HTTP request to the YOLO5 service for prediction
            yolo5_url = "http://my_yolo5_test:8081/predict"
            headers = {'Content-Type': 'application/json'}
            image_filename = photo_path
            json_data = {'imgName': image_filename}

            response_data = None  # Initialize response_data variable

            try:
                # Send an HTTP POST request to the YOLO5 service
                response = requests.post(yolo5_url, headers=headers, json=json_data)

                # Logging the status code for debugging
                logger.info(f"Response status code: {response.status_code}")

                # Check the response status code
                if response.status_code == 200:
                    response_data = json.loads(response.text)

                    # Extract label values from the response data
                    labels = response_data.get('labels', [])

                    if not labels:  # Check if labels list is empty
                        logger.error("Labels not found in response data.")
                        self.send_text(msg['chat']['id'], "Labels not found in response data. Please try again.")
                    else:

                        # Count the occurrences of each class value
                        class_counts = {}
                        for label in labels:
                            class_value = label.get('class')  # Assuming 'class' key contains the class value
                            class_counts[class_value] = class_counts.get(class_value, 0) + 1

                        # Send class counts to the chat or log them
                        for class_value, count in class_counts.items():
                            message = f"{class_value}: {count} "
                            self.send_text(msg['chat']['id'], message)
                            # Alternatively, you can log the counts
                            logger.info(message)

                    logger.info("Prediction request sent successfully.")
                else:
                    logger.error(f"Prediction request failed with status code: {response.status_code}")
                    self.send_text(msg['chat']['id'], f'somthing is went wrong ...please try again')

            except Exception as e:
                logger.error(f"Error occurred: {e}")
                self.send_text(msg['chat']['id'], f'somthing is went wrong ...please try again')

        else:
            logger.info('Not a photo message, ignoring.')
