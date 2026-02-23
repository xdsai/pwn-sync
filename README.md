# pwn-sync

A synchronization toolset for [Pwnagotchi](https://pwnagotchi.ai) that syncs captured `.pcap` and `.geo.json` handshake files to your home server, with optional auto-upload to [OnlineHashCrack](https://www.onlinehashcrack.com/) and Discord notifications for cracked passwords.

## Components

| File | What it does |
|------|-------------|
| `pwn_sync.py` | Pwnagotchi plugin — detects new handshakes and uploads them to your server |
| `server.py` | Flask server — receives handshakes, extracts them, optionally uploads to OHC |
| `ohc_monitor.py` | Monitors OHC dashboard for cracked passwords, sends Discord webhook notifications |
| `configure.py` | Interactive setup wizard for both server and pwnagotchi sides |

## How it works

```
Pwnagotchi → (tar archive over HTTP) → Flask Server → (auto-upload) → OnlineHashCrack
                                                                            ↓
                                          Discord Webhook ← ohc_monitor.py checks for cracked passwords
```

1. The Pwnagotchi plugin runs on every internet connection event. It checks for new `.pcap` / `.geo.json` files, tarballs them, and POSTs them to your server.
2. The server receives and extracts the handshakes. If auto-upload is enabled, it pushes each `.pcap` to OnlineHashCrack's API.
3. The OHC monitor polls the dashboard periodically. When new passwords are cracked, it sends an embed to your Discord webhook — with a Google Maps link if geo data is available.

## Server setup

```bash
git clone https://github.com/xdsai/pwn-sync.git && cd pwn-sync
pip install -r requirements.txt
python3 configure.py
python3 server.py
```

The setup wizard will ask for:
- Whether to auto-upload to OHC (+ email if yes)
- Auth token (generate or enter existing)
- Server hostname/IP
- Discord webhook URL
- Protocol (HTTP/HTTPS) and port

### Running the OHC monitor

If auto-upload is enabled, run the monitor as a daemon to get Discord alerts for cracked passwords:

```bash
python3 ohc_monitor.py
```

## Pwnagotchi setup

Clone the repo on your Pwnagotchi and run the setup wizard:

```bash
git clone https://github.com/xdsai/pwn-sync.git && cd pwn-sync
pip install -r requirements.txt
python3 configure.py
```

Use the same auth token as your server. Then copy the plugin into your plugins directory:

```bash
cp pwn_sync.py /path/to/pwnagotchi/plugins/
```

Enable it in `config.toml`:

```toml
main.plugins.pwn_sync.enabled = true
```

The rest of the repo (`cfg/`, `files/`) should stay in the Pwnagotchi's home directory.

## Networking options

**Local only:** Use `http`, your server's local IP, and any unused port. The Pwnagotchi must be on the same network.

**Remote:** Use your public IP or domain, set up port forwarding, and use `https` with port `443`. The auth token provides basic protection against unauthorized uploads.

## License

GPL-3.0
