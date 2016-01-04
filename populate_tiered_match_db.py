from riotwatcher import (RiotWatcher, NORTH_AMERICA)
import csv
import os
import json
import sqlite3
import time

import constants

def main():
    p_ids = []
    with open('player_tiers.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        p_ids = [row['user_id'] for row in reader if row['tier'] == 'SILVER']

    db = sqlite3.connect('matchdb')
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_by_tier(
            user_id INTEGER KEY,
            match_id INTEGER KEY,
            tier VARCHAR(255),
            UNIQUE (user_id, match_id) ON CONFLICT REPLACE);
    """)
    db.commit()
    db.close()

    w = RiotWatcher(constants.riot_id)
    db = sqlite3.connect('matchdb')
    cursor = db.cursor()

    curTime = long(time.time()*1000)

    for user_id in p_ids:
        cursor.execute(
            '''SELECT DISTINCT user_id FROM match_by_tier WHERE user_id=?''',
            (user_id,)
        )
        if (cursor.fetchone() is None):
            match_list = []
            try:
                match_list = w.get_match_list(
                    str(user_id),
                    region=NORTH_AMERICA,
                    begin_time=curTime-1000*60*60*24*30,
                    end_time=curTime,
                )['matches']
            except Exception as e:
                print(e)
            filtered_matches = [m for m in match_list if m['queue'] == 'RANKED_SOLO_5x5']
            retVal = filtered_matches[:10]
            time.sleep(2)
            user_matches = [(user_id, m['matchId'], 'SILVER') for m in retVal]
            cursor.executemany(
                '''INSERT INTO match_by_tier (user_id, match_id, tier) VALUES (?,?, ?)''',
                user_matches
            )
            db.commit()
            print("Dealt with {0}".format(user_id))
        else:
            print("Skipped {0}".format(user_id))
    db.close()

if __name__ == "__main__":
    main()
