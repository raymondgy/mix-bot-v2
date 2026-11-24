def main():
    print("Starting bot...")

    football_picks = get_football_picks()
    print(f"Football picks: {len(football_picks)}")

    basketball_picks = get_basketball_picks()
    print(f"Basketball picks: {len(basketball_picks)}")

    # Football slip - 5 odds alone
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

    # Basketball slip - 5 odds alone
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
