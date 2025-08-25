#!/usr/bin/env python3
"""Force sync Discord slash commands to ensure they appear"""
import asyncio
import os
import discord
from discord import app_commands
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('force_sync')

class CommandSyncBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.synced = False

    async def on_ready(self):
        if not self.synced:
            logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
            
            # Clear ALL commands first - both global and guild
            logger.info("Clearing ALL existing commands...")
            self.tree.clear_commands(guild=None)
            
            # Clear guild-specific commands if GUILD_ID is set
            guild_id = os.getenv('GUILD_ID')
            if guild_id:
                guild_obj = discord.Object(id=int(guild_id))
                self.tree.clear_commands(guild=guild_obj)
                logger.info(f"Cleared guild-specific commands for guild {guild_id}")
            
            # Register all commands from server_setup.py
            @self.tree.command(name="roles", description="Manage your self-assignable roles")
            async def roles(interaction: discord.Interaction):
                await interaction.response.send_message("Command registered", ephemeral=True)
            
            @self.tree.command(name="search", description="Search the web")
            @app_commands.describe(query="What to search for")
            async def search(interaction: discord.Interaction, query: str):
                await interaction.response.send_message(f"Searching: {query}", ephemeral=True)
            
            @self.tree.command(name="imagine", description="Generate an image with AI")
            @app_commands.describe(
                prompt="What to generate",
                negative="What to avoid in the image (optional)",
                quality="Quality preset: fast (4 steps), balanced (8 steps), quality (12 steps)",
                width="Image width in pixels (512-1024, default: 1024)",
                height="Image height in pixels (512-1024, default: 1024)",
                seed="Random seed for reproducibility (-1 for random)"
            )
            async def imagine(
                interaction: discord.Interaction, 
                prompt: str,
                negative: str = "",
                quality: str = "balanced",
                width: int = 1024,
                height: int = 1024,
                seed: int = -1
            ):
                await interaction.response.send_message(f"Generating: {prompt} (quality: {quality})", ephemeral=True)
            
            @self.tree.command(name="post_welcome", description="[Admin] Post or update welcome message")
            @app_commands.default_permissions(administrator=True)
            async def post_welcome(interaction: discord.Interaction):
                await interaction.response.send_message("Admin command", ephemeral=True)
            
            @self.tree.command(name="post_rules", description="[Admin] Post or update rules")
            @app_commands.default_permissions(administrator=True)
            async def post_rules(interaction: discord.Interaction):
                await interaction.response.send_message("Admin command", ephemeral=True)
            
            @self.tree.command(name="init_members", description="[Admin] Give Guest role to existing members")
            @app_commands.default_permissions(administrator=True)
            async def init_members(interaction: discord.Interaction):
                await interaction.response.send_message("Admin command", ephemeral=True)
            
            @self.tree.command(name="setup", description="[Admin] Setup the server structure")
            @app_commands.default_permissions(administrator=True)
            async def setup(interaction: discord.Interaction):
                await interaction.response.send_message("Admin command", ephemeral=True)
            
            # Log registered commands
            commands = self.tree.get_commands()
            logger.info(f"Registered {len(commands)} commands locally:")
            for cmd in commands:
                logger.info(f"  - /{cmd.name}: {cmd.description}")
            
            # Sync globally
            try:
                logger.info("Syncing commands globally...")
                synced = await self.tree.sync()
                logger.info(f"Successfully synced {len(synced)} commands globally:")
                for cmd in synced:
                    logger.info(f"  - /{cmd.name}")
            except Exception as e:
                logger.error(f"Failed to sync globally: {e}")
            
            # Also sync to specific guild if GUILD_ID is set
            guild_id = os.getenv('GUILD_ID')
            if guild_id:
                try:
                    guild = discord.Object(id=int(guild_id))
                    logger.info(f"Syncing commands to guild {guild_id}...")
                    synced = await self.tree.sync(guild=guild)
                    logger.info(f"Successfully synced {len(synced)} commands to guild:")
                    for cmd in synced:
                        logger.info(f"  - /{cmd.name}")
                except Exception as e:
                    logger.error(f"Failed to sync to guild: {e}")
            
            self.synced = True
            logger.info("Command sync complete! The bot will stay online for 10 seconds...")
            
            # Keep bot online for a bit to ensure sync completes
            await asyncio.sleep(10)
            logger.info("Shutting down...")
            await self.close()

async def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        logger.info("Please set DISCORD_TOKEN in your .env file")
        return
    
    bot = CommandSyncBot()
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())