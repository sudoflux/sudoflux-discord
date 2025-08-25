#!/usr/bin/env python3
import discord
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    # List all registered slash commands
    for guild in client.guilds:
        print(f"\nGuild: {guild.name}")
        commands = await guild.fetch_commands()
        if commands:
            print("Registered commands:")
            for cmd in commands:
                print(f"  - /{cmd.name}: {cmd.description}")
        else:
            print("  No commands registered")
    
    # Check global commands
    app_commands = await client.fetch_global_commands()
    print("\nGlobal commands:")
    for cmd in app_commands:
        print(f"  - /{cmd.name}: {cmd.description}")
    
    await client.close()

token = os.getenv('DISCORD_TOKEN')
if token:
    client.run(token)
else:
    print("DISCORD_TOKEN not found")