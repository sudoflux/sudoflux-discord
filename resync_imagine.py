#!/usr/bin/env python3
"""Force re-sync the /imagine command with all parameters"""
import asyncio
import os
import discord
from discord import app_commands
from dotenv import load_dotenv
import logging
import sys

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('resync')

class ResyncBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user}')
        
        try:
            # First, sync with NO commands to clear Discord's cache
            logger.info("Step 1: Clearing all commands from Discord...")
            self.tree.clear_commands(guild=None)
            
            # Sync the empty tree to Discord
            await self.tree.sync()
            logger.info("Cleared global commands")
            
            # Also clear guild commands if specified
            guild_id = os.getenv('GUILD_ID')
            if guild_id:
                guild = discord.Object(id=int(guild_id))
                self.tree.clear_commands(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Cleared guild {guild_id} commands")
            
            # Wait for Discord to process
            logger.info("Waiting 5 seconds for Discord to process...")
            await asyncio.sleep(5)
            
            # Now register the updated imagine command
            logger.info("Step 2: Registering updated /imagine command...")
            
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
                await interaction.response.send_message("Test", ephemeral=True)
            
            # Log the command parameters
            logger.info("Registered /imagine with parameters:")
            for cmd in self.tree.get_commands():
                if cmd.name == "imagine":
                    logger.info(f"  Found /imagine command")
                    if hasattr(cmd, '_params'):
                        for param_name in cmd._params:
                            logger.info(f"    - {param_name}")
            
            # Sync the new command
            logger.info("Step 3: Syncing updated command to Discord...")
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands globally")
            
            if guild_id:
                guild = discord.Object(id=int(guild_id))
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} commands to guild {guild_id}")
            
            logger.info("✅ SUCCESS! The /imagine command has been re-synced with all parameters:")
            logger.info("  - prompt (required)")
            logger.info("  - negative (optional)")
            logger.info("  - quality (optional, default: balanced)")
            logger.info("  - width (optional, default: 1024)")
            logger.info("  - height (optional, default: 1024)")
            logger.info("  - seed (optional, default: -1)")
            logger.info("")
            logger.info("Discord may take 1-2 minutes to update. Try:")
            logger.info("1. Type /imagine and wait a moment")
            logger.info("2. Restart Discord client if needed")
            logger.info("3. The parameters should appear after 'prompt:'")
            
        except Exception as e:
            logger.error(f"Error during resync: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(5)
        await self.close()

async def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found!")
        logger.info("Set DISCORD_TOKEN in .env file")
        sys.exit(1)
    
    bot = ResyncBot()
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Failed: {e}")

if __name__ == "__main__":
    logger.info("Starting command resync...")
    logger.info("This will clear and re-register the /imagine command")
    asyncio.run(main())