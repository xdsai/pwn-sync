import requests, os, json, subprocess, logging, time
import pwnagotchi.plugins as plugins

pwn_sync_dir = os.path.expanduser('/home/pi/pwn-sync')

with open(f'{pwn_sync_dir}/cfg/config.json', 'r') as cfg:
    cfg = json.load(cfg)
    webhook = cfg['webhook']
    auth_token = cfg['auth_token']
    server_url = cfg['server_url']
    port = cfg['port']
    if port == "443":
        port = ""
    else:
        port = ':' + port
    protocol = cfg['protocol']


class PwnSync(plugins.Plugin):
    __author__ = 'alex@jndl.dev'
    __version__ = '0.9.1'
    __license__ = 'GPL3'
    __description__ = 'Synchronize handshakes to your local server'


    def __init__(self):
        self.ready = False
    
    def on_loaded(self):
        self.ready = True
        logging.info(f"PWN-SYNC v{self.__version__}: plugin loaded")

    def on_internet_available(self, agent):
        if not self.ready:
            return

        with open(f'{pwn_sync_dir}/cfg/pwn_uploaded.json', 'r') as uploaded_json:
            uploaded_files = json.load(uploaded_json)
        display = agent.view()
        while True:
            try:
                display.set('status','Checking for new handshakes')
                display.update()
                logging.info(f"PWN-SYNC v{self.__version__}: Checking for new handshakes")
                handshakes = subprocess.check_output('sudo ls -1 /root/handshakes', shell=True).decode('utf-8').splitlines()
                files_to_tarball = ''
                files_to_be_uploaded = []

                for filename in handshakes:
                    if filename.endswith('.pcap') or filename.endswith('.geo.json'):
                        if filename not in uploaded_files:
                            files_to_tarball += f'/root/handshakes/{filename} '
                            files_to_be_uploaded.append(filename)
                
                if len(files_to_be_uploaded) > 0:
                    display.set('status','Creating tarball')
                    display.update()
                    logging.info(f"PWN-SYNC v{self.__version__}: Creating tarball")
                    process = subprocess.Popen(f'sudo tar czf {pwn_sync_dir}/files/pwn_synced.tar {files_to_tarball}', shell=True, stdin=None, stdout=open("/dev/null", "w"), stderr=None, executable="/bin/bash")
                    process.wait()
                    if process.returncode > 0:
                        raise Exception(f'{process.returncode}')
                    break
                else:
                    display.set('status','No new handshakes!')
                    display.update()
                    logging.info(f"PWN-SYNC v{self.__version__}: No new handshakes!")
                    time.sleep(360)
                
            except Exception as e:
                logging.error(f"PWN-SYNC v{self.__version__} Error while creating tarball: {e}")
                display.set('status', 'Tar archive creation failed!')
                display.update()
                time.sleep(360)
                pass

        logging.info(f'PWN-SYNC v{self.__version__} Successfully made the tar archive, sending to webhook')
        while True:
            display.set('status', 'Sending tar archive')
            display.update()            
            
            with open(f'{pwn_sync_dir}/files/pwn_synced.tar', 'rb') as tar:
                authentication = {"pwn_auth_token": auth_token}
                payload = {'pwn_tar': tar, 'json': (json.dumps(authentication))}
                main_req = requests.post(f'{protocol}://{server_url}/pwn-sync{port}', files = payload, timeout = 60)
            if main_req.status_code == 200:
                logging.info("PWN-SYNC: Successfully uploaded the tar archive")
                requests.post(f'{protocol}://{server_url}/pwn-sync{port}', files = {'json': (json.dumps({"pwn_auth_token": auth_token, "status": "ended_transmission"}))})
                display.set('status', 'Synchronized!')
                display.update()
                for filename in files_to_be_uploaded:
                    uploaded_files.append(filename)
                with open(f'{pwn_sync_dir}/cfg/pwn_uploaded.json', 'w') as update:
                    json.dump(uploaded_files, update)
                break
            else:
                logging.error(f"PWN-SYNC v{self.__version__} Upload error: {main_req.reason}")
                display.set('status', 'Tar archive upload failed!')
                display.update()
                time.sleep(120)

