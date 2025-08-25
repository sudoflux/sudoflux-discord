#!/usr/bin/env python3
"""Test if the imagine command can be registered in isolation"""

# This tests if there's something specific about the imagine command that fails

print("Testing imagine command registration in isolation...")

# First, let's check if all the decorators chain properly
test_code = '''
import discord
from discord import app_commands
from discord.ext import commands

# Create a minimal bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.tree.command(name="imagine", description="Generate an image with AI")
@app_commands.describe(
    prompt="What to generate",
    negative="What to avoid in the image",
    width="Image width in pixels",
    height="Image height in pixels", 
    seed="Random seed number"
)
async def imagine_command(
    interaction: discord.Interaction,
    prompt: str,
    negative: str = "",
    width: int = 1024,
    height: int = 1024,
    seed: int = -1
):
    pass

# Check if command registered
commands = bot.tree.get_commands()
print(f"Registered {len(commands)} commands")
for cmd in commands:
    print(f"  - {cmd.name}")
'''

# Try to execute this
try:
    exec(test_code)
    print("✓ Command registration code executes without error")
except Exception as e:
    print(f"✗ Error during registration: {e}")
    import traceback
    traceback.print_exc()

print("\nChecking for subtle issues...")

# Check if there's something about the multi-line function definition
print("\n1. Multi-line function definition:")
print("   The imagine_command spans multiple lines (line 773-779)")
print("   This is valid Python but might cause issues if there's")
print("   any hidden character or indentation problem")

print("\n2. Unique aspects of imagine command:")
print("   - Only command with multi-line function signature")
print("   - Has 5 parameters (most commands have 1)")
print("   - Uses default values for all params except 'prompt'")

print("\n3. Possible issue:")
print("   Between lines 772 and 773, after the closing ')' of @app_commands.describe")
print("   and before 'async def imagine_command(', there might be a hidden character")
print("   or the decorator chain might be broken")

print("\nRECOMMENDATION:")
print("Rewrite the imagine command with single-line signature to test:")