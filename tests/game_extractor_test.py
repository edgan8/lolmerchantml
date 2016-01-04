import json
import unittest

from src.game_extractor import GameExtractor


class TestGameExtractor(unittest.TestCase):
    def test_sample_match(self):
        with open("sample_match.json", 'r') as f:
            json_data = json.loads(f.read().decode("utf-8"))
            extractor = GameExtractor(json_data)
            rows = extractor.get_rows()
            print(rows)
            winners = [r for r in rows if r['winner']]
            self.assertEquals(5, len(winners))
            self.assertEquals(10, len(rows))

if __name__ == '__main__':
    unittest.main()