

from src.imports import *
from src.globals import *
from src.whitelist_db import whitelist_db

import os
import io
import discord
from datetime import datetime, timezone

try:
    Admin_Role = int(os.getenv("Admin_roll"))
except (TypeError, ValueError):
    Admin_Role = 0

TICKET_PANEL_PATH = Path("data/ticket/panel.json")
_ticket_view_registered = False
_self_whitelist_view_registered = False


def get_rcon_config() -> tuple[str, int, str] | None:
    """Read RCON settings from env. Returns None if incomplete."""
    host = (os.getenv("RCON_HOST") or "").strip()
    port_raw = (os.getenv("RCON_PORT") or "").strip()
    password = (os.getenv("RCON_PASSWORD") or "").strip()
    if not host or not port_raw or not password:
        return None
    try:
        port = int(port_raw)
    except ValueError:
        print(f"Invalid RCON_PORT value: {port_raw}")
        return None
    return host, port, password


def rcon_cmd(command: str) -> str:
    config = get_rcon_config()
    if config is None:
        raise RuntimeError(
            "RCON is not configured. Set RCON_HOST, RCON_PORT, and RCON_PASSWORD "
            "in data/config/config.env"
        )
    host, port, password = config
    with mcrcon.MCRcon(host, password, port=port) as mcr:
        return mcr.command(command)


async def assign_whitelist_role(member: discord.Member) -> str | None:
    """Assign whitelist_role if configured. Returns an error string on failure."""
    if Whitelist_role is None:
        return None
    role = member.guild.get_role(Whitelist_role)
    if role is None:
        return "whitelist_role is set but that role was not found on this server."
    if role in member.roles:
        return None
    try:
        await member.add_roles(role, reason="Minecraft whitelist")
    except discord.Forbidden:
        return "I do not have permission to assign the whitelist role."
    except discord.HTTPException as e:
        return f"Could not assign whitelist role: {e}"
    return None


def _load_ticket_panel_message_id() -> int | None:
    if not TICKET_PANEL_PATH.exists():
        return None
    try:
        data = json.loads(TICKET_PANEL_PATH.read_text(encoding="utf-8"))
        message_id = data.get("message_id")
        return int(message_id) if message_id else None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Could not load ticket panel message id: {e}")
        return None


def _save_ticket_panel_message_id(message_id: int, channel_id: int) -> None:
    TICKET_PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = TICKET_PANEL_PATH.with_suffix(".json.tmp")
    payload = {
        "message_id": str(message_id),
        "channel_id": str(channel_id),
    }
    temp_path.write_text(json.dumps(payload, indent=4), encoding="utf-8")
    os.replace(temp_path, TICKET_PANEL_PATH)


def get_ticket_channel_id() -> int | None:
    """Channel for the Create Ticket panel (Ticket_channel in config.env)."""
    raw = os.getenv("Ticket_channel")
    if not raw or not str(raw).strip():
        return None
    try:
        return int(raw)
    except ValueError:
        print(f"Invalid Ticket_channel value: {raw}")
        return None


