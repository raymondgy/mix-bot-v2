import os, requests
from datetime import date

API_KEY = os.environ.get("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
HEADERS = {"x-apisports-key": API_KEY}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_tennis_odds(fixture_id):
    url = f"https://v3.tennis.api-sports.io/odds?fixture={fixture_id}&bookmaker=8"
    try:
        r = requests.get(url, headers=HEADERS).json()
        resp = r.get("response", [])
        if not resp:
            return None
        for odd in resp[0].get("bookmakers", [{}])[0].get("bets", []):
            if odd["name"] == "Match Winner":
                values = odd["values"]
                fav = min(values, key=lambda x: float(x["odd"]))
                return float(fav["odd"]), fav["value"]
    except:
        return None
    return None

def get_tennis_picks():
    picks = []
    today = str(date.today())
    url = f"https://v3.tennis.api-sports.io/fixtures?date={today}"
    r = requests.get(url, headers=HEADERS).json()
    fixtures = r.get("response", [])
    for f in fixtures:
        if f["status"]["short"] != "NS":
            continue
        if len(f.get("players", [])) < 2:
            continue
        p1 = f["players"][0]
        p2 = f["players"][1]
        odds_data = get_tennis_odds(f["fixture"]["id"])
        if not odds_data:
            continue
        fav_odd, fav_name = odds_data
        if not (1.25 <= fav_odd <= 1.60):
            continue
        try:
            rank1 = int(p1.get("ranking") or 9999)
            rank2 = int(p2.get("ranking") or 9999)
            gap = abs(rank1 - rank2)
            if gap < 40:
                continue
        except:
            continue
        picks.append(f"🎾 *{p1['name']} vs {p2['name']}*\nTournament: {f['tournament']['name']}\nPick: *{fav_name} to Win @ {fav_odd}*\nReason: Ranking gap {gap} + Odds in sweet spot (1.25-1.60)\nConfidence: 78%")
        if len(picks) >= 3:
            break
    return picks

def get_team_last5_avg(team_id):
    url = f"https://v3.basketball.api-sports.io/games?team={team_id}&season=2026-2027&league=12"
    r = requests.get(url, headers=HEADERS).json()
    games = r.get("response", [])[-5:]
    if len(games) < 5:
        return None
    total = 0
    for g in games:
        if g["scores"]["home"]["total"] and g["scores"]["away"]["total"]:
            total += g["scores"]["home"]["total"] + g["scores"]["away"]["total"]
    return total / 5 if total else None

def get_nba_picks():
    picks = []
    today = str(date.today())
    url = f"https://v3.basketball.api-sports.io/games?date={today}&league=12&season=2026-2027"
    r = requests.get(url, headers=HEADERS).json()
    games = r.get("response", [])
    for g in games:
        if g["status"]["short"] != "NS":
            continue
        home = g["teams"]["home"]
        away = g["teams"]["away"]
        home_avg = get_team_last5_avg(home["id"])
        away_avg = get_team_last5_avg(away["id"])
        if not home_avg or not away_avg:
            continue
        combined = (home_avg + away_avg) / 2
        if combined > 225:
            picks.append(f"🏀 *{away['name']} @ {home['name']}*\nLeague: NBA\nPick: *Over 221.5 Total Points*\nReason: Combined avg last 5 games = {combined:.1f} pts\nConfidence: 73%")
        elif combined < 205:
            picks.append(f"🏀 *{away['name']} @ {home['name']}*\nLeague: NBA\nPick: *Under 209.5 Total Points*\nReason: Combined avg last 5 games = {combined:.1f} pts (low scoring)\nConfidence: 72%")
        else:
            continue
        if len(picks) >= 2:
            break
    return picks

def main():
    tennis = get_tennis_picks()
    nba = get_nba_picks()
    all_picks = tennis + nba
    if len(all_picks) < 2:
        send_telegram(f"⚠️ *MIX BOT V2 - {date.today()}*\n\nOnly {len(all_picks)} picks pass V2 filters today. No force bet. Bot go check again tomorrow.")
        return
    all_picks = all_picks[:5]
    msg = f"🔥 *MIX PICKS V2 - {date.today()}* | Tennis + NBA\nFilters: Tennis 1.25-1.60 odds + Ranking gap 40+ | NBA Avg 225+/205-\n\n"
    msg += "\n\n---\n\n".join(all_picks)
    msg += "\n\n---\n⚠️ *V2 Rule: Stake 1-2% per pick. Quality > Quantity. No sure odds.*"
    send_telegram(msg)
    print(f"Sent {len(all_picks)} V2 picks")

if __name__ == "__main__":
    main()
