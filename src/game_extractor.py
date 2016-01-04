from __future__ import unicode_literals


class GameExtractor(object):
    fields = [
        # These two fields always first
        'matchId',
        'summonerId',

        # Rest alphabetically
        'allyChampions',
        'championId',
        'gold5',
        'gold10',
        'gold15',
        'gold20',
        'xp5',
        'xp10',
        'xp15',
        'xp20',
        'items10',
        'opponentChampions',
        'lane',
        'purchases',
        'role',
        'xpDiff10',
        'damageTakenDiff10',
        'gdPerMin10',
        'winner',
    ]
    VALID_QUEUES = {
        'RANKED_SOLO_5x5',
        'RANKED_TEAM_5x5',
        'RANKED_PREMADE_5x5',
        'NORMAL_5x5_BLIND',
        'NORMAL_5x5_DRAFT',
    }
    VALID_MODES = {
        'CLASSIC'
    }

    def __init__(self, json_dict):
        self.data = json_dict

    def is_valid(self):
        """
        Checks if the game is a standard 5v5 game
        :return: boolean
        """
        return (
            self.data['queueType'] in self.VALID_QUEUES
            and self.data['matchMode'] in self.VALID_MODES
            and self.data['matchDuration'] > 800
        )

    def get_common_data(self):
        """
        Some features are shared among all players of a match
        :return: dictionary of shared fields
        """
        common_fields = {}
        common_fields['matchId'] = self.data['matchId']
        return common_fields

    def get_rows(self):
        """
        We need to return one row per player in the game
        :return: list of dictionaries with the row elements
        """
        rows = []
        common_fields = self.get_common_data()

        p_identities = self.data['participantIdentities']
        p_data = self.data['participants']
        winning_team = self.get_winning_team()
        items_purchased = self.get_items_purchased()
        team_champions = self.get_team_champions()
        teams = set(team_champions.keys())
        gold_per_player = self.get_gold_per_player()
        xp_per_player = self.get_xp_per_player()
        gold_diff = self.get_gold_diff()
        xp_diff = self.get_xp_diff()
        dmg_taken_diff = self.get_dmg_taken_diff()

        for p in p_identities:
            p_id = int(p['participantId'])
            p_idx = p_id - 1
            team_id = p_data[p_idx]['teamId']
            opposing_team_id = (teams - {team_id}).pop()
            player_purchases = items_purchased[p_idx]
            purchase_list = [item_pair[0] for item_pair in player_purchases]
            items_10min = {
                item_pair[0] for item_pair in player_purchases
                if item_pair[1] < 1000*60*10
            }
            cur_row = {
                'summonerId': p['player']['summonerId'],

                'allyChampions': team_champions[team_id],
                'championId': p_data[p_idx]['championId'],
                'gold5': gold_per_player[p_idx].get(5, None),
                'gold10': gold_per_player[p_idx].get(10, None),
                'gold15': gold_per_player[p_idx].get(15, None),
                'gold20': gold_per_player[p_idx].get(20, None),
                'xp5': xp_per_player[p_idx].get(5, None),
                'xp10': xp_per_player[p_idx].get(10, None),
                'xp15': xp_per_player[p_idx].get(15, None),
                'xp20': xp_per_player[p_idx].get(20, None),
                'items10': list(items_10min),
                'opponentChampions': team_champions[opposing_team_id],
                'purchases': purchase_list,
                'lane': p_data[p_idx]['timeline']['lane'],
                'role': p_data[p_idx]['timeline']['role'],
                'xpDiff10': xp_diff[p_idx],
                'damageTakenDiff10': dmg_taken_diff[p_idx],
                'gdPerMin10': gold_diff[p_idx],
                'winner': (team_id == winning_team),
            }

            cur_row.update(common_fields)
            rows.append(cur_row)

        return rows

    def get_winning_team(self):
        teams = self.data['teams']
        if teams[0]['winner']:
            return teams[0]['teamId']
        else:
            return teams[1]['teamId']

    def get_events(self):
        t_frames = self.data['timeline']['frames']
        for frame in t_frames:
            if 'events' in frame:
                for event in frame['events']:
                    yield event

    def get_participant_frames(self):
        t_frames = self.data['timeline']['frames']
        for frame in t_frames:
            yield frame['participantFrames']

    def get_team_champions(self):
        champions_per_team = {}
        p_data = self.data['participants']
        for p in p_data:
            p_team_id = p['teamId']
            p_champion = p['championId']
            if p_team_id in champions_per_team:
                champions_per_team[p_team_id].append(p_champion)
            else:
                champions_per_team[p_team_id] = [p_champion]
        return champions_per_team

    def get_items_purchased(self):
        """
        :return: list(idx by player) of lists of (item_id, timestamp) in order
        """
        items_per_player = [[] for p in range(10)]
        for event in self.get_events():
            if event['eventType'] == 'ITEM_PURCHASED':
                p_idx = int(event['participantId']) - 1
                item_id = int(event['itemId'])
                timestamp = int(event['timestamp'])
                items_per_player[p_idx].append((item_id, timestamp))
        return items_per_player



    def get_gold_per_player(self):
        """
        :return: list(idx by player) of dict of time -> gold
        """
        gold_per_player = [{} for p in range(10)]
        t_frames = self.data['timeline']['frames']
        frame_no = 0
        while frame_no < len(t_frames):
            frame = t_frames[frame_no]
            for p_frame in frame['participantFrames'].values():
                p_idx = int(p_frame['participantId']) - 1
                gold_per_player[p_idx][frame_no] = p_frame['totalGold']
            frame_no += 5
        return gold_per_player

    def get_xp_per_player(self):
        """
        :return: list(idx by player) of dict of time -> xp
        """
        xp_per_player = [{} for p in range(10)]
        t_frames = self.data['timeline']['frames']
        frame_no = 0
        while frame_no < len(t_frames):
            frame = t_frames[frame_no]
            for p_frame in frame['participantFrames'].values():
                p_idx = int(p_frame['participantId']) - 1
                xp_per_player[p_idx][frame_no] = p_frame['xp']
            frame_no += 5
        return xp_per_player

    def get_gold_diff(self):
        """
        :return: list(idx by player) of gold differential
        """
        gold_diff = [None for p in range(10)]
        participants_data = self.data['participants']
        for i in range(10):
            if 'timeline' in participants_data[i]:
                if 'goldPerMinDeltas' in participants_data[i]['timeline']:
                    gold_diff[i] = participants_data[i]['timeline']['goldPerMinDeltas']['zeroToTen']
        return gold_diff

    def get_xp_diff(self):
        """
        :return: list(idx by player) of experience differential
        """
        xp_diff = [None for p in range(10)]
        participants_data = self.data['participants']
        for i in range(10):
            if 'timeline' in participants_data[i]:
                if 'xpDiffPerMinDeltas' in participants_data[i]['timeline']:
                    xp_diff[i] = participants_data[i]['timeline']['xpDiffPerMinDeltas']['zeroToTen']
        return xp_diff

    def get_dmg_taken_diff(self):
        """
        :return: list(idx by player) of experience differential
        """
        dmg_taken_diff = [None for p in range(10)]
        participants_data = self.data['participants']
        for i in range(10):
            if 'timeline' in participants_data[i]:
                if 'damageTakenDiffPerMinDeltas' in participants_data[i]['timeline']:
                    dmg_taken_diff[i] = participants_data[i]['timeline']['damageTakenDiffPerMinDeltas']['zeroToTen']
        return dmg_taken_diff