def build_ticket_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Support Tickets",
        description=(
            "Need help or want to join the whitelist?\n"
            "Click **Create Ticket** below to open a ticket."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Version: {version}")
    return embed


async def start_ticket_flow(interaction: discord.Interaction) -> None:
    """Shared ticket-creation UX used by the panel button and /ticket fallback."""
    channel_id = get_ticket_channel_id()
    if channel_id is not None and interaction.channel_id != channel_id:
        create_ticket_channel = bot.get_channel(channel_id)
        mention = (
            create_ticket_channel.mention
            if create_ticket_channel
            else f"<#{channel_id}>"
        )
        await interaction.response.send_message(
            f"You can only create a ticket in the designated channel: {mention}",
            ephemeral=True,
        )
        return

    is_whitelisted = discord.utils.get(interaction.user.roles, id=Whitelist_role)

    if is_whitelisted:
        modal = discord.ui.Modal(title="Ticket Form")
        IGN = discord.ui.TextInput(label="Your IGN", style=discord.TextStyle.short, max_length=16)
        Coords = discord.ui.TextInput(
            label="What are the coords",
            placeholder="If none put Nan",
            style=discord.TextStyle.short,
            max_length=256,
        )
        Issue = discord.ui.TextInput(
            label="Describe your issue",
            style=discord.TextStyle.paragraph,
            max_length=1024,
        )
        modal.add_item(IGN)
        modal.add_item(Coords)
        modal.add_item(Issue)

        async def IssueTicket(submit_interaction: discord.Interaction):
            IGN_ = IGN.value
            Coords_ = Coords.value
            Issue_ = Issue.value

            ticket = tickets.create_ticket(
                user_id=submit_interaction.user.id,
                username=submit_interaction.user.name,
                guild_id=submit_interaction.guild_id,
            )
            ticket_channel = await submit_interaction.guild.create_text_channel(
                ticket["id"],
                topic=f"Ticket by {ticket['username']}",
                category=submit_interaction.channel.category,
            )
            await ticket_channel.set_permissions(
                submit_interaction.guild.default_role,
                read_messages=False,
                send_messages=True,
            )
            await ticket_channel.set_permissions(
                submit_interaction.user, read_messages=True
            )
            await ticket_channel.send(
                f"**Someone will be with you shortly, please provide any releavent info you may want to share to us about this issue\n\n If this is a player rebort please post as much information you can regarding the concern**\n"
                + f"> In game name: {IGN_}\n"
                + f"> Ticket reason: {Issue_}\n"
                + f"> Ticket location: {Coords_}\n"
                f"-# Note: Tickets are manually reviewed and may take some time for someone to reach you, sorry for the hold"
            )
            tickets.update_ticket(ticket["id"], channel_id=ticket_channel.id)
            await submit_interaction.response.send_message(
                "Ticket has been created here " + ticket_channel.mention
            )

        modal.on_submit = IssueTicket
    else:
        modal = discord.ui.Modal(title="Whitelist Form")
        IGN = discord.ui.TextInput(label="Your IGN", style=discord.TextStyle.short, max_length=16)
        TAC = discord.ui.TextInput(
            label="TAC",
            placeholder="Do you agree to Follow all the rules of this server?",
            style=discord.TextStyle.short,
            max_length=4,
        )
        modal.add_item(IGN)
        modal.add_item(TAC)

        async def WhitelistTicket(submit_interaction: discord.Interaction):
            IGN_ = (IGN.value or "").strip()
            TAC_ = TAC.value
            ticket = tickets.create_ticket(
                user_id=submit_interaction.user.id,
                username=submit_interaction.user.name,
                guild_id=submit_interaction.guild_id,
            )
            ticket_channel = await submit_interaction.guild.create_text_channel(
                ticket["id"],
                topic=f"Ticket by {ticket['username']}",
                category=submit_interaction.channel.category,
            )
            await ticket_channel.set_permissions(
                submit_interaction.guild.default_role,
                read_messages=False,
                send_messages=True,
            )
            await ticket_channel.set_permissions(
                submit_interaction.user, read_messages=True
            )
            await ticket_channel.send(
                f"**Welcome to Eclips SMP**\n"
                + f"||<@&1261418176944541727>||"
                f"\n**BEFORE** joining please read the rules at <#1548427583018766469>\n\n"
                + f"> this is a whitelist server and your minecraft and discord account will be looked at to see if you fit this community\n\n"
                + f"> If you still want to join, click **Whitelist Myself** below (or ask staff if something goes wrong).\n\n"
                + f"> If you where told to could join this server please tell us there name and we will add them to the ticket\n\n"
                + f"Discrod Username: `{submit_interaction.user}`\nMinecraft Username: `{IGN_}`\nTAC: {TAC_}\n\n"
                + f"-# Note: Tickets are manually reviewed and may take some time for someone to reach you, sorry for the hold",
                view=SelfWhitelistView(),
            )

            tickets.update_ticket(
                ticket["id"],
                channel_id=ticket_channel.id,
                ticket_type="whitelist",
                minecraft_username=IGN_,
            )
            await submit_interaction.response.send_message(
                "Ticket has been created here " + ticket_channel.mention, ephemeral=True
            )

        modal.on_submit = WhitelistTicket

    await interaction.response.send_modal(modal)


class CreateTicketButton(Button):
    def __init__(self):
        super().__init__(
            label="Create Ticket",
            style=discord.ButtonStyle.primary,
            custom_id="ticket_panel:create",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        await start_ticket_flow(interaction)


class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreateTicketButton())


class SelfWhitelistButton(Button):
    def __init__(self):
        super().__init__(
            label="Whitelist Myself",
            style=discord.ButtonStyle.success,
            custom_id="ticket:self_whitelist",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return

        ticket = tickets.get_ticket(interaction.channel.name)
        if ticket is None:
            await interaction.response.send_message(
                "This button only works in an open whitelist ticket.",
                ephemeral=True,
            )
            return

        if str(interaction.user.id) != str(ticket["user_id"]):
            await interaction.response.send_message(
                "Only the ticket opener can use **Whitelist Myself**. "
                "Staff can use `/whitelist` if needed.",
                ephemeral=True,
            )
            return

        minecraft_username = (ticket.get("minecraft_username") or "").strip()
        if not minecraft_username:
            await interaction.response.send_message(
                "No Minecraft username is stored on this ticket. "
                "Ask staff to run `/whitelist` with your IGN.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            result = rcon_cmd(f"whitelist add {minecraft_username}")
        except Exception as e:
            await interaction.followup.send(
                f"Could not whitelist via RCON: {e}",
                ephemeral=True,
            )
            return

        discord_tag = str(interaction.user)
        whitelist_db.record(
            discord_user_id=interaction.user.id,
            discord_tag=discord_tag,
            minecraft_username=minecraft_username,
            source="self_whitelist",
            ticket_id=ticket["id"],
        )

        role_error = await assign_whitelist_role(interaction.user)
        role_note = f"\nRole: {role_error}" if role_error else ""

        # Disable the button on this message after a successful whitelist.
        try:
            disabled_view = View(timeout=None)
            disabled_button = Button(
                label="Whitelisted",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                custom_id="ticket:self_whitelist:done",
            )
            disabled_view.add_item(disabled_button)
            await interaction.message.edit(view=disabled_view)
        except (discord.HTTPException, AttributeError) as e:
            print(f"Could not disable self-whitelist button: {e}")

        await interaction.followup.send(
            f"You have been whitelisted as `{minecraft_username}`.\n"
            f"RCON: {result}{role_note}",
            ephemeral=True,
        )


class SelfWhitelistView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfWhitelistButton())


def register_persistent_ticket_views() -> None:
    """Register persistent ticket UI views once (survives bot restarts)."""
    global _ticket_view_registered, _self_whitelist_view_registered

    if not _ticket_view_registered:
        bot.add_view(TicketPanelView())
        _ticket_view_registered = True

    if not _self_whitelist_view_registered:
        bot.add_view(SelfWhitelistView())
        _self_whitelist_view_registered = True


async def setup_ticket_panel():
    """Post or refresh the Create Ticket panel using Ticket_channel."""
    register_persistent_ticket_views()

    channel_id = get_ticket_channel_id()
    if channel_id is None:
        print("Ticket panel skipped: Ticket_channel is not set")
        return

    view = TicketPanelView()

    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.HTTPException as e:
            print(f"Ticket panel skipped: could not fetch channel {channel_id}: {e}")
            return

    embed = build_ticket_embed()
    message_id = _load_ticket_panel_message_id()

    if message_id is not None:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed, view=view)
            print(f"Updated existing ticket panel message {message_id}")
            return
        except discord.NotFound:
            print("Stored ticket panel message was deleted; sending a new one")
        except discord.HTTPException as e:
            print(f"Could not edit ticket panel message: {e}; sending a new one")

    message = await channel.send(embed=embed, view=view)
    _save_ticket_panel_message_id(message.id, channel.id)
    print(f"Posted ticket panel message {message.id} in channel {channel.id}")


@bot.listen("on_ready")
async def on_ready_ticket_panel():
    await setup_ticket_panel()




async def send_ticket_transcript(interaction, tickets, bot):
    # Find the ticket associated with this channel
    ticket = tickets.get_ticket(interaction.channel.name)

    if ticket is None:
        print("Ticket not found for this channel.")
        return False

    # Get the transcript channel
    channel_id = int(os.getenv("transcript_channel"))
    transcript_channel = bot.get_channel(channel_id)

    if transcript_channel is None:
        transcript_channel = await bot.fetch_channel(channel_id)

    # Retrieve ALL messages, oldest first
    transcript = []
    message_count = 0

    async for message in interaction.channel.history(
        limit=None,
        oldest_first=True
    ):
        message_count += 1

        timestamp = message.created_at.strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        content = message.content or "[No text content]"

        transcript.append(
            f"[{timestamp}] "
            f"{message.author.name} ({message.author.id}):\n"
            f"{content}"
        )

        # Include attachment URLs
        for attachment in message.attachments:
            transcript.append(
                f"Attachment: {attachment.url}"
            )

        # Include embed contents
        for embed in message.embeds:
            if embed.title:
                transcript.append(f"Embed Title: {embed.title}")

            if embed.description:
                transcript.append(
                    f"Embed Description: {embed.description}"
                )

            for field in embed.fields:
                transcript.append(
                    f"{field.name}: {field.value}"
                )

        transcript.append("-" * 60)

    # Convert transcript into a TXT file
    transcript_text = "\n".join(transcript)

    file_data = io.BytesIO(
        transcript_text.encode("utf-8")
    )

    file_data.seek(0)

    transcript_file = discord.File(
        file_data,
        filename=f"{ticket['id']}.txt"
    )

    # Ticket timestamps
    opened_at = datetime.fromisoformat(ticket["opened_at"])
    closed_at = datetime.now(timezone.utc)

    # Create ticket information embed
    embed = discord.Embed(
        title="Ticket Closed",
        description=f"Transcript for ticket `{ticket['id']}`",
        color=discord.Color.red(),
        timestamp=closed_at
    )

    embed.add_field(
        name="Ticket ID",
        value=f"`{ticket['id']}`",
        inline=False
    )

    embed.add_field(
        name="Opened By",
        value=f"<@{ticket['user_id']}>",
        inline=True
    )

    embed.add_field(
        name="Closed By",
        value=interaction.user.mention,
        inline=True
    )

    embed.add_field(
        name="Opened At",
        value=discord.utils.format_dt(opened_at, "F"),
        inline=False
    )

    embed.add_field(
        name="Closed At",
        value=discord.utils.format_dt(closed_at, "F"),
        inline=False
    )

    embed.add_field(
        name="Total Messages",
        value=str(message_count),
        inline=True
    )

    embed.add_field(
        name="Ticket Channel",
        value=f"`{interaction.channel.name}`",
        inline=True
    )

    embed.set_footer(
        text=f"Ticket System • {ticket['id']}"
    )

    # Send the embed and TXT attachment together
    await transcript_channel.send(
        embed=embed,
        file=transcript_file
    )

    return True

@bot.tree.command(
    name="ticket",
    description="Creates a Ticket (fallback; prefer the Create Ticket button)",
)
@app_commands.allowed_installs(guilds=True, users=True)
async def createticket(interaction: discord.Interaction):
    await start_ticket_flow(interaction)



@bot.tree.command(name='add', description='Add a user to the ticket channel by their user ID')
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(user_id="The ID of the user to add to the ticket")
async def add(interaction: discord.Integration, user_id: discord.Member):
    ticket = tickets.get_ticket(interaction.channel.name)
    if ticket:
        if not user_id:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(user_id, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"User <@{user_id.id}> has been added to the ticket.", ephemeral=False)
    else:
        await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
    
@bot.tree.command(name='remove', description='Remove a user from the ticket channel by mention')
@app_commands.default_permissions(manage_channels=True)
@app_commands.describe(user_id="The ID of the user to add to the ticket")
async def remove(interaction: discord.Integration, user_id: discord.Member):
    ticket = tickets.get_ticket(interaction.channel.name)
    if ticket:
        if not user_id:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(user_id, read_messages=False, send_messages=False)
        await interaction.response.send_message(f"User <@{user_id.id}> has been removed from the ticket.", ephemeral=False)
    else:
        await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
    
    
    
@bot.tree.command(name="closeticket",description="Closes a Ticket")
@app_commands.default_permissions(manage_channels=True)
async def closeticket(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    success = await send_ticket_transcript(
        interaction,
        tickets,
        bot
    )

    if not success:
        await interaction.followup.send(
            "Could not find the ticket.",
            ephemeral=True
        )
        return

    # Find the ticket ID
    ticket = tickets.get_ticket(interaction.channel.name)

    # Remove ticket from the JSON file
    tickets.close_ticket(ticket["id"])
    await interaction.followup.send(
            "Ticket has been closed and the transcript has been sent.",
            ephemeral=True
        )
    await asyncio.sleep(10)  # Give some time for the followup message to be sent before deleting the channel
    # Delete the ticket channel
    await interaction.channel.delete()


@bot.tree.command(
    name="whitelist",
    description="Staff fallback: add a Minecraft username to the server whitelist via RCON",
)
@app_commands.default_permissions(manage_roles=True)
@app_commands.describe(
    username="Minecraft username to whitelist",
    member="Optional Discord member to link in the database / assign whitelist role",
)
async def whitelist(
    interaction: discord.Interaction,
    username: str,
    member: discord.Member | None = None,
):
    # Check if the user has the admin role before proceeding
    if not any(role.id == Admin_Role for role in interaction.user.roles):
        await interaction.response.send_message("You can't Use this command.", ephemeral=True)
        return

    username = (username or "").strip()
    if not username:
        await interaction.response.send_message(
            "Provide a Minecraft username.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        result = rcon_cmd(f"whitelist add {username}")
    except Exception as e:
        await interaction.followup.send(f"RCON Error: {e}")
        return

    ticket = tickets.get_ticket(interaction.channel.name)
    target = member
    if target is None and ticket is not None:
        target = interaction.guild.get_member(int(ticket["user_id"])) if interaction.guild else None

    notes = [f"RCON: {result}"]

    if target is not None:
        whitelist_db.record(
            discord_user_id=target.id,
            discord_tag=str(target),
            minecraft_username=username,
            source="staff_whitelist",
            ticket_id=ticket["id"] if ticket else None,
        )
        role_error = await assign_whitelist_role(target)
        notes.append(f"Linked Discord: {target} (`{target.id}`)")
        if role_error:
            notes.append(f"Role: {role_error}")
    else:
        notes.append(
            "No Discord member linked (pass `member`, or run inside their ticket)."
        )

    await interaction.followup.send("\n".join(notes))
