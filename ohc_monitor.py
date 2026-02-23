import os
import csv
import json
import time
import logging
import random

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE_DIR, 'cfg', 'config.json')
CRACKED_PATH = os.path.join(BASE_DIR, 'cfg', 'cracked.json')
GEO_DIR = os.path.join(BASE_DIR, 'files')
CSV_PATH = os.path.join(BASE_DIR, 'cfg', 'ohc.csv')

DASHBOARD_URL = 'https://www.onlinehashcrack.com/dashboard'
CSV_EXPORT_URL = 'https://www.onlinehashcrack.com/wpa-exportcsv'

POLL_INTERVAL = 3600  # 1 hour
ERROR_SLEEP_MIN = 600
ERROR_SLEEP_MAX = 1800

logging.basicConfig(level=logging.INFO)


def load_config():
    with open(CFG_PATH, 'r') as f:
        config = json.load(f)
    return config['webhook'], config['email']


def load_cracked():
    with open(CRACKED_PATH, 'r') as f:
        return json.load(f)


def save_cracked(cracked):
    with open(CRACKED_PATH, 'w') as f:
        json.dump(cracked, f)


def fetch_dashboard_csv(session, email):
    session.get(DASHBOARD_URL, timeout=60)
    session.post(DASHBOARD_URL, data={'emailTasks': email, 'submit': ''}, timeout=60)
    resp = session.get(CSV_EXPORT_URL, timeout=60)
    resp.raise_for_status()
    return resp.content


def parse_csv(raw_bytes):
    # strip null bytes (edge case: SSID contains null bytes)
    cleaned = raw_bytes.replace(b'\x00', b'')
    text = cleaned.decode('utf-8', errors='replace')
    reader = csv.reader(text.splitlines())

    results = []
    for row in reader:
        if len(row) < 5:
            continue
        captured, essid, bssid, _hash_type, password = row[0], row[1], row[2], row[3], row[4]
        if password and password != 'password' and essid != 'ESSID':
            results.append({
                'captured': captured,
                'essid': essid,
                'bssid': bssid,
                'password': password,
            })
    return results


def find_geo_json(essid, bssid):
    clean_bssid = bssid.replace(':', '')
    clean_essid = essid.replace('-', '').replace('_', '').replace(' ', '')
    expected = f'{clean_essid}_{clean_bssid}.geo.json'

    geo_path = os.path.join(GEO_DIR, expected)
    if not os.path.exists(geo_path):
        return None

    with open(geo_path, 'r') as f:
        geo = json.load(f)
    loc = geo.get('location', {})
    lat, lng = loc.get('lat'), loc.get('lng')
    if lat and lng:
        return f'https://www.google.com/maps/place/{lat},{lng}'
    return None


def notify_webhook(webhook, entry, maps_url=None):
    embed = {
        'title': 'Password found!',
        'color': 16739436,
        'fields': [{'name': entry['essid'], 'value': f"||{entry['password']}||"}],
        'footer': {'text': f"Captured @ {entry['captured']}"},
    }
    if maps_url:
        embed['description'] = f'[Google Maps]({maps_url})'

    requests.post(webhook, json={'embeds': [embed]}, timeout=10)


def check_for_cracked(webhook, email):
    session = requests.Session()
    raw_csv = fetch_dashboard_csv(session, email)
    entries = parse_csv(raw_csv)
    cracked = load_cracked()
    known_essids = {c['ESSID'] for c in cracked}

    new_count = 0
    for entry in entries:
        if entry['essid'] in known_essids:
            continue

        maps_url = find_geo_json(entry['essid'], entry['bssid'])
        notify_webhook(webhook, entry, maps_url)

        cracked.append({'ESSID': entry['essid'], 'password': entry['password']})
        known_essids.add(entry['essid'])
        new_count += 1

    if new_count > 0:
        save_cracked(cracked)
    logging.info(f'Check complete: {new_count} new passwords found')


def main():
    webhook, email = load_config()
    logging.info('OnlineHashCrack monitor started')

    while True:
        try:
            check_for_cracked(webhook, email)
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logging.error(f'Error: {e}')
            time.sleep(random.randint(ERROR_SLEEP_MIN, ERROR_SLEEP_MAX))


if __name__ == '__main__':
    main()
