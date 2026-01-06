#!/usr/bin/env python3
"""
Thai Railway Ticket Availability Monitor
Tracks seat availability and sends Telegram notifications when tickets become available.
"""

import requests
import time
import schedule
import os
from datetime import datetime, timedelta
from typing import Optional
import json

# ============ CONFIGURATION ============

# Load from environment variables (set these in your .env file or hosting platform)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL_MINUTES = int(os.environ.get("CHECK_INTERVAL_MINUTES", "5"))

# Trips to monitor - each trip has name, tripId, and route info
TRIPS_TO_MONITOR = [
    {
        "name": "23:38",
        "tripId": "513851",
        "provinceStartId": "23",
        "provinceEndId": "74",
    },
    {
        "name": "21:09",
        "tripId": "513833",
        "provinceStartId": "23",
        "provinceEndId": "74",
    },
    {
        "name": "19-45",
        "tripId": "513831",
        "provinceStartId": "23",
        "provinceEndId": "74",
    },
]

# ============ END CONFIGURATION ============

# URLs
BASE_URL = "https://dticket.railway.co.th/DTicketPublicWeb"
HOME_URL = f"{BASE_URL}/"
GET_COACH_URL = f"{BASE_URL}/booking/booking/getTrainCoach"

# Headers for AJAX requests
AJAX_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://dticket.railway.co.th",
    "Referer": f"{BASE_URL}/booking/booking",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

# Global state
session: Optional[requests.Session] = None
last_session_time: Optional[datetime] = None
previous_availability = {}


