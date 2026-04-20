from statsbombpy import sb
import re

def get_match_events(competition_id, season_id, match_index=0):
    matches = sb.matches(competition_id, season_id)
    
    match_id = matches['match_id'].iloc[match_index]

    events = sb.events(match_id=match_id)

    return matches, events, match_id

def search_competition(query):
    comps = sb.competitions()
    mask = comps['competition_name'].str.contains(query, case=False, na=False)
    results = comps[mask][['competition_name', 'season_name', 'competition_id', 'season_id']].reset_index(drop=True)
    print(results.to_string())
    return results
    
def load_comp_data():
    query = input("Enter a competition: ")
    results = search_competition(query)

    if results.empty:
        print("No competitions found.")
        return None, None

    idx = int(input("Enter index of competition: "))
    chosen_season = results.iloc[idx]

    matches = sb.matches(competition_id=chosen_season['competition_id'], season_id=chosen_season['season_id'])

    return matches, chosen_season

def clean_filename(s):
    return re.sub(r'[^\w]', '_', s) # to allow competitions with '.' and spaces to be saved as csv files