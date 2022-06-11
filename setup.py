import json, random, string

with open('./cfg/config.json', 'r') as cfg:
    tmp = json.load(cfg)
    while True:
        autoupload = input('Do you want to automatically upload received handshakes to Onlinehashcrack? (y/n): ').lower()
        if len(autoupload) == 1 and (autoupload == 'y' or autoupload == 'n'):
            tmp['auto_upload'] = autoupload
            break
        else:
            print('Invalid option, try again.')

    if tmp['auto_upload'] == 'y':
        mail_input = input('Please enter your email address, this will be used to upload pcaps to OHC under your account: ')
        tmp['email'] = mail_input

    while True:
        auth_prompt = input('Do you want to generate a new token? (y/n): ').lower()
        if len(auth_prompt) == 1 and auth_prompt == 'y':
            token = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(12))
            print(f'Your token is: {token}')
            tmp['auth_token'] = token
            break
        elif len(auth_prompt) == 1 and auth_prompt == 'n':
            token = input('Please enter your token here: ')
            tmp['auth_token'] = token
            break
        else:
            print('Invalid response, try again')
    
    while True:
        server_url_input = input('Please enter the hostname where your server is hosted (IP/URL): ')
        if 'http' in server_url_input or 'https' in server_url_input:
            print('Try again without the http/https://')
        else:
            tmp['server_url'] = server_url_input
            break

    webhook_input = input('Please enter the discord webhook to send updates to: ')
    tmp['webhook'] = webhook_input

    while True:
        protocol_input = input('Do you want to change the default protocol? (http -> https) - (y/n): ').lower()
        if len(protocol_input) == 1:
            if protocol_input == 'y':
                tmp['port'] = 443
                tmp['protocol'] = 'https'
            else:
                port_input = input('Please the port you want to run the flask server on: ')
                tmp['port'] = port_input
            break

    with open('./cfg/config.json', 'w') as update:
        json.dump(tmp, update)
    
    print('Configuration successful. You may have to enter your token into your Pwnagotchi config as well')