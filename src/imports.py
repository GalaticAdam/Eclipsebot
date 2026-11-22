import json
import os
import subprocess
import re
import secrets
from pathlib import Path
from datetime import datetime, timezone
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord import Embed
from discord.ui import Button, View
from dotenv import load_dotenv
import asyncio
import mcrcon
import random

intents = discord.Intents.all()
intents.members = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='!!!', intents=intents)
stat_names = []



leave_message = """# 🚪 A VERY IMPORTANT ANNOUNCEMENT REGARDING {name}'S DEPARTURE

Dear members, moderators, administrators, friends, acquaintances, random individuals, and everyone unfortunate enough to be reading this message,

After an extraordinarily long period of consideration, reflection, internal debate, and approximately 47 minutes of staring at my screen, I have finally come to a decision.

**{mention} IS LEAVING.**

Yes. You read that correctly.

{name}, the person currently being discussed in this extremely important announcement, has decided to depart from this Discord server.

This decision was not made lightly. In fact, we spent so much time thinking about how to announce {name}'s departure that we nearly forgot that {name} was supposed to be leaving in the first place.

We would like to take this opportunity to reflect on everything that {name} has contributed during their time here.

The conversations, the arguments, the jokes that were funny for approximately three seconds, the random pings at completely unreasonable hours, and the countless messages that somehow managed to waste everyone's time.

{name} will be remembered.

Perhaps not by everyone.

Perhaps not for very long.

But remembered nonetheless.

To the moderators, thank you for maintaining order during {name}'s time here.

To the administrators, thank you for putting up with everything that happened.

And to {name}, we have just one thing to say.

WHY?

Why would you do this?

What happened?

Who hurt you?

Was it something we said?

Was it something someone else said?

Did you simply wake up one morning, open Discord, look at this server, and decide that you had finally had enough?

We may never know.

As {name} prepares to close this chapter of their Discord journey, we ask that everyone respect this decision.

Please do not organize a search party, contact international authorities, establish a dedicated investigation channel, or create a 47-page document attempting to determine {name}'s whereabouts.

{name} is not missing.

{name} is simply leaving.

There will undoubtedly be moments when we remember {name}. Perhaps we will see their username somewhere else, hear a familiar joke, or receive a notification and briefly experience the overwhelming urge to wonder where {name} went.

But those days will eventually pass.

We hope that {name} finds happiness, success, and everything they are looking for beyond the boundaries of this particular digital establishment.

May their future notifications be plentiful, their internet connection stable, their ping low, and their Discord experience significantly more productive than it was here.

And now, after all of these words, all of these paragraphs, all of these reflections, and all of this unnecessary emotional preparation, it is finally time.

{name} IS GOING.

{name} IS LEAVING.

{name} IS DEPARTING.

{name} IS EXITING.

{name} IS DISCONNECTING.

{name} IS REMOVING THEMSELVES FROM THIS ESTABLISHMENT.

This is the end of an era.

An era that may have lasted four days, four months, or four years.

An era nonetheless.

Thank you for everything, {name}.

Goodbye.

**Sincerely,**
The members who are still here.

*P.S. If {name} comes back tomorrow, no one saw anything.*
"""


