import os
import requests
from datetime import datetime, timezone

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_odds_for_sport(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
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
                for outcome in market.get("outcomes", []):
                    price = outcome.get("price")
                    name = outcome.get("name")
                    # Only safe favourites: 1.30 - 1.55
                    if price and 1.30 <= price <= 1.55:
                        picks.append({
                            "match": f"{home} vs {away}",
                            "pick": name,
                            "odd": price,
                            "time": time_str
                        })
            break  # only first bookmaker
    return picks

def build_slip(picks, title, emoji):
    if not picks:
        return None
    # Pick 5 selections that multiply to ~5.00
    selected = []
    total = 1.0
    for p in picks:
        if len(selected) >= 5:
            break
        # Avoid duplicate matches
        if any(s["match"] == p["match"] for s in selected):
            continue
        selected.append(p)
        total *= p["odd"]

    if len(selected) < 3:
        return None

    lines = [f"{emoji} {title} - {len(selected)} ODDS 🎯", ""]
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
    print("Starting bot...")
    print("ODDS_API_KEY set:", bool(ODDS_API_KEY))
    print("TELEGRAM_BOT_TOKEN set:", bool(TELEGRAM_BOT_TOKEN))
    print("TELEGRAM_CHAT_ID set:", bool(TELEGRAM_CHAT_ID))

    football = get_odds_for_sport("soccer")
    print(f"Football picks: {len(football)}")

    basketball = get_odds_for_sport("basketball_nba")
    print(f"Basketball picks: {len(basketball)}")

    foot_slip = build_slip(football, "FOOTBALL", "⚽")
    basket_slip = build_slip(basketball, "BASKETBALL", "🏀")

    if foot_slip:
        print("Sending football slip")
        send_telegram(foot_slip)
    else:
        print("No football picks")

    if basket_slip:
        print("Sending basketball slip")
        send_telegram(basket_slip)
    else:
        print("No basketball picks")

    print("Bot done.")

if __name__ == "__main__":
    main()
