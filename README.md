# Eclipsebot
Discord bot for the Eclipse SMP

## Config

Copy `data/config/config-template.env` to `data/config/config.env` and fill in values.

| Key | Description |
| --- | --- |
| `TOKEN` | Discord bot token |
| `Ticket_channel` | Channel ID for the Create Ticket panel (and where tickets may be opened) |
| `transcript_channel` | Channel ID for closed-ticket transcripts |
| `whitelist_role` | Role ID that marks a user as whitelisted |
| `Role_channel` | Channel ID where the role-button panel is posted/updated on startup |
| `Role_buttons` | Comma-separated `role_id:Button Label` pairs for the panel |

### Ticket panel

1. Set `Ticket_channel` to the channel that should show the Create Ticket button (for example `1571754119494893628`).
2. Restart the bot. On startup it posts the panel (or edits the existing one using the message ID in `data/ticket/panel.json`).
3. Members click **Create Ticket** to open the same ticket form previously started with `/ticket`.
4. `/ticket` remains as an optional fallback in that channel.

Non-bot messages in `Ticket_channel` are auto-deleted so the panel stays clean.

### Role buttons

1. Set `Role_channel` to the channel that should show the role panel.
2. Set `Role_buttons`, for example:

   ```
   Role_buttons=123456789012345678:Announcements,987654321098765432:Events
   ```

3. Restart the bot. On startup it posts the panel (or edits the existing one using the message ID in `data/roles/panel.json`).
4. Members click a button to toggle that role on or off.

The bot needs **Manage Roles**, and its highest role must sit above every role listed in `Role_buttons`.

## Docker

Runs the bot in a container that restarts after crashes and host reboots (`restart: unless-stopped`). Secrets stay on the host — `config.env` is gitignored and excluded from the image.

### Persist layout

Compose mounts the host `./data` directory into the container at `/app/data`:

| Host path | Purpose |
| --- | --- |
| `data/config/config.env` | Bot token and channel/role IDs |
| `data/roles/panel.json` | Role panel message ID (survives recreates) |
| `data/ticket/opentickets.json` | Open ticket state |

### Build and run

```bash
# 1. Create config on the host (do not commit this file)
cp data/config/config-template.env data/config/config.env
# edit data/config/config.env with your TOKEN and IDs

# 2. Build and start in the background
docker compose up -d --build

# 3. Follow logs
docker compose logs -f

# Stop
docker compose down
```

After a host reboot, Docker starts the container again automatically (as long as the Docker daemon is set to start on boot). Recreating the container keeps state because `./data` is bind-mounted from the host.

### Update to latest `main`

Keeps the same `./data` mount, so `config.env`, `panel.json`, and ticket state survive the rebuild.

```bash
# From the repo root on the host
./scripts/update.sh
```

What it does: `git fetch` + fast-forward `main`, then `docker compose up -d --build`. Equivalent one-liner if you prefer not to use the script:

```bash
git checkout main && git pull --ff-only origin main && docker compose up -d --build
```

The script refuses to run if `data/config/config.env` is missing or the working tree has uncommitted changes.