def log(message: str):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def send_telegram_notification(message: str) -> bool:
    """Send a notification via Telegram bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            log("✅ Telegram notification sent")
            return True
        else:
            log(f"❌ Telegram error: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Telegram failed: {e}")
        return False


def create_session() -> bool:
    """Create a new session by visiting the main page to get cookies."""
    global session, last_session_time
    
    log("🔄 Creating new session...")
    
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        
        # Visit home page to get session cookies
        resp = session.get(HOME_URL, allow_redirects=True, timeout=30)
        
        if resp.status_code == 200:
            # Set language preference
            session.cookies.set("lang", "en")
            last_session_time = datetime.now()
            log(f"✅ Session created (cookies: {len(session.cookies)})")
            return True
        else:
            log(f"❌ Failed to create session: HTTP {resp.status_code}")
            return False
            
    except Exception as e:
        log(f"❌ Session error: {e}")
        return False


def ensure_session() -> bool:
    """Ensure we have a valid session, refresh if needed."""
    global session, last_session_time
    
    # Refresh session every 20 minutes or if it doesn't exist
    if session is None or last_session_time is None:
        return create_session()
    
    if datetime.now() - last_session_time > timedelta(minutes=20):
        log("🔄 Session expired, refreshing...")
        return create_session()
    
    return True


def get_train_coaches(trip: dict) -> Optional[dict]:
    """Get coach/seat availability for a specific trip."""
    global session
    
    if not ensure_session():
        return None
    
    try:
        data = {
            "tripId": trip["tripId"],
            "provinceStartId": trip["provinceStartId"],
            "provinceEndId": trip["provinceEndId"],
        }
        
        resp = session.post(
            GET_COACH_URL,
            data=data,
            headers=AJAX_HEADERS,
            timeout=30
        )
        
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 500:
            log(f"   ⚠️ Server error, will refresh session")
            session = None  # Force session refresh
            return None
        else:
            log(f"   ❌ HTTP {resp.status_code}")
            return None
            
    except json.JSONDecodeError:
        log(f"   ❌ Invalid JSON response")
        return None
    except Exception as e:
        log(f"   ❌ Error: {e}")
        return None


def parse_availability(response_data: dict) -> list:
    """Parse the API response and extract seat availability info."""
    available_seats = []
    
    if not response_data:
        return available_seats
    
    if not response_data.get("result", False):
        return available_seats
    
    data = response_data.get("data", {})
    if not data:
        return available_seats
        
    coaches = data.get("results", [])
    
    for coach in coaches:
        seat_count = coach.get("availableSeatCount", 0)
        coach_no = coach.get("coachNo", "?")
        coach_class = coach.get("coachClassDescEn", "Unknown")
        seat_type = coach.get("coachSeatTypeEn", "Unknown")
        air_type = coach.get("coachAirTypeEn", "")
        
        # Skip Seating Coach - only track Sleeping Coach
        if seat_type == "Seating Coach":
            continue
        
        coach_desc = f"{coach_class} - {seat_type}"
        if air_type:
            coach_desc += f" ({air_type})"
        
        if seat_count > 0:
            available_seats.append({
                "coach_type": coach_desc,
                "coach_no": coach_no,
                "available_count": seat_count,
            })
    
    return available_seats


def format_availability_message(trip_name: str, available_seats: list) -> str:
    """Format notification message."""
    message = f"🚂 <b>TICKETS AVAILABLE!</b>\n\n"
    message += f"Train: <b>{trip_name}</b>\n\n"
    
    for seat in available_seats:
        message += f"🎫 {seat['coach_type']} (Coach #{seat['coach_no']})\n"
        message += f"   Available: <b>{seat['available_count']}</b> seats\n\n"
    
    return message


def check_all_trains():
    """Check availability for all configured trips."""
    global previous_availability
    
    log("=" * 50)
    log("Checking availability...")
    
    if not ensure_session():
        log("❌ No session, skipping check")
        return
    
    error_count = 0
    
    for trip in TRIPS_TO_MONITOR:
        trip_name = trip["name"]
        log(f"{trip_name}...")
        
        response = get_train_coaches(trip)
        
        if response is None:
            error_count += 1
            if error_count >= 3:
                log("🔄 Too many errors, refreshing session...")
                create_session()
                error_count = 0
            time.sleep(1)
            continue
        
        available_seats = parse_availability(response)
        total_available = sum(s["available_count"] for s in available_seats)
        
        prev_available = previous_availability.get(trip_name, 0)
        
        if total_available > 0:
            log(f"   🎉 {total_available} seats available!")
            
            if prev_available == 0:
                message = format_availability_message(trip_name, available_seats)
                send_telegram_notification(message)
            else:
                log(f"   (already notified)")
        else:
            log(f"   ❌ No seats")
            if prev_available > 0:
                log(f"   ⚠️ Seats gone (were: {prev_available})")
        
        previous_availability[trip_name] = total_available
        time.sleep(1)
    
    log("Done.")
    log("=" * 50)


def send_startup_message():
    """Send startup notification."""
    trip_list = "\n".join([f"  • {t['name']}" for t in TRIPS_TO_MONITOR])
    message = (
        f"🤖 <b>Train Monitor Started</b>\n\n"
        f"Monitoring {len(TRIPS_TO_MONITOR)} trips:\n{trip_list}\n\n"
        f"Check interval: {CHECK_INTERVAL_MINUTES} min\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    send_telegram_notification(message)


def main():
    """Main entry point."""
    # Validate required environment variables
    if not TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable is not set")
        print("   Set it with: export TELEGRAM_BOT_TOKEN='your-bot-token'")
        return
    if not TELEGRAM_CHAT_ID:
        print("❌ ERROR: TELEGRAM_CHAT_ID environment variable is not set")
        print("   Set it with: export TELEGRAM_CHAT_ID='your-chat-id'")
        return
    
    print("""
    ╔════════════════════════════════════════════════╗
    ║     🚂 Thai Railway Ticket Monitor Bot 🚂      ║
    ╠════════════════════════════════════════════════╣
    ║  Checking every 5 minutes with auto-refresh    ║
    ║  Press Ctrl+C to stop                          ║
    ╚════════════════════════════════════════════════╝
    """, flush=True)
    
    log(f"Monitoring {len(TRIPS_TO_MONITOR)} trips")
    log(f"Check interval: {CHECK_INTERVAL_MINUTES} minutes")
    
    # Initialize session
    create_session()
    
    # Send startup notification
    send_startup_message()
    
    # First check
    check_all_trains()
    
    # Schedule periodic checks
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_all_trains)
    
    log(f"Next check in {CHECK_INTERVAL_MINUTES} minutes...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log("Stopped by user.")
        send_telegram_notification("🛑 <b>Train Monitor Stopped</b>")


if __name__ == "__main__":
    main()
