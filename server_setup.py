#!/usr/bin/env python3
import os
import asyncio
import yaml
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sudoflux-bot')

class SudofluxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='sudoflux.io casual bot'
        )
        
        self.structure = self.load_structure()
        self.assignable_roles = self.get_assignable_roles()
    
    def load_structure(self) -> Dict[str, Any]:
        """Load the server structure from YAML file"""
        with open('structure.yaml', 'r') as f:
            return yaml.safe_load(f)
    
    def get_assignable_roles(self) -> List[str]:
        """Get list of roles that users can self-assign"""
        assignable = []
        for category in ['interests', 'platforms', 'regions']:
            if category in self.structure['roles']:
                assignable.extend([role['name'] for role in self.structure['roles'][category]])
        if 'special' in self.structure['roles']:
            for role in self.structure['roles']['special']:
                if role['name'] == 'Guest':
                    assignable.append(role['name'])
        return assignable
    
    async def setup_hook(self):
        """Setup hook for bot initialization"""
        logger.info("Bot setup hook started")
        
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info(f'Connected to {len(self.guilds)} guild(s)')
        
        guild_id = os.getenv('GUILD_ID')
        if guild_id:
            guild = self.get_guild(int(guild_id))
            if guild:
                logger.info(f'Setting up specific guild: {guild.name} (ID: {guild.id})')
                await self.setup_guild(guild)
            else:
                logger.warning(f'Guild with ID {guild_id} not found')
        else:
            for guild in self.guilds:
                logger.info(f'Setting up guild: {guild.name} (ID: {guild.id})')
                await self.setup_guild(guild)
            
        await self.tree.sync()
        logger.info("Command tree synced")
    
    async def setup_guild(self, guild: discord.Guild):
        """Setup or update a guild with the defined structure"""
        logger.info(f"Starting guild setup for {guild.name}")
        
        await self.setup_roles(guild)
        await self.setup_categories_and_channels(guild)
        
        logger.info(f"Guild setup complete for {guild.name}")
    
    async def setup_roles(self, guild: discord.Guild):
        """Create or update roles"""
        existing_roles = {role.name: role for role in guild.roles}
        
        for category_name, roles in self.structure['roles'].items():
            for role_data in roles:
                role_name = role_data['name']
                
                if role_name in existing_roles:
                    logger.info(f"Role '{role_name}' already exists")
                    continue
                
                permissions = discord.Permissions.none()
                if 'permissions' in role_data:
                    if role_data['permissions'] == 'administrator':
                        permissions = discord.Permissions.administrator
                    else:
                        for perm in role_data['permissions'].split(','):
                            setattr(permissions, perm.strip(), True)
                
                try:
                    await guild.create_role(
                        name=role_name,
                        color=discord.Color(role_data.get('color', 0)),
                        hoist=role_data.get('hoist', False),
                        mentionable=role_data.get('mentionable', False),
                        permissions=permissions,
                        reason="Bot setup: Creating role"
                    )
                    logger.info(f"Created role: {role_name}")
                except Exception as e:
                    logger.error(f"Failed to create role {role_name}: {e}")
    
    async def setup_categories_and_channels(self, guild: discord.Guild):
        """Create or update categories and channels"""
        existing_categories = {cat.name: cat for cat in guild.categories}
        existing_channels = {ch.name: ch for ch in guild.channels}
        
        for category_data in self.structure['categories']:
            category_name = category_data['name']
            
            if category_name in existing_categories:
                category = existing_categories[category_name]
                logger.info(f"Category '{category_name}' already exists")
            else:
                overwrites = {}
                if category_data.get('private', False):
                    overwrites[guild.default_role] = discord.PermissionOverwrite(
                        read_messages=False
                    )
                    for role in guild.roles:
                        if role.name in ['Admin', 'Moderator', 'Staff', 'Bot']:
                            overwrites[role] = discord.PermissionOverwrite(
                                read_messages=True
                            )
                
                try:
                    category = await guild.create_category(
                        name=category_name,
                        position=category_data.get('position', 0),
                        overwrites=overwrites,
                        reason="Bot setup: Creating category"
                    )
                    logger.info(f"Created category: {category_name}")
                except Exception as e:
                    logger.error(f"Failed to create category {category_name}: {e}")
                    continue
            
            for channel_data in category_data.get('channels', []):
                channel_name = channel_data['name']
                channel_type = channel_data.get('type', 'text')
                
                full_channel_name = f"{category_name}-{channel_name}"
                if channel_name in [ch.name for ch in category.channels]:
                    logger.info(f"Channel '{channel_name}' already exists in {category_name}")
                    continue
                
                overwrites = {}
                
                if channel_data.get('read_only', False):
                    overwrites[guild.default_role] = discord.PermissionOverwrite(
                        send_messages=False,
                        add_reactions=False,
                        create_public_threads=False,
                        create_private_threads=False
                    )
                    
                    allowed_writers = channel_data.get('allowed_writers', [])
                    for role in guild.roles:
                        if role.name in allowed_writers or role.name == 'Admin':
                            overwrites[role] = discord.PermissionOverwrite(
                                send_messages=True,
                                add_reactions=True
                            )
                
                if channel_data.get('marketplace_only', False):
                    overwrites[guild.default_role] = discord.PermissionOverwrite(
                        send_messages=False
                    )
                    for role in guild.roles:
                        if role.name in ['Marketplace Verified', 'Admin', 'Moderator', 'Staff']:
                            overwrites[role] = discord.PermissionOverwrite(
                                send_messages=True
                            )
                
                try:
                    if channel_type == 'voice':
                        channel = await category.create_voice_channel(
                            name=channel_name,
                            position=channel_data.get('position', 0),
                            user_limit=channel_data.get('user_limit', 0),
                            overwrites=overwrites,
                            reason="Bot setup: Creating voice channel"
                        )
                        logger.info(f"Created voice channel: {channel_name}")
                    else:
                        channel = await category.create_text_channel(
                            name=channel_name,
                            position=channel_data.get('position', 0),
                            topic=channel_data.get('topic', ''),
                            slowmode_delay=channel_data.get('slowmode', 0),
                            overwrites=overwrites,
                            reason="Bot setup: Creating text channel"
                        )
                        logger.info(f"Created text channel: {channel_name}")
                except Exception as e:
                    logger.error(f"Failed to create channel {channel_name}: {e}")
    
    async def get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """Get the bot-logs channel"""
        for channel in guild.text_channels:
            if channel.name == 'bot-logs':
                return channel
        return None
    
    async def on_member_join(self, member: discord.Member):
        """Log member joins"""
        log_channel = await self.get_log_channel(member.guild)
        if log_channel:
            embed = discord.Embed(
                title="Member Joined",
                description=f"{member.mention} joined the server",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url if member.display_avatar else None)
            embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"))
            embed.set_footer(text=f"ID: {member.id}")
            await log_channel.send(embed=embed)
    
    async def on_member_remove(self, member: discord.Member):
        """Log member leaves"""
        log_channel = await self.get_log_channel(member.guild)
        if log_channel:
            embed = discord.Embed(
                title="Member Left",
                description=f"{member.mention} left the server",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url if member.display_avatar else None)
            embed.set_footer(text=f"ID: {member.id}")
            await log_channel.send(embed=embed)
    
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Log role changes"""
        if before.roles != after.roles:
            log_channel = await self.get_log_channel(after.guild)
            if not log_channel:
                return
            
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="Member Roles Updated",
                    description=f"{after.mention}'s roles changed",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                if added_roles:
                    embed.add_field(
                        name="Added Roles",
                        value=", ".join([role.mention for role in added_roles]),
                        inline=False
                    )
                
                if removed_roles:
                    embed.add_field(
                        name="Removed Roles",
                        value=", ".join([role.mention for role in removed_roles]),
                        inline=False
                    )
                
                embed.set_footer(text=f"ID: {after.id}")
                await log_channel.send(embed=embed)

class RoleSelect(discord.ui.Select):
    def __init__(self, roles: List[str], action: str, category: str = ""):
        self.action = action
        self.category = category
        options = [
            discord.SelectOption(label=role, value=role)
            for role in roles[:25]
        ]
        
        if category:
            placeholder = f"{action.capitalize()} {category} roles"
        else:
            placeholder = f"Select roles to {action}"
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=len(options),
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        
        if self.action == "add":
            roles_to_add = []
            for role_name in self.values:
                role = discord.utils.get(guild.roles, name=role_name)
                if role and role not in member.roles:
                    roles_to_add.append(role)
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Self-assigned via /roles")
                await interaction.response.send_message(
                    f"Added roles: {', '.join([r.name for r in roles_to_add])}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You already have all selected roles!",
                    ephemeral=True
                )
        
        elif self.action == "remove":
            roles_to_remove = []
            for role_name in self.values:
                role = discord.utils.get(guild.roles, name=role_name)
                if role and role in member.roles:
                    roles_to_remove.append(role)
            
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Self-removed via /roles")
                await interaction.response.send_message(
                    f"Removed roles: {', '.join([r.name for r in roles_to_remove])}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You don't have any of the selected roles!",
                    ephemeral=True
                )

class RoleView(discord.ui.View):
    def __init__(self, bot: SudofluxBot):
        super().__init__(timeout=180)
        self.bot = bot
        
        interests = [r for r in self.bot.assignable_roles if r in 
                    ['Tech', 'DevOps', 'Homelab', 'Retro', 'Modding', 'Keyboards', 'Gaming']]
        platforms = [r for r in self.bot.assignable_roles if r in 
                    ['PC', 'Switch', 'PlayStation', 'Xbox']]
        regions = [r for r in self.bot.assignable_roles if r in 
                    ['NA', 'EU', 'APAC']]
        
        if interests:
            self.add_item(RoleSelect(interests, "add", "Interest"))
            self.add_item(RoleSelect(interests, "remove", "Interest"))
        
        if platforms:
            self.add_item(RoleSelect(platforms, "add", "Platform"))
            self.add_item(RoleSelect(platforms, "remove", "Platform"))
        
        if regions:
            self.add_item(RoleSelect(regions, "add", "Region"))
            self.add_item(RoleSelect(regions, "remove", "Region"))
    
    @discord.ui.button(label="View My Roles", style=discord.ButtonStyle.primary, row=4)
    async def view_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        assignable_roles = [r for r in member.roles if r.name in self.bot.assignable_roles]
        
        if assignable_roles:
            role_list = "\n".join([f"• {r.mention}" for r in assignable_roles])
            embed = discord.Embed(
                title="Your Current Roles",
                description=role_list,
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="Your Current Roles",
                description="You don't have any self-assignable roles yet!",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def main():
    bot = SudofluxBot()
    
    @bot.tree.command(name="roles", description="Manage your self-assignable roles")
    async def roles_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Role Management",
            description="Use the dropdowns below to add or remove roles.\n\n**Available Categories:**\n• **Interests**: Tech, DevOps, Homelab, Retro, Modding, Keyboards, Gaming\n• **Platforms**: PC, Switch, PlayStation, Xbox\n• **Regions**: NA, EU, APAC",
            color=discord.Color.blue()
        )
        
        view = RoleView(bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @bot.tree.command(name="setup", description="[Admin] Setup the server structure")
    @app_commands.default_permissions(administrator=True)
    async def setup_command(interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You need administrator permissions to use this command!",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            await bot.setup_guild(interaction.guild)
            await interaction.followup.send(
                "✅ Server setup complete! All roles, categories, and channels have been created/updated.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error during setup: {str(e)}",
                ephemeral=True
            )
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        return
    
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())