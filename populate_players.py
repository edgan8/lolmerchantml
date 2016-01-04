import riotwatcher as rw
import csv
import os
import json
import time
import copy

import constants

curTime = long(time.time()*1000)


def get_tiers(w, user_ids):
    """
    :type w: rw.RiotWatcher
    """
    max_chunk_size = 10
    user_id_chunks = [user_ids[i:i+max_chunk_size] for i in xrange(0, len(user_ids), max_chunk_size)]
    tiers = {}
    for user_chunk in user_id_chunks:
        user_data = w.get_league_entry(
            summoner_ids=user_chunk,
            region=rw.NORTH_AMERICA,
        )
        time.sleep(1)
        for user_id, data in user_data.viewitems():
            for queue in data:
                if queue['queue'] == 'RANKED_SOLO_5x5':
                    tiers[int(user_id)] = queue['tier']
    return tiers


def get_neighbors(w, user_id):
    """
    :type w: rw.RiotWatcher
    """
    recent_games = w.get_recent_games(user_id)
    time.sleep(1)
    games = [g for g in recent_games['games'] if g['subType'] == 'RANKED_SOLO_5x5']
    player_sets = [g['fellowPlayers'] for g in games]
    neighbors = set()
    for p_set in player_sets:
        for player in p_set:
            neighbors.add(player['summonerId'])
    return neighbors


def mark_row_crawled(rows, user_id):
    for row in rows:
        if row['user_id'] == user_id:
            row['crawled'] = 1


def main():
    w = rw.RiotWatcher(constants.riot_id)

    cur_data = {}
    with open('player_tiers.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cur_data[row['user_id']] = row

    ids_to_crawl = {row['user_id'] for row in cur_data.viewvalues()
                    if row['tier'] in ["SILVER"] and row['crawled'] == '0'}
    total_ids = set(cur_data.viewkeys())

    new_data = copy.deepcopy(cur_data)

    for x in range(100):
        cur_id = ids_to_crawl.pop()
        print("Crawling: {0}".format(cur_id))
        neighbor_ids = get_neighbors(w, cur_id)
        neighbor_ids -= total_ids
        neighbor_ids = list(neighbor_ids)[:40]
        neighbor_tiers = get_tiers(w, neighbor_ids)

        for n_id, n_tier in neighbor_tiers.viewitems():
            new_data[n_id] = {
                'user_id': n_id,
                'tier': n_tier,
                'crawled': 0,
            }
            ids_to_crawl.add(n_id)
        total_ids |= set(neighbor_tiers.keys())
        new_data[cur_id]['crawled'] = 1

    sorted_rows = new_data.values()
    sorted_rows.sort(key=lambda row: (1-int(row['crawled']), row['user_id']))

    with open('player_tiers.csv', 'w') as csvout:
        writer = csv.DictWriter(csvout, fieldnames=['user_id', 'tier', 'crawled'])
        writer.writeheader()
        writer.writerows(sorted_rows)


if __name__ == "__main__":
    main()
