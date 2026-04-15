import pandas as pd
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch

# competitions = sb.competitions()
# print(competitions[['competition_name', 'season_name', 'competition_id', 'season_id']])

matches = sb.matches(competition_id=11, season_id=26)
print(matches[['home_team', 'away_team', 'match_id']].head(1))

match_id = matches['match_id'].iloc[0]

events = sb.events(match_id=match_id)
# print(events['type'].value_counts())

shots = events[events['type'] == 'Shot'].copy()

shots['x'] = shots['location'].apply(lambda loc: loc[0])
shots['y'] = shots['location'].apply(lambda loc: loc[1])

shots['colour'] = shots['shot_outcome'].apply(lambda outcome: 'blue' if outcome == 'Goal' else 'red')

pitch = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='white', stripe=True)
fig, ax = plt.subplots(figsize = (18,12))

pitch.draw(ax=ax)
pitch.scatter(shots['x'], shots['y'], color = shots['colour'], ax=ax, alpha = 0.75, zorder = 3)

match_info = matches[matches['match_id'] == match_id].iloc[0]
title = f"{match_info['home_team']} vs {match_info['away_team']}, {match_info['match_date']}"
ax.set_title(title, fontsize=15, pad=10)
fig.tight_layout()
fig.savefig('outputs/shot_map.png', dpi=150)