# 🚂 Thai Railway Ticket Monitor Bot

A Python bot that monitors seat availability on Thai Railway (dticket.railway.co.th) and sends Telegram notifications when tickets become available.

## Features

- ✅ Monitors multiple trains/timings simultaneously
- ✅ Checks availability every 5 minutes
- ✅ Sends Telegram notifications when seats become available
- ✅ Tracks all seat types (coaches)
- ✅ Avoids duplicate notifications
- ✅ Startup/shutdown notifications

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Set the following environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-telegram-chat-id"
export CHECK_INTERVAL_MINUTES="5"  # optional, default is 5
```

Or create a `.env` file:
```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
CHECK_INTERVAL_MINUTES=5
```

### 3. Run the Bot

```bash
python train_monitor.py
```

## 🚀 Deployment to Railway.app

### Step 1: Prepare Your Code

1. Make sure all files are committed to Git:
   ```bash
   git add .
   git commit -m "Ready for Railway deployment"
   ```

2. Push to GitHub (if not already):
   ```bash
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

### Step 2: Deploy to Railway

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will auto-detect it's a Python project

### Step 3: Configure Environment Variables

In Railway dashboard, go to your service → **Variables** tab and add:

- `TELEGRAM_BOT_TOKEN` = `8068705451:AAGWWjaev2gb0thHYWhoXPzJpo7hT3Hv2EY`
- `TELEGRAM_CHAT_ID` = `252041404`
- `CHECK_INTERVAL_MINUTES` = `5` (optional, default is 5)

### Step 4: Deploy

Railway will automatically:
- Install dependencies from `requirements.txt`
- Run the bot using the `Procfile`
- Keep it running 24/7

### Step 5: Monitor

- View logs in Railway dashboard → **Deployments** → Click on deployment → **View Logs**
- The bot will send a startup notification to Telegram when it starts

### Notes

- The bot runs continuously on Railway
- No need for `nohup` or background processes - Railway handles it
- Railway auto-restarts the bot if it crashes
- Free tier includes 500 hours/month (enough for 24/7 operation)

## Important Notes

### Session Cookies

The cookies included in the configuration are from your browser session. These may expire and need to be updated periodically. To get new cookies:

1. Open https://dticket.railway.co.th in your browser
2. Log in to your account
3. Search for a train and go to seat selection
4. Open Developer Tools (F12) → Network tab
5. Find the `getTrainCoach` request
6. Copy the cookies from the request headers

### Adding More Trains

To add more trains to monitor, add entries to the `TRAINS` list:

```python
{
    "name": "My Train Description",
    "tripId": "123456",
    "provinceStartId": "297",
    "provinceEndId": "1679",
    "viewStateHolder": "...",
}
```

Get these values from the Network tab when selecting a train in the browser.

## Running in Background

### Using nohup (Linux/Mac)

```bash
nohup python train_monitor.py > monitor.log 2>&1 &
```

### Using screen

```bash
screen -S train-monitor
python train_monitor.py
# Press Ctrl+A, then D to detach
```

### Using tmux

```bash
tmux new -s train-monitor
python train_monitor.py
# Press Ctrl+B, then D to detach
```

## Troubleshooting

### "No seats available" but website shows seats

- Session cookies may have expired
- Update the `COOKIES` dictionary with fresh values from your browser

### No Telegram notifications

- Verify the bot token and chat ID are correct
- Make sure you've started a chat with your bot first
- Check if the bot can send messages to you

### Request timeouts

- The railway server may be slow or blocking requests
- Try increasing the timeout in the code
- Add longer delays between requests


