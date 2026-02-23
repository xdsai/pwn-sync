import os
import json
import time
import logging
import subprocess
import threading

import requests
from flask import Flask, request, abort

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE_DIR, 'cfg', 'config.json')
UPLOADED_PATH = os.path.join(BASE_DIR, 'cfg', 'server_uploaded.json')
HANDSHAKE_DIR = os.path.join(BASE_DIR, 'handshakes')
FILES_DIR = os.path.join(BASE_DIR, 'files')
TAR_PATH = os.path.join(FILES_DIR, 'pwn_synced.tar')

OHC_API_URL = 'https://api.onlinehashcrack.com'


def load_config():
    with open(CFG_PATH, 'r') as f:
        return json.load(f)


config = load_config()

app = Flask(__name__, static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000  # 16MB


@app.route('/pwn-sync', methods=['POST'])
def receive_handshakes():
    if not request.files:
        abort(400)

    auth = json.loads(request.files['json'].read())
    if auth.get('pwn_auth_token') != config['auth_token']:
        app.logger.warning('Invalid auth token received')
        abort(403)

    if 'pwn_tar' in request.files:
        return _handle_tar_upload(request.files['pwn_tar'])

    if auth.get('status') == 'ended_transmission':
        app.logger.warning('Transmission completed')
        if config.get('auto_upload') == 'y':
            threading.Thread(target=upload_to_ohc, daemon=True).start()
        return 'Success', 200

    abort(400)


def _handle_tar_upload(tar_file):
    app.logger.warning('Received tarball, saving...')
    tar_file.save(TAR_PATH)

    result = subprocess.run(
        ['tar', 'xf', TAR_PATH, '--strip-components', '1', '-C', HANDSHAKE_DIR],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        app.logger.warning(f'Tar extraction failed: {result.stderr}')
        abort(400)

    app.logger.warning('Extracted tarball')
    return 'Success', 200


def upload_to_ohc():
    app.logger.warning('Starting auto-upload to OnlineHashCrack')
    email = config['email']
    webhook = config.get('webhook')

    with open(UPLOADED_PATH, 'r') as f:
        uploaded = json.load(f)

    stats = {'success': 0, 'already_uploaded': 0, 'no_handshake': 0, 'invalid_file': 0}
    count = 0
    start = time.time()

    for filename in os.listdir(HANDSHAKE_DIR):
        if not filename.endswith('.pcap') or filename in uploaded:
            continue

        filepath = os.path.join(HANDSHAKE_DIR, filename)
        try:
            with open(filepath, 'rb') as f:
                resp = requests.post(OHC_API_URL, data={'email': email}, files={'file': f}, timeout=30)

            if 'already sent' in resp.text:
                stats['already_uploaded'] += 1
            elif 'No valid EAPOL handshake or PMKID found' in resp.text:
                stats['no_handshake'] += 1
            elif 'File is not valid' in resp.text:
                stats['invalid_file'] += 1
            else:
                stats['success'] += 1

            uploaded.append(filename)
            count += 1
            time.sleep(0.5)

        except Exception as e:
            app.logger.warning(f'Failed to upload {filename}: {e}')

    with open(UPLOADED_PATH, 'w') as f:
        json.dump(uploaded, f)

    elapsed = round(time.time() - start)

    if webhook:
        embed = {
            'embeds': [{
                'title': 'Finished upload to OHC',
                'description': f'{count} .pcaps in {elapsed} seconds',
                'color': 3388927,
                'fields': [
                    {'name': 'Successful', 'value': str(stats['success']), 'inline': True},
                    {'name': 'Already uploaded', 'value': str(stats['already_uploaded']), 'inline': True},
                    {'name': 'No handshake', 'value': str(stats['no_handshake']), 'inline': True},
                    {'name': 'Invalid file', 'value': str(stats['invalid_file']), 'inline': True},
                ],
            }],
        }
        requests.post(webhook, json=embed, timeout=10)

    app.logger.warning('OHC upload complete')


if __name__ == '__main__':
    os.makedirs(HANDSHAKE_DIR, exist_ok=True)
    os.makedirs(FILES_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=int(config['port']))
