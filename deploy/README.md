# Deploying on Arch Linux (Omarchy)

The app runs as a plain Python process under a systemd **user** service, from a uv-managed virtualenv inside the
checkout. No Docker. These steps assume the machine is called `moniempc`, is on your Tailscale tailnet, and the repo
lives in `~/cookbook`.

Your recipe data (database, photos, PDFs) lives in `~/.local/share/cookbook`, outside the repo.

## 1. Install the tools

```sh
sudo pacman -S --needed git uv nodejs npm tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up          # skip if the machine is already on your tailnet
```

## 2. Get the code and install dependencies

```sh
git clone https://github.com/abdelmoniemh/cookbook.git ~/cookbook
cd ~/cookbook
uv sync --frozen
```

## 3. Build the web UI

```sh
cd ~/cookbook/web
npm ci
npm run build              # writes web/dist, which the server serves at /
cd ~/cookbook
```

Without `web/dist` the server still runs the API and shows a short message at `/`.

## 4. Import your cookbooks

Copy the PDFs over (from the machine that has them) and run the importer:

```sh
# on the machine with the PDFs
ssh moniempc 'mkdir -p ~/.local/share/cookbook/pdfs'
scp *.pdf moniempc:.local/share/cookbook/pdfs/

# on moniempc
cd ~/cookbook
uv run cookbook-import ~/.local/share/cookbook/pdfs/*.pdf --report ~/import-report.md
```

You can also upload a PDF later from the web UI (`POST /api/import`), which stores it in the same `pdfs/` folder.
Re-importing a book updates its recipes in place; recipes you edited in the app are kept.

## 5. Install and start the service

```sh
mkdir -p ~/.config/systemd/user
cp ~/cookbook/deploy/cookbook.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now cookbook
loginctl enable-linger $USER   # keep it running when you're logged out and start it at boot
```

Check it:

```sh
systemctl --user status cookbook
journalctl --user -u cookbook -f
curl http://127.0.0.1:8000/api/health
```

If you cloned somewhere other than `~/cookbook`, edit `WorkingDirectory` and `ExecStart` in
`~/.config/systemd/user/cookbook.service`, then `systemctl --user daemon-reload && systemctl --user restart cookbook`.

## 6. Open it over Tailscale

From any device on your tailnet (with MagicDNS on): **http://moniempc:8000**

The app has no login. It listens on all interfaces (`--host 0.0.0.0`), so anyone who can reach port 8000 can use it.
Keep it to the tailnet:

- If `ufw` is enabled (Omarchy turns it on), allow the port on the Tailscale interface only:
  `sudo ufw allow in on tailscale0 to any port 8000 proto tcp`
- To keep it off the LAN entirely, change `--host 0.0.0.0` to `--host 127.0.0.1` in the unit and use
  `tailscale serve` below.

### Optional: HTTPS on the tailnet

With HTTPS certificates enabled for your tailnet (admin console > DNS > HTTPS Certificates):

```sh
sudo tailscale serve --bg 8000
tailscale serve status       # shows https://moniempc.<your-tailnet>.ts.net
```

This proxies `https://moniempc.<tailnet>.ts.net` to the local server and persists across reboots.
Undo with `sudo tailscale serve --https=443 off`.

## Updating

```sh
~/cookbook/deploy/update.sh
```

It runs `git pull --ff-only`, `uv sync --frozen`, rebuilds the UI (`npm ci && npm run build`), restarts the service
and prints the health check.

## Backups

Everything worth keeping is in `~/.local/share/cookbook` (`cookbook.db`, `images/`, `pdfs/`). The database uses
WAL mode, so back it up with `sqlite3 cookbook.db ".backup backup.db"`, or stop the service before copying the files.
