# Eclipsebot
Discord bot for the Eclipse SMP

## Config

Copy `data/config/config-template.env` to `data/config/config.env` and fill in values.

| Key | Description |
| --- | --- |
| `TOKEN` | Discord bot token |
| `Ticket_channel` | Channel ID for the Create Ticket panel (and where tickets may be opened) |
| `transcript_channel` | Channel ID for closed-ticket transcripts |
| `whitelist_role` | Role ID that marks a user as whitelisted (assigned after a successful whitelist) |
| `Admin_roll` | Role ID allowed to run admin ticket commands (e.g. `/whitelist`). Required at startup — omitting it crashes import of `Ticket.py` |
| `RCON_HOST` | Minecraft RCON host (e.g. `localhost` on the game host) |
| `RCON_PORT` | Minecraft RCON port (e.g. `6009`) |
| `RCON_PASSWORD` | Minecraft RCON password (never commit the real value) |
| `Role_channel` | Channel ID where the role-button panel is posted/updated on startup |
| `Role_buttons` | Comma-separated `role_id:Button Label` pairs for the panel |

If you already have a `config.env` from an older checkout, add any new keys from `config-template.env` (especially `Admin_roll=`, `RCON_HOST=`, `RCON_PORT=`, `RCON_PASSWORD=`) before restarting.

### Whitelist tickets

1. Non-whitelisted members open a ticket and enter their Minecraft IGN.
2. The ticket message includes a **Whitelist Myself** button (ticket opener only).
3. Clicking it runs `whitelist add <IGN>` over RCON, stores Discord ↔ Minecraft in SQLite, and assigns `whitelist_role` when configured.
4. Staff can still use `/whitelist username:[IGN] member:[optional]` as a fallback.

Whitelist records live at `data/whitelist/whitelist.db` (created at runtime; bind-mounted with `./data` in Docker).

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
| `data/config/config.env` | Bot token, channel/role IDs, and RCON settings |
| `data/roles/panel.json` | Role panel message ID (survives recreates) |
| `data/ticket/panel.json` | Create Ticket panel message ID (survives recreates) |
| `data/ticket/opentickets.json` | Open ticket state |
| `data/whitelist/whitelist.db` | SQLite Discord ↔ Minecraft whitelist records |

### Build and run

```bash
# 1. Create config on the host (do not commit this file)
cp data/config/config-template.env data/config/config.env
# edit data/config/config.env — set TOKEN, Ticket_channel, transcript_channel,
# whitelist_role, Admin_roll, RCON_HOST, RCON_PORT, RCON_PASSWORD,
# Role_channel, Role_buttons as needed

# 2. Build and start in the background
docker compose up -d --build

# 3. Follow logs
docker compose logs -f

# Stop
docker compose down
```

`Admin_roll` must be set in the host `data/config/config.env` before the container starts; without it the bot exits while importing tickets. Updating the image does not rewrite that file — if your existing `config.env` is missing keys from the template, add them on the host (then restart or re-run `./scripts/update.sh`).

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
