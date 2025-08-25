#!/usr/bin/env python3
"""Test command registration without running the bot"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Monkey-patch to prevent actual bot connection
import discord
original_login = discord.Client.login
async def mock_login(self, token):
    print("Mock login - not connecting to Discord")
    return
discord.Client.login = mock_login

# Now import and run the bot setup
try:
    from server_setup import main
    
    async def test():
        # Import server_setup components
        from server_setup import SudofluxBot
        
        # Create bot instance
        bot = SudofluxBot()
        
        # This is where commands are defined - we need to simulate main()
        # Let's directly check what happens when we define commands
        
        # Define a test command the same way imagine is defined
        from discord import app_commands
        
        try:
            @bot.tree.command(name="test_imagine", description="Test image generation")
            @app_commands.describe(
                prompt="What to generate",
                negative="What to avoid", 
                width="Width",
                height="Height",
                seed="Seed"
            )
            async def test_imagine_command(
                interaction: discord.Interaction,
                prompt: str,
                negative: str = "",
                width: int = 1024,
                height: int = 1024,
                seed: int = -1
            ):
                pass
            print("✓ Test command with same signature as imagine registered successfully")
        except Exception as e:
            print(f"✗ Failed to register test command like imagine: {e}")
            import traceback
            traceback.print_exc()
        
        # Check registered commands
        commands = bot.tree.get_commands()
        print(f"\nCommands registered in tree: {len(commands)}")
        for cmd in commands:
            print(f"  - /{cmd.name}: {cmd.description}")
            
        # Check if image_gen initialized
        if hasattr(bot, 'image_gen'):
            if bot.image_gen:
                print("\n✓ image_gen initialized successfully")
            else:
                print("\n⚠ image_gen is None (initialization failed)")
        else:
            print("\n✗ image_gen attribute doesn't exist")
    
    asyncio.run(test())
    
except Exception as e:
    print(f"Error during test: {e}")
    import traceback
    traceback.print_exc()