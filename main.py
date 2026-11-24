import os
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_best_5(picks):
    picks = sorted(picks, key=lambda x: x['odds'], reverse=True)
    return picks[:5]

def get_odds_for_sport(sport_key, league_name):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h,totals",
        "oddsFormat": "decimal"
    }
    try:
        resp = requests.get(url, params=params, timeout=20)
        data = resp.json()
    except Exception as e:
        print(f"Error {league_name}: {e}")
        return []
    picks = []
    for game in data:
        if not game.get("bookmakers"):
            continue
        book = game["bookmakers"][0]
        for market in book.get("markets", []):
            if market["key"] == "h2h":
                for outcome in market["outcomes"]:
                    if 1.30 <= outcome["price"] <= 1.60:
                        picks.append({
                            "match": f"{game['home_team']} vs {game['away_team']}",
                            "league": league_name,
                            "market": f"{outcome['name']} Win",
                            "odds": outcome["price"]
                        })
            if market["key"] == "totals":
                for outcome in market["outcomes"]:
                    if outcome["price"] and 1.30 <= outcome["price"] <= 1.60:
                        picks.append({
                            "match": f"{game['home_team']} vs {game['away_team']}",
                            "league": league_name,
                            "market": f"{outcome['name']} {outcome.get('point','')}",
                            "odds": outcome["price"]
                        })
    return picks

def get_football_picks():
    all_picks = []
    for sport, league in [
        ("soccer_epl", "EPL"),
        ("soccer_spain_la_liga", "La Liga"),
        ("soccer_italy_serie_a", "Serie A"),
        ("soccer_germany_bundesliga", "Bundesliga"),
        ("soccer_france_ligue_one", "Ligue 1"),
    ]:
        all_picks.extend(get_odds_for_sport(sport, league))
    return all_picks

def get_basketball_picks():
    all_picks = []
    for sport, league in [
        ("basketball_nba", "NBA"),
        ("basketball_euroleague", "EuroLeague"),
    ]:
        all_picks.extend(get_odds_for_sport(sport, league))
    return all_picks

def main():
    print("Starting bot...")
    football_picks = get_football_picks()
    print(f"Football picks: {len(football_picks)}")
    basketball_picks = get_basketball_picks()
    print(f"Basketball picks: {len(basketball_picks)}")

    football_best = get_best_5(football_picks)
    if football_best:
        total_odds = 1
        message = "⚽ FOOTBALL - 5 ODDS 🔥\n\n"
        for p in football_best:
            total_odds *= p['odds']
            message += f"{p['match']}\n{p['league']} | {p['market']} @ {p['odds']}\n\n"
        message += f"🎯 Total Odds: {total_odds:.2f}\n"
        message += f"💰 Stake: 1000 -> Win: {1000 * total_odds:.0f}"
        send_telegram(message)
        print("Football slip sent")
    else:
        print("No football picks")

    basketball_best = get_best_5(basketball_picks)
    if basketball_best:
        total_odds = 1
        message = "🏀 BASKETBALL - 5 ODDS 🔥\n\n"
        for p in basketball_best:
            total_odds *= p['odds']
            message += f"{p['match']}\n{p['league']} | {p['market']} @ {p['odds']}\n\n"
        message += f"🎯 Total Odds: {total_odds:.2f}\n"
        message += f"💰 Stake: 1000 -> Win: {1000 * total_odds:.0f}"
        send_telegram(message)
        print("Basketball slip sent")
    else:
        print("No basketball picks")
    print("Done!")

if __name__ == "__main__":
    main()
