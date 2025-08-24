# Kubernetes Deployment Instructions

## Prerequisites
- RKE2 cluster access
- kubectl configured
- Discord bot token
- Discord server (guild) ID

## Deployment Steps

### 1. Create the Secret

First, create the namespace and secret with your Discord credentials:

```bash
# Set the namespace
export KNS=discord-bots

# Create namespace if it doesn't exist
kubectl get ns $KNS >/dev/null 2>&1 || kubectl create ns $KNS

# Input your Discord credentials
read -s -p "DISCORD_TOKEN: " DISCORD_TOKEN; echo
read -p "GUILD_ID (server id): " GUILD_ID

# Delete existing secret if present
kubectl -n $KNS delete secret discord-casual-secrets >/dev/null 2>&1 || true

# Create the secret
kubectl -n $KNS create secret generic discord-casual-secrets \
  --from-literal=DISCORD_TOKEN="$DISCORD_TOKEN" \
  --from-literal=GUILD_ID="$GUILD_ID"
```

### 2. Deploy the Bot

Apply the Kubernetes manifests:

```bash
# Using kubectl
kubectl apply -k k8s/

# Or apply individual files
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
```

### 3. Verify Deployment

Check that the bot is running:

```bash
# Check pod status
kubectl -n discord-bots get pods

# View logs
kubectl -n discord-bots logs -l app=discord-casual

# Describe deployment
kubectl -n discord-bots describe deployment discord-casual
```

## Updating the Bot

To update to a new version:

1. Tag a new release in Git:
```bash
git tag -a v0.2.0 -m "discord-casual 0.2.0"
git push origin v0.2.0
```

2. Update the image tag in `k8s/deployment.yaml`
3. Apply the updated deployment:
```bash
kubectl apply -k k8s/
```

## Troubleshooting

### Bot not connecting
- Verify the secret is created: `kubectl -n discord-bots get secret discord-casual-secrets`
- Check logs: `kubectl -n discord-bots logs -l app=discord-casual`
- Ensure the bot token is valid and the bot is invited to the server

### Permission errors
- Ensure the bot has appropriate permissions in Discord
- Check the Bot role is positioned correctly in the Discord role hierarchy

## Rollback

To rollback to a previous version:

```bash
kubectl -n discord-bots rollout undo deployment discord-casual
```

## Cleanup

To remove the bot from your cluster:

```bash
kubectl delete -k k8s/
kubectl -n discord-bots delete secret discord-casual-secrets
```