from statsbombpy import sb

def get_match_events(competition_id, season_id, match_index=0):

    matches = sb.matches(competition_id, season_id)
    match_id = matches['match_id'].iloc[match_index]

    events = sb.events(match_id=match_id)

    return matches, events, match_id
