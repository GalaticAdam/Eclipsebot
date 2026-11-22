# Eclipsebot
Discord bot for the Eclipse SMP

## Docker (recommended)

Runs the bot in a container that restarts automatically after crashes and on host reboot (as long as Docker itself starts on boot).

1. Copy config and fill in values:

   ```bash
   cp data/config/config-template.env data/config/config.env
   ```

2. Build and start in the background:

   ```bash
   docker compose up -d --build
   ```

3. Make sure Docker starts on boot (Arch Linux example):

   ```bash
   sudo systemctl enable --now docker
   ```

Useful commands:

```bash
docker compose logs -f        # follow logs
docker compose restart        # restart the bot
docker compose down           # stop and remove the container
```

`data/` is mounted into the container, so `config.env`, open tickets, and the role panel message ID persist across rebuilds.

## Config

Copy `data/config/config-template.env` to `data/config/config.env` and fill in values.

| Key | Description |
| --- | --- |
| `TOKEN` | Discord bot token |
| `Ticket_channel` | Channel ID where `/ticket` may be used |
| `transcript_channel` | Channel ID for closed-ticket transcripts |
| `whitelist_role` | Role ID that marks a user as whitelisted |
| `Role_channel` | Channel ID where the role-button panel is posted/updated on startup |
| `Role_buttons` | Comma-separated `role_id:Button Label` pairs for the panel |

### Role buttons

1. Set `Role_channel` to the channel that should show the role panel.
2. Set `Role_buttons`, for example:

   ```
   Role_buttons=123456789012345678:Announcements,987654321098765432:Events
   ```

3. Restart the bot. On startup it posts the panel (or edits the existing one using the message ID in `data/roles/panel.json`).
4. Members click a button to toggle that role on or off.

The bot needs **Manage Roles**, and its highest role must sit above every role listed in `Role_buttons`.
