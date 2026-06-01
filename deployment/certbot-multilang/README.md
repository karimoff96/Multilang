MultiLang SSL automation

This folder contains templates and scripts to automate obtaining and renewing a TLS certificate for `multilang.uz` (including wildcard `*.multilang.uz`) without touching other project configs.

Approach
- Use a DNS-01 ACME plugin (recommended) so wildcard certificates can be issued and auto-renewed.
- You can use either `certbot` with a DNS plugin (e.g. `certbot-dns-cloudflare`) or `acme.sh` with the provider's DNS API.
- The included `renew_and_reload.sh` runs `certbot renew` and reloads `nginx` if a cert was renewed. A systemd timer and service are provided to run it daily.

Files
- `renew_and_reload.sh` – script that runs `certbot renew` and reloads `nginx` on successful renewal.
- `multilang-cert-renew.service` – systemd oneshot service to run the script.
- `multilang-cert-renew.timer` – systemd timer to run the service daily.
- `nginx_multilang.conf.template` – example nginx server block pointing to `/etc/letsencrypt/live/multilang.uz` certificate paths.

Quick install (example using Cloudflare DNS plugin)
1. Install certbot and DNS plugin (example for Debian/Ubuntu):

```bash
sudo apt update
sudo apt install certbot python3-certbot-dns-cloudflare
```

2. Create Cloudflare credentials file `/etc/letsencrypt/cloudflare.ini` with contents:

```
# Cloudflare API token with DNS edit permissions
dns_cloudflare_api_token = YOUR_TOKEN_HERE
```

Set permissions:

```bash
sudo chown root:root /etc/letsencrypt/cloudflare.ini
sudo chmod 600 /etc/letsencrypt/cloudflare.ini
```

3. Obtain certificate (one-time):

```bash
sudo certbot --non-interactive --agree-tos --email admin@multilang.uz \
  --dns-cloudflare --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d multilang.uz -d "*.multilang.uz"
```

4. Copy provided systemd unit/timer to `/etc/systemd/system/`, reload systemd and enable the timer:

```bash
sudo cp deployment/certbot-multilang/multilang-cert-renew.service /etc/systemd/system/
sudo cp deployment/certbot-multilang/multilang-cert-renew.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now multilang-cert-renew.timer
```

5. Test renewal script (dry run):

```bash
sudo /bin/bash /home/Wow-dash/deployment/certbot-multilang/renew_and_reload.sh
```

Notes & alternatives
- If you don't use Cloudflare, choose the appropriate `certbot` DNS plugin (e.g. `certbot-dns-route53`, `certbot-dns-ovh`), or use `acme.sh` which supports many DNS providers.
- A truly "never expiring" certificate is only possible with a self-signed certificate (not trusted by browsers). The recommended production approach is automated renewal (Let’s Encrypt) which keeps the certificate effectively permanent by renewing it automatically.
- The provided templates do not modify any existing project files — they live under `deployment/certbot-multilang/` so you can copy/install them on the server.

If you tell me which DNS provider you use (Cloudflare, AWS Route53, Godaddy, etc.), I can add an exact `certbot` command and credentials template for that provider.
