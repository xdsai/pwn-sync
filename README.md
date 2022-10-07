# Pwnagotchi Sync

A synchronization tool that allows you to synchronize your .pcap and .geo.json files from your [Pwnagotchi](https://pwnagotchi.ai) to your home server with the option of automatically uploading them to [Onlinehashcrack](https://www.onlinehashcrack.com/). It utilizes a flask server for receiving and processing files on your home server/network, and the pwnagotchi sends any new captured files to the server as soon as it detects internet connectivity. The server can then upload the handshakes via OHC's API and the monitoring script then sends any newly cracked networks to a discord webhook along with a Google maps link with the coordinates of the network, if any are found.

## Server Install

Clone the repository and cd into it ->

```
git clone https://github.com/xdsai/pwn-sync.git && cd pwn-sync
```

Install the required dependencies with pip ->

```
pip install -r requirements.txt
```

And run the setup.py script ->

```
python3 setup.py
```

### Server Notes

The setup will prompt you to enter needed information for the scripts to work. You are first asked whether you want the scripts to automatically upload all handshakes to OHC, if yes you have to enter an email address. This will be used to upload the handshakes to the API under your account, where you can later retrieve them from their dashboard.

You have 2 options of running the flask server. First one is you can run it locally, and your Pwnagotchi will only be able to sync to the server when it's connected to the same network as the server. In this case, choose http as the desired protocol and in the server_url field, enter the local IP address of the machine the server is running on. Port doesn't matter much, but be sure to choose an unused one, preferably above 1000.

If you decide to make the flask server available to the outside world, allowing uploads from anywhere, you have to use your [public IP](https://jndl.dev/ip) in the server_url field and make sure you have port forwarding set up for the server. You are encouraged to use HTTPS in this case.

### Pwnagotchi Install

Clone the repository on your pwnagotchi as well, and install the requirements. Then run setup.py.

When prompted for a token, input the one you have received from your server side, this will make authentication on both sides work. If this token is invalid, nothing will work. This is a small form of protection, so that not just anyone can send you requests. Email isn't neccessary in this case, but make sure to enter the right port, server_url/IP of the machine that runs the server and protocol.

Then, move the pwn_sync.py to your installed plugins directory, leave the rest in your home directory, anywhere else it won't work as the paths were hardcoded, and enable the plugin in config.yaml by adding the line below, or enable the switch in webcfg.

```
main.plugins.pwn_sync.enable = true
```

### OHC Monitor Notes

The ohc_monitor.py script is made to detect any newly cracked networks from Onlinehashcrack. It downloads all your networks in csv form and checks against a saved list of previously cracked networks. Any changes are sent to the discord webhook, with a Google Maps link with the coordinates of the network, if any are found. Recommended to run 24/7 as a daemon, if your automatic uploading to OHC is disabled, there's no point to running this.
