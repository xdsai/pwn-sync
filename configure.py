#!/usr/bin/env python3
"""Interactive setup wizard for pwn-sync configuration."""

import json
import os
import random
import secrets
import string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE_DIR, 'cfg', 'config.json')


def prompt_yn(question):
    while True:
        answer = input(f'{question} (y/n): ').strip().lower()
        if answer in ('y', 'n'):
            return answer == 'y'
        print('Invalid option, try again.')


def prompt_nonempty(question):
    while True:
        answer = input(f'{question}: ').strip()
        if answer:
            return answer
        print('Cannot be empty, try again.')


def generate_token(length=24):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    with open(CFG_PATH, 'r') as f:
        config = json.load(f)

    # auto-upload to OHC
    config['auto_upload'] = 'y' if prompt_yn('Automatically upload handshakes to OnlineHashCrack?') else 'n'

    if config['auto_upload'] == 'y':
        config['email'] = prompt_nonempty('Email address for OHC uploads')

    # auth token
    if prompt_yn('Generate a new auth token?'):
        token = generate_token()
        print(f'Your token: {token}')
        config['auth_token'] = token
    else:
        config['auth_token'] = prompt_nonempty('Enter your auth token')

    # server URL
    while True:
        url = prompt_nonempty('Server hostname (IP or domain, no http://)')
        if '://' in url:
            print('Enter just the hostname/IP without the protocol prefix.')
            continue
        config['server_url'] = url
        break

    # discord webhook
    config['webhook'] = prompt_nonempty('Discord webhook URL for notifications')

    # protocol & port
    if prompt_yn('Use HTTPS?'):
        config['port'] = '443'
        config['protocol'] = 'https'
    else:
        config['protocol'] = 'http'
        config['port'] = prompt_nonempty('Port for the Flask server')

    with open(CFG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

    print('\nConfiguration saved.')
    print('If setting up the Pwnagotchi side, make sure the auth token matches on both ends.')


if __name__ == '__main__':
    main()
