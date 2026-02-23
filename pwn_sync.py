import os
import json
import time
import logging
import subprocess

import requests
import pwnagotchi.plugins as plugins

SYNC_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(SYNC_DIR, 'cfg', 'config.json')
UPLOADED_PATH = os.path.join(SYNC_DIR, 'cfg', 'pwn_uploaded.json')
TAR_PATH = os.path.join(SYNC_DIR, 'files', 'pwn_synced.tar')
HANDSHAKE_DIR = '/root/handshakes'
UPLOAD_RETRY_INTERVAL = 300


def load_config():
    with open(CFG_PATH, 'r') as f:
        config = json.load(f)
    port = config['port']
    port_suffix = '' if port == '443' else f':{port}'
    base_url = f"{config['protocol']}://{config['server_url']}{port_suffix}"
    return {
        'auth_token': config['auth_token'],
        'base_url': base_url,
    }


def load_uploaded():
    with open(UPLOADED_PATH, 'r') as f:
        return json.load(f)


def save_uploaded(uploaded):
    with open(UPLOADED_PATH, 'w') as f:
        json.dump(uploaded, f)


class PwnSync(plugins.Plugin):
    __author__ = 'alex@jndl.dev'
    __version__ = '1.1.0'
    __license__ = 'GPL3'
    __description__ = 'Synchronize handshakes to your local server'

    def __init__(self):
        self.ready = False

    def on_loaded(self):
        self.ready = True
        logging.info(f'PWN-SYNC v{self.__version__}: plugin loaded')

    def on_internet_available(self, agent):
        if not self.ready:
            return

        config = load_config()
        display = agent.view()
        uploaded = load_uploaded()

        new_files = self._find_new_handshakes(uploaded, display)
        if not new_files:
            display.set('status', 'No new handshakes!')
            display.update()
            logging.info(f'PWN-SYNC v{self.__version__}: No new handshakes!')
            return

        if not self._create_archive(new_files, display):
            return

        if self._upload_archive(config, display):
            uploaded.extend(new_files)
            save_uploaded(uploaded)
            display.set('status', 'Synchronized!')
            display.update()

    def _find_new_handshakes(self, uploaded, display):
        display.set('status', 'Checking for new handshakes')
        display.update()
        logging.info(f'PWN-SYNC v{self.__version__}: Checking for new handshakes')

        try:
            result = subprocess.run(
                ['sudo', 'ls', '-1', HANDSHAKE_DIR],
                capture_output=True, text=True, check=True,
            )
            handshakes = result.stdout.strip().splitlines()
        except subprocess.CalledProcessError as e:
            logging.error(f'PWN-SYNC v{self.__version__}: Failed to list handshakes: {e}')
            return []

        return [
            f for f in handshakes
            if (f.endswith('.pcap') or f.endswith('.geo.json')) and f not in uploaded
        ]

    def _create_archive(self, files, display):
        display.set('status', 'Creating tar archive')
        display.update()
        logging.info(f'PWN-SYNC v{self.__version__}: Creating tar archive')

        file_paths = [os.path.join(HANDSHAKE_DIR, f) for f in files]
        try:
            subprocess.run(
                ['sudo', 'tar', 'czf', TAR_PATH] + file_paths,
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            logging.info(f'PWN-SYNC v{self.__version__}: Created tar archive')
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f'PWN-SYNC v{self.__version__}: Tar failed: {e}')
            display.set('status', 'Tar archive creation failed!')
            display.update()
            return False

    def _upload_archive(self, config, display):
        url = f"{config['base_url']}/pwn-sync"
        token = config['auth_token']

        for attempt in range(3):
            logging.info(f'PWN-SYNC v{self.__version__}: Upload attempt {attempt + 1}')
            display.set('status', 'Sending tar archive')
            display.update()

            try:
                with open(TAR_PATH, 'rb') as tar:
                    auth = json.dumps({'pwn_auth_token': token})
                    resp = requests.post(url, files={'pwn_tar': tar, 'json': auth}, timeout=60)

                if resp.status_code == 200:
                    logging.info(f'PWN-SYNC v{self.__version__}: Upload successful')
                    end = json.dumps({'pwn_auth_token': token, 'status': 'ended_transmission'})
                    requests.post(url, files={'json': end}, timeout=30)
                    return True

                logging.error(f'PWN-SYNC v{self.__version__}: Upload failed (HTTP {resp.status_code})')

            except Exception as e:
                logging.error(f'PWN-SYNC v{self.__version__}: Upload error: {e}')

            display.set('status', 'Upload failed, retrying...')
            display.update()
            time.sleep(UPLOAD_RETRY_INTERVAL)

        return False
