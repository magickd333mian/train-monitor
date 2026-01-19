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

# Search name for notifications
SEARCH_NAME = "Ayutthaya >>> Chiang Mai ::: 07 of JAN, 2026"

# Trips to monitor - each trip has name, tripId, route info, and viewStateHolder
TRIPS_TO_MONITOR = [
    {
        "name": "Trip 1",
        "tripId": "517922",
        "provinceStartId": "74",
        "provinceEndId": "1679",
        "viewStateHolder": "w4SUgSWiev0jy3Xr6SU7czt9sCn_UIL5RMPBt9HmgUkor9E9u2fcf_urf0P2HwGTWxLu6_9vT6vMBB-ea4Uc9k4QcU18ZanCjDjhf-rrDw65pfRX22SiM-W216-z4EvLiHKVqm77x58BNtFqoqiYV_KZ4zPE-wiAhEg6MxbZiZhVjdo4032swLT0JeCFpWNhogUSTjuZBsL2fXqLOROPmXx76Lk2uus6sCi0gxC4YOJPijlUjtfoBC0bMOzNyh5HQXQh7qP3NpHjPF5gf4cHl8ZXzDhb-bLRiLxo-ctRbamcZpRncHiJ7SGxHHfZIKy8WuaJENBVdgWxCklySEoxf5HUq-nmlxErx5uxkw==",
    },
    {
        "name": "Trip 2",
        "tripId": "517904",
        "provinceStartId": "74",
        "provinceEndId": "1679",
        "viewStateHolder": "eQU5UiN8yjmtssSaFnJ8csu2Ei-sGJLGEPLk1N26PF3IZAD-qL5vRSKLu1MZ2dG2dkw0zxhEZUvgADLjYKZI11ouCx0F1glWYLVfK0cs4m0__ioRRnWz9_0fmZDhvO1Blvl2a2EZahrZ4_aMNHgzBrKWRrhHlQQ_BHsvXKXRP47k-QYsVphldkqF0SKWzF8L5J-bpkfsmgo2IBOo1ZsmrmJ7xH55KPMZAqS2lJw6QfMn70SRe3X2mFp8mzYFDpXubG2cCKp7xABNRT_h2MoOGhgrrKvxrWDUQ47T7yaGzdMWAYqqVz2fYrPRbkCOxOEBd-gR2ZiaCYOk69PFoSby2PDL1xrAuHeaxIPf5A==",
    },
    {
        "name": "Trip 3",
        "tripId": "517902",
        "provinceStartId": "74",
        "provinceEndId": "1679",
        "viewStateHolder": "hc1EWN1fUQy1qp5DPq2s5uV2w3HBm9lCmbLbQZCFDENLqRZFA1bnutGxZxUNpmVbG3v1F0OXC-syMrm2gEWEkYl0OVQiPPO4J0UYGsejUnt8A2B8Q94DzE-yw0lgwaY-Vu2_UgnSwKVvygbXLSdgv-N7IVDU_7yZm0Sk4irvxp4_DVT0kXqoH5qhfZgX35F0F32cq9c_PkI-0jtNnXTrIZfyj9Q3SdI3BDVxtHQrojnkBeURNf9E8qHKRxMCMR15cnnltwPyatNBxvLFHooOpGsDHqcFUXSWAPYwI9i1KN4gIuEE65Q-HPzmKTPRZO1clpZok_yC4sgroyG0Bu_l76JcKLhIoCxlqIxPiQ==",
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
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8,uk;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://dticket.railway.co.th",
    "Referer": f"{BASE_URL}/booking/booking",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8,uk;q=0.7",
        })
        
        # Visit home page to get session cookies
        resp = session.get(HOME_URL, allow_redirects=True, timeout=30)
        
        if resp.status_code == 200:
            # Set cookies from cURL command
            session.cookies.set("JSESSIONID", "node0fyuli80i184di6c00qfl0vgh14653051.node0")
            session.cookies.set("DTicketPublicSessionId", "w-G3202zJgsLmSuiYEACZJsbsewqelciK_DJOKs58mI")
            session.cookies.set("DTicketPublicUserName", "DTicketPublicWeb")
            session.cookies.set("accessType", "4")
            session.cookies.set("lang", "en")
            session.cookies.set("TS0190b5aa", "01071ea79e6a61529dbc3c21057473d323f8dd4409efb31ba68dcd8feea09d72fb74d5a5551def40966be43f3c7e3b374e1492b8d36eeb055b9ea43493aa13d1de92600506233963dc61a7acd15c8dc9739b6fecb17c8bbcf896a9d1bb3d8c666ea37b8df999cdcee07cfbb748800bb0bfd4cd3f60188d1d8c7d13fbf77858387a0aecd26d107f6443c109080236d82cd56de3e99ff04492b56aa586739d180133ba4317e3")
            session.cookies.set("dticket", "352456876.37151.0000")
            session.cookies.set("TS0185f5ba", "01071ea79e340aacb8a982aa6beff835b0350f1ec3efb31ba68dcd8feea09d72fb74d5a5551def40966be43f3c7e3b374e1492b8d357767d7f258a5f039c4ba4ae9f598c54")
            session.cookies.set("ccmp_uuid", "cf7dde85-eb57-494f-9835-5155ddb1c679")
            session.cookies.set("ccmp_strictly_setting", "true")
            session.cookies.set("ccmp_functional_setting", "true")
            session.cookies.set("ccmp_analytics_setting", "true")
            session.cookies.set("ccmp_advertising_setting", "true")
            session.cookies.set("TS7d2cd1d6027", "0883a5da20ab2000fdccdf4685ed2b514f814a79b539d6d159a675a04de543f94fed11a4c898bdae08165c74e9113000594a9b82240cc97fa294d777c28bacdf35d77ca2d87d8fac2b327edfadfa59bbce3c634aa1ceb69822e9660cac1f0122")
            
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
            "viewStateHolder": trip["viewStateHolder"],
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
    message += f"<b>{SEARCH_NAME}</b>\n"
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
        f"<b>{SEARCH_NAME}</b>\n\n"
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
