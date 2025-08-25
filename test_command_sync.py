#!/usr/bin/env python3
"""Test script to verify command registration and sync"""
import asyncio
import os
import discord
from discord import app_commands
import logging

# Skip dotenv for test

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_sync')

async def test_sync():
    # Create a minimal bot to test command registration
    intents = discord.Intents.default()
    bot = discord.Client(intents=intents)
    tree = app_commands.CommandTree(bot)
    
    # Register test commands similar to the actual bot
    @tree.command(name="test_imagine", description="Test image generation command")
    @app_commands.describe(prompt="What to generate")
    async def test_imagine(interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(f"Test: {prompt}")
    
    @tree.command(name="test_search", description="Test search command")
    @app_commands.describe(query="What to search for")
    async def test_search(interaction: discord.Interaction, query: str):
        await interaction.response.send_message(f"Searching: {query}")
    
    # Check registered commands
    commands = tree.get_commands()
    logger.info(f"Commands registered locally: {len(commands)}")
    for cmd in commands:
        logger.info(f"  - /{cmd.name}: {cmd.description}")
        if hasattr(cmd, '_params'):
            for param_name, param in cmd._params.items():
                logger.info(f"      param: {param_name} ({param.type})")
    
    # Test if we can create the imagine command with the exact signature
    try:
        @tree.command(name="imagine", description="Generate an image with AI")
        @app_commands.describe(prompt="What to generate")
        async def imagine_command(interaction: discord.Interaction, prompt: str):
            pass
        logger.info("✓ /imagine command can be registered with simplified signature")
    except Exception as e:
        logger.error(f"✗ Failed to register /imagine: {e}")
    
    return tree

if __name__ == "__main__":
    tree = asyncio.run(test_sync())
    print(f"\nTotal commands that would be registered: {len(tree.get_commands())}")