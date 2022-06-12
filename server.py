import requests, json, time, os, tarfile, threading, subprocess
from flask import *

with open('./cfg/config.json', 'r') as cfg:
    cfg = json.load(cfg)
    email = cfg["email"]
    auth_token = cfg["auth_token"]
    auto_upload = cfg["auto_upload"]
    webhook = cfg["webhook"]
    cfg_port = cfg["port"]

app = Flask(__name__, static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 16*1000*1000 # max tar content size = 16MB


@app.route('/pwn-sync', methods=['POST'])
def get_content():

    if request.method == 'POST':
        if request.files:
            auth = json.loads(request.files['json'].read())
            if auth['pwn_auth_token'] == auth_token:

                if 'pwn_tar' in request.files:
                    pwned_tar = request.files['pwn_tar']
                    app.logger.warning('Received a tarball, saving...')
                    pwned_tar.save(f'./files/pwn_synced.tar')
                    process = subprocess.Popen(f'tar xf ./files/pwn_synced.tar --strip-components 1', shell=True, stdin=None, stdout=open("/dev/null", "w"), stderr=None, executable="/bin/bash")
                    process.wait()
                    if process.returncode > 0:
                        app.logger.warning(f'tar command failed, returned code: {process.returncode}')
                        abort(400)
                    app.logger.warning('Extracted the tarball archive')
                    return 'Success', 200
                if 'status' in auth:
                    if auth['status'] == "ended_transmission":
                        app.logger.warning('Transmission completed successfully')
                        if auto_upload == 'y':
                            threading.Thread(target = send_to_OHC).start()
                        return 'Success', 200     
            else:
                app.logger.warning('Invalid Auth token received')   
                abort(400)
        
def send_to_OHC():
    app.logger.warning('Starting auto-upload to Onlinehashcrack')
    files = os.listdir('./handshakes')
    upload_stats = {
        "already_uploaded":0,
        "no_handshake":0,
        "invalid_file":0,
        "success":0
    }

    with open('./cfg/server_uploaded.json', 'r') as uploaded_json:
        server_uploaded = json.load(uploaded_json)

    count = 0
    time_start = time.time()

    for pcap in files:
        if pcap.endswith(".pcap"):
            if pcap not in server_uploaded:
                with open(f'./handshakes/{pcap}', 'rb') as pcap_to_upload:
                    data = {'email': email}
                    payload = {'file': pcap_to_upload}
                    try:

                        ohc_post = requests.post('https://api.onlinehashcrack.com', data=data, files=payload, timeout=30)
                        if 'already sent' in ohc_post.text:

                            upload_stats['already_uploaded'] += 1
                        elif 'No valid EAPOL handshake or PMKID found' in ohc_post.text:
                            upload_stats['no_handshake'] += 1

                        elif 'File is not valid' in ohc_post.text:
                            upload_stats['invalid_file'] += 1
                        
                        else:
                            upload_stats['success'] += 1
                        
                        server_uploaded.append(pcap)
                        count += 1
                        time.sleep(0.5)

                    except:
                        pass

    with open('./cfg/server_uploaded.json', 'w') as update:
        json.dump(server_uploaded, update)
        
    time_end = round(time.time() - time_start)
    embed = {'embeds': [{
        'title': "Finished upload to OHC",
        'description': f'{count} .pcaps in {time_end} seconds',
        'color': 3388927,
        'fields': [
            {
            'name':'**Successful uploads**',
            'value': upload_stats['success'],
            'inline': True 
            },
            {
            'name':'**Already uploaded**',
            'value': upload_stats['already_uploaded'],
            'inline': True 
            },
            {
            'name':'**No handshake found**',
            'value': upload_stats['no_handshake'],
            'inline': True 
            },
            {
            'name':'**Invalid file**',
            'value': upload_stats['invalid_file'],
            'inline': True 
            },
            ]}]}
    requests.post(webhook, json = embed)
    app.logger.warning('Upload to OHC completed, posted embed to webhook...')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(cfg_port))