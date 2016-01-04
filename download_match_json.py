from riotwatcher import (RiotWatcher, NORTH_AMERICA)
import os
import json
import sqlite3
import time

import constants

def get_match_filename(match_id):
    return "match_{0}.json".format(match_id)

def main():
    w = RiotWatcher(constants.riot_id)
    db = sqlite3.connect('matchdb')

    cursor = db.cursor()
    cursor.execute(
        '''SELECT DISTINCT match_id FROM match_by_tier ORDER BY match_id ASC'''
    )
    if not os.path.exists("matches_silver"):
        os.makedirs("matches_silver")
    os.chdir("matches_silver");
    for row in cursor:
        match_id = row[0]
        print(match_id)
        match_filename = get_match_filename(match_id)
        if (os.path.isfile(match_filename)):
            print("Skipping: {}".format(match_filename))
        else:
            try:
                match_json = w.get_match(match_id, include_timeline=True)
                with open(match_filename, 'w') as f:
                    f.write(json.dumps(match_json))
                print("Writing: {}".format(match_filename))
            except Exception as e:
                print("Failed: {0} with {1}".format(
                    match_filename,
                    e
                ))
            time.sleep(1.2)


if __name__ == "__main__":
    main()
