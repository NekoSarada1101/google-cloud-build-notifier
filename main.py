import base64
import json
import logging
import os
import zoneinfo
from datetime import datetime, timedelta
from pprint import pformat

import google.cloud.logging
import requests

# 標準 Logger の設定
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger()

# Cloud Logging ハンドラを logger に接続
logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

# setup_logging() するとログレベルが INFO になるので DEBUG に変更
logger.setLevel(logging.DEBUG)


WEBHOOK_URL = os.environ['WEBHOOK_URL']
ICON_IMAGE_URL = os.environ['ICON_IMAGE_URL']
JST = zoneinfo.ZoneInfo('Asia/Tokyo')


def build_notify(event, context):
    try:
        logger.info('===== START cloud build notifier =====')
        logger.debug(f'event={pformat(event)}')
        logger.debug(f'context={pformat(context)}')

        logger.info('----- get pubsub event data -----')
        event_data_json = base64.b64decode(event['data']).decode('utf-8')
        logger.debug(f'event_data={event_data_json}')
        event_data = json.loads(event_data_json)

        if event_data['status'] not in ['SUCCESS', 'FAILURE']:
            logger.info('===== END cloud build notifier =====')
            return

        logger.info('----- create post content -----')
        headers = {'Content-Type': 'application/json'}
        content = f'''Build Status: **{event_data['status']}**'''
        embeds = [
            {
                'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                'color': 65280 if event_data['status'] == 'SUCCESS' else 16711680,
                'footer': {
                    'text': "Cloud Build Notifier",
                    'icon_url': ICON_IMAGE_URL
                },
                'author': {
                    'name': '@Google Cloud',
                    'url': f'https://console.cloud.google.com/home/dashboard?hl=ja&project={event_data["projectId"]}',
                    'icon_url': 'https://avatars.slack-edge.com/2019-10-30/817024818759_0abdf89bb617c3003b21_512.png'
                },
                'fields': [
                    {
                        'name': 'Build Log',
                        'value': f'[{event_data["id"]}]({event_data["logUrl"]})'
                    },
                    {
                        'name': 'Start at',
                        'value': str(datetime.strptime(event_data['startTime'][:event_data['startTime'].find('.')], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=9)),
                        'inline': True
                    },
                    {
                        'name': 'Finish at',
                        'value': str(datetime.strptime(event_data['finishTime'][:event_data['finishTime'].find('.')], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=9)),
                        'inline': True
                    },
                ]
            },
        ]

        body = {
            'username': 'Cloud Build Notifier',
            'avatar_url': ICON_IMAGE_URL,
            'content': content,
            'embeds': embeds
        }

        logger.debug(f'webhook_url={WEBHOOK_URL}')
        logger.debug(f'headers={pformat(headers)}')
        logger.debug(f'body={pformat(body)}')

        logger.info('----- post message -----')
        response = requests.post(WEBHOOK_URL, json.dumps(body), headers=headers)

        logger.debug(f'response.status={pformat(response.status_code)}')
        logger.info('===== END cloud build notifier =====')
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    build_notify('', '')
