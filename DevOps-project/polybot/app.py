import flask
from flask import request
import os
from bot import ObjectDetectionBot, Bot, QuoteBot

app = flask.Flask(__name__)


TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']

TELEGRAM_TOKEN = ""
with open('/run/secrets/telegram_token_file', 'r') as file:
    TELEGRAM_TOKEN = ''.join(file.read().split('\n'))
    print(TELEGRAM_TOKEN)

@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


if __name__ == "__main__":
    bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)

    app.run(host='0.0.0.0', port=8443)
