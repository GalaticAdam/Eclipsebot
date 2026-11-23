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
