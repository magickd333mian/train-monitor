# 🚀 Railway Deployment Guide

## Quick Deployment Steps

### 1. Push to GitHub
```bash
git init  # if not already a git repo
git add .
git commit -m "Deploy to Railway"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Deploy on Railway

1. Visit [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway auto-detects Python and installs dependencies

### 3. Set Environment Variables

In Railway dashboard → Your Service → **Variables**:

| Variable | Value |
|----------|-------|
| `TELEGRAM_BOT_TOKEN` | `8068705451:AAGWWjaev2gb0thHYWhoXPzJpo7hT3Hv2EY` |
| `TELEGRAM_CHAT_ID` | `252041404` |
| `CHECK_INTERVAL_MINUTES` | `5` (optional) |

### 4. Verify Deployment

- Check Railway logs: Dashboard → Deployments → View Logs
- You should see: "✅ Session created" and "✅ Telegram notification sent"
- Check Telegram for startup notification

## Files Included

- ✅ `Procfile` - Tells Railway how to run the bot
- ✅ `requirements.txt` - Python dependencies
- ✅ `railway.json` - Railway configuration
- ✅ `runtime.txt` - Python version

## Monitoring

- **Logs**: Railway Dashboard → Deployments → View Logs
- **Status**: Railway Dashboard → Service status
- **Telegram**: You'll receive notifications when seats are available

## Troubleshooting

### Bot not starting
- Check Railway logs for errors
- Verify environment variables are set correctly
- Check that `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct

### No Telegram notifications
- Verify bot token and chat ID in Railway variables
- Check Railway logs for "Telegram notification sent" messages
- Make sure you've started a chat with your bot

### Bot keeps restarting
- Check Railway logs for error messages
- Verify the Thai Railway API is accessible
- Check if session creation is failing

## Cost

Railway free tier includes:
- 500 hours/month (enough for 24/7 operation)
- $5 credit monthly
- Perfect for this bot!
