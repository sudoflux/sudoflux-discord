# Fix: /imagine Command Parameters Not Showing

If only the `prompt` parameter shows up for `/imagine`, Discord's command cache needs to be cleared.

## Quick Fix

1. **Run the resync script locally** (if you have Discord token):
```bash
python3 resync_imagine.py
```

2. **OR restart the bot pod** to trigger fresh sync:
```bash
kubectl -n discord-bots delete pod -l app=discord-casual
kubectl -n discord-bots logs -l app=discord-casual -f
```

3. **Wait 1-2 minutes** for Discord to update its cache

4. **In Discord:**
   - Type `/imagine` and wait a moment
   - You should see all parameters:
     - prompt (required)
     - negative (optional) 
     - quality (optional): fast, balanced, quality
     - width (optional): 512-1024
     - height (optional): 512-1024
     - seed (optional): -1 for random

## If Parameters Still Don't Show

1. **Force clear Discord's cache:**
   - Close Discord completely
   - Reopen Discord
   - Try `/imagine` again

2. **Manual sync** (requires bot token):
```bash
python3 force_sync_commands.py
```

3. **Check bot logs** for sync confirmation:
```bash
kubectl -n discord-bots logs -l app=discord-casual | grep -E "imagine|sync|command"
```

## Expected Parameters

After successful sync, `/imagine` should show:

- **prompt**: What to generate (required)
- **negative**: What to avoid in the image
- **quality**: fast (4 steps), balanced (8 steps), quality (12 steps)
- **width**: Image width in pixels (512-1024)
- **height**: Image height in pixels (512-1024)
- **seed**: Random seed (-1 for random)

## Why This Happens

Discord caches slash command definitions. When we add new parameters, Discord doesn't automatically update. We need to:
1. Clear the old command definition
2. Re-register with new parameters
3. Force Discord to sync the changes

The bot now does this automatically on startup, but sometimes Discord's cache persists.