import csv
import json
import os
import os.path

from src.game_extractor import GameExtractor

TOTAL_FILES = 12000
MATCH_DIR = 'matches_silver'
OUTPUT_FILE = 'parser_silver.csv'


def main():
    rows = []
    cur_dir = os.getcwd()
    match_dir = os.path.join(cur_dir, MATCH_DIR)
    file_count = 0
    for file_name in os.listdir(match_dir):
        if file_count >= TOTAL_FILES:
            break
        if file_count % 100 == 0:
            print(file_count)
        if file_name.lower().endswith(".json"):
            file_path = os.path.join(match_dir, file_name)
            with open(file_path, 'r') as f:
                f_content = f.read().decode("utf-8")

            try:   
                json_data = json.loads(f_content)
                ge = GameExtractor(json_data)
                if ge.is_valid():
                    rows.extend(ge.get_rows())
                else:
                    print("Skipping Invalid")
            except Exception as e:
                print(str(e) + " " + file_path)
        file_count += 1

    with open(OUTPUT_FILE, 'wb') as csvfile:
        wr = csv.DictWriter(csvfile, GameExtractor.fields, quoting=csv.QUOTE_ALL)
        wr.writeheader()
        wr.writerows(rows)
    return


if __name__ == "__main__":
    main()
