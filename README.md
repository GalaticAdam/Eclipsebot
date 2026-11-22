# Eclipsebot
Discord bot for the Eclipse SMP

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
