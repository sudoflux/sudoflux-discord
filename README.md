# sudoflux.io Casual Bot

Discord bot for the sudoflux.io community server.

## Features

- **Server Bootstrap**: Automatically creates/updates Discord server structure (roles, categories, channels)
- **Role Management**: `/roles` command for self-assignable roles (interests, platforms, regions)
- **Activity Logging**: Logs joins, leaves, and role changes to `#bot-logs`
- **Channel Permissions**: Enforces read-only channels and marketplace restrictions

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure bot token:
```bash
cp .env.example .env
# Edit .env and add your Discord bot token
```

3. Run the bot:
```bash
python server_setup.py
```

## Commands

- `/roles` - Self-assign interest, platform, and region roles
- `/setup` - (Admin only) Bootstrap/update server structure

## Server Structure

The bot manages the following Discord structure:

### Categories
- 00 START HERE (welcome, rules, announcements, roles)
- 10 LOUNGE (general chat channels)
- 20 TECH LAB (tech discussion)
- 30 RETRO & MODDING (retro gaming and hardware mods)
- 40 MECH KEYS (mechanical keyboards)
- 50 HOMELAB & SERVERS (homelab and infrastructure)
- 60 GAMING (LFG and gaming content)
- 70 MARKET (buy/sell/trade - restricted)
- 90 VOICE (voice channels)
- 99 STAFF (private staff channels)

### Self-Assignable Roles
- **Interests**: Tech, DevOps, Homelab, Retro, Modding, Keyboards, Gaming
- **Platforms**: PC, Switch, PlayStation, Xbox  
- **Regions**: NA, EU, APAC

## Deployment

This bot is designed to run on Kubernetes. Deployment manifests will be added in a future update.