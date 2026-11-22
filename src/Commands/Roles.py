from src.imports import *
from src.globals import *

ROLE_PANEL_PATH = Path("data/roles/panel.json")
_role_view_registered = False


def _parse_role_buttons(raw: str | None) -> list[tuple[int, str]]:
    """Parse Role_buttons env: role_id:Label,role_id:Label"""
    if not raw or not raw.strip():
        return []

    roles = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            print(f"Skipping invalid Role_buttons entry (missing ':'): {entry}")
            continue

        role_id_str, label = entry.split(":", 1)
        role_id_str = role_id_str.strip()
        label = label.strip()
        if not role_id_str.isdigit() or not label:
            print(f"Skipping invalid Role_buttons entry: {entry}")
            continue

        roles.append((int(role_id_str), label[:80]))

    return roles


def _load_panel_message_id() -> int | None:
    if not ROLE_PANEL_PATH.exists():
        return None
    try:
        data = json.loads(ROLE_PANEL_PATH.read_text(encoding="utf-8"))
        message_id = data.get("message_id")
        return int(message_id) if message_id else None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Could not load role panel message id: {e}")
        return None


def _save_panel_message_id(message_id: int, channel_id: int) -> None:
    ROLE_PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = ROLE_PANEL_PATH.with_suffix(".json.tmp")
    payload = {
        "message_id": str(message_id),
        "channel_id": str(channel_id),
    }
    temp_path.write_text(json.dumps(payload, indent=4), encoding="utf-8")
    os.replace(temp_path, ROLE_PANEL_PATH)


def build_role_embed(roles: list[tuple[int, str]]) -> discord.Embed:
    lines = [f"**{label}** — <@&{role_id}>" for role_id, label in roles]
    description = (
        "Click a button below to toggle that role on or off.\n\n"
        + "\n".join(lines)
    )
    embed = discord.Embed(
        title="Role Selection",
        description=description,
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Version: {version}")
    return embed


class RoleToggleButton(Button):
    def __init__(self, role_id: int, label: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"role_toggle:{role_id}",
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return

        role = interaction.guild.get_role(self.role_id)
        if role is None:
            await interaction.response.send_message(
                "That role no longer exists. Please contact a staff member.",
                ephemeral=True,
            )
            return

        member = interaction.user
        try:
            if role in member.roles:
                await member.remove_roles(role, reason="Role panel toggle")
                await interaction.response.send_message(
                    f"Removed the **{role.name}** role.",
                    ephemeral=True,
                )
            else:
                await member.add_roles(role, reason="Role panel toggle")
                await interaction.response.send_message(
                    f"Added the **{role.name}** role.",
                    ephemeral=True,
                )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to manage that role.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Could not update your roles: {e}",
                ephemeral=True,
            )


class RolePanelView(View):
    def __init__(self, roles: list[tuple[int, str]]):
        super().__init__(timeout=None)
        for role_id, label in roles:
            self.add_item(RoleToggleButton(role_id, label))


def get_configured_roles() -> list[tuple[int, str]]:
    return _parse_role_buttons(os.getenv("Role_buttons"))


def get_role_channel_id() -> int | None:
    raw = os.getenv("Role_channel")
    if not raw or not str(raw).strip():
        return None
    try:
        return int(raw)
    except ValueError:
        print(f"Invalid Role_channel value: {raw}")
        return None


async def setup_role_panel():
    """Post or refresh the role button panel using config.env settings."""
    global _role_view_registered

    channel_id = get_role_channel_id()
    roles = get_configured_roles()

    if channel_id is None:
        print("Role panel skipped: Role_channel is not set")
        return

    if not roles:
        print("Role panel skipped: Role_buttons is empty or invalid")
        return

    if len(roles) > 25:
        print("Role panel skipped: Discord allows at most 25 buttons per message")
        return

    view = RolePanelView(roles)
    if not _role_view_registered:
        bot.add_view(view)
        _role_view_registered = True

    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.HTTPException as e:
            print(f"Role panel skipped: could not fetch channel {channel_id}: {e}")
            return

    embed = build_role_embed(roles)
    message_id = _load_panel_message_id()

    if message_id is not None:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed, view=view)
            print(f"Updated existing role panel message {message_id}")
            return
        except discord.NotFound:
            print("Stored role panel message was deleted; sending a new one")
        except discord.HTTPException as e:
            print(f"Could not edit role panel message: {e}; sending a new one")

    message = await channel.send(embed=embed, view=view)
    _save_panel_message_id(message.id, channel.id)
    print(f"Posted role panel message {message.id} in channel {channel.id}")


@bot.listen("on_ready")
async def on_ready_role_panel():
    await setup_role_panel()
