import os
import requests
from datetime import datetime, timezone

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_over15_for_sport(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,uk,eu",
        "markets": "totals",
        "oddsFormat": "decimal",
    }
    try:
        resp = requests.get(url, params=params, timeout=20)
        print(f"{sport_key} status: {resp.status_code}")
        data = resp.json()
        if isinstance(data, dict):
            print("API Error:", data)
            return []
        if not isinstance(data, list):
            print("Unexpected API response:", type(data))
            return []
    except Exception as e:
        print(f"Error fetching {sport_key}: {e}")
        return []

    picks = []
    for game in data:
        if not isinstance(game, dict):
            continue
        bookmakers = game.get("bookmakers") or []
        if not bookmakers:
            continue
        home = game.get("home_team")
        away = game.get("away_team")
        commence = game.get("commence_time", "")
        try:
            dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
            time_str = dt.strftime("%H:%M")
        except:
            time_str = commence

        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") != "totals":
                    continue
                for outcome in market.get("outcomes", []):
                    price = outcome.get("price")
                    name = outcome.get("name")
                    point = outcome.get("point")
                    # Only Over 1.5, safe range
                    if name == "Over" and point == 1.5 and price and 1.15 <= price <= 1.40:
                        picks.append({
                            "match": f"{home} vs {away}",
                            "pick": "Over 1.5 Goals",
                            "odd": price,
                            "time": time_str
                        })
            break  # only first bookmaker
    return picks

def build_slip(picks, title, emoji):
    if not picks:
        return None
    # Pick 4 selections - total go be around 2.0 - 2.5
    selected = []
    total = 1.0
    for p in picks:
        if len(selected) >= 4:
            break
        if any(s["match"] == p["match"] for s in selected):
            continue
        selected.append(p)
        total *= p["odd"]

    if len(selected) < 3:
        return None

    lines = [f"{emoji} {title} - Over 1.5 Goals 🎯", ""]
    for p in selected:
        lines.append(f"⏰ {p['time']} | {p['match']}")
        lines.append(f"👉 {p['pick']} @ {p['odd']}")
        lines.append("")
    lines.append(f"💰 Total Odds: {round(total, 2)}")
    lines.append("🔥 Stake wisely | Good luck!")
    return "\n".join(lines)

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=20)
        print("Telegram status:", r.status_code, r.text[:200])
    except Exception as e:
        print("Telegram error:", e)

def main():
    print("Starting bot - Over 1.5 mode...")
    print("ODDS_API_KEY set:", bool(ODDS_API_KEY))

    # Try several leagues to get enough Over 1.5 games
    all_picks = []
    for league in ["soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_germany_bundesliga", "soccer_france_ligue_one", "soccer_netherlands_eredivisie", "soccer_portugal_primeira_liga", "soccer"]:
        picks = get_over15_for_sport(league)
        print(f"{league} picks: {len(picks)}")
        all_picks.extend(picks)

    foot_slip = build_slip(all_picks, "FOOTBALL OVER 1.5", "⚽")

    if foot_slip:
        print("Sending football slip")
        send_telegram(foot_slip)
    else:
        print("No football picks")
        send_telegram("⚽ No Over 1.5 picks today - no good value. Check back tomorrow.")

    print("Bot done.")

if __name__ == "__main__":
    main()
