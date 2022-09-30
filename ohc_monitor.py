import requests, csv, json, time, os, logging, random

with open('./cfg/config.json', 'r') as cfg:
    cfg = json.load(cfg)
    webhook = cfg['webhook']
    email = cfg['email']
logging.basicConfig(level=logging.INFO)
dashboard_url = 'https://www.onlinehashcrack.com/dashboard'

s = requests.Session()
logging.info('Loading config successful, starting Onlinehashcrack monitor...')

while True:
    try:

        s.get(dashboard_url, timeout = 60)
        auth_post = s.post(dashboard_url, data = {'emailTasks': email, 'submit':''})
        csv_req = s.get('https://www.onlinehashcrack.com/wpa-exportcsv')
        if csv_req.status_code == 200:

            with open('./cfg/ohc.csv', 'wb') as csv_init:
                csv_init.write(csv_req.content)

            with open('./cfg/ohc.csv', 'rb') as fi:
                data = fi.read()

            with open('./cfg/ohc.csv', 'wb') as fo:
                fo.write(data.replace(b'\x00', b''))

            with open('./cfg/ohc.csv', 'r') as csvfile:
                csv_dash = csv.reader(csvfile)
                with open('./cfg/cracked.json', 'r') as cracked_json:
                    cracked = json.load(cracked_json)

                for row in csv_dash:
                    if len(row) > 1:
                        password = row[4]
                        essid = row[1]
                        bssid = row[2]

                        if password != '' and (password != 'password' and essid != "ESSID"):
                            found = False
                            for saved in cracked:
                                if essid in saved['ESSID']:
                                    found = True

                            if not found:
                                cracked.append({"ESSID": essid, "password": password})
                                embed = {'embeds': [{
                                    'title': "Password found!",
                                    'color': 16739436,
                                    'fields': [
                                        {
                                            'name': f'{essid}',
                                            'value': f'||{password}||'
                                        }],
                                    'footer': {
                                        "text": f'Captured @ {row[0]}'
                                    }}]}

                                bssid = bssid.replace(':', '')
                                essid = essid.replace('-', '').replace('_', '').replace(' ', '')

                                for geojson in os.listdir('./files'):
                                    if geojson.endswith('.geo.json'):
                                        if geojson == f'{essid}_{bssid}.geo.json':
                                            with open(f'./files/{geojson}', 'r') as geo_json:
                                                geo = json.load(geo_json)
                                                lat = geo['location']['lat']
                                                lng = geo['location']['lng']
                                                embed['embeds'][0]['description'] = f'[Google Maps](https://www.google.com/maps/place/{lat},{lng})'
                                
                                requests.post(webhook, json = embed)

                with open('./cfg/cracked.json', 'w') as update:
                    json.dump(cracked, update)
                    
        time.sleep(3600)

    except Exception as e:
        logging.error(f'Error occurred, callback: {e}, sleeping...')
        time.sleep(random.randint(600,1800))
        pass