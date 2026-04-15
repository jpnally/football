import pandas as pd
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from tools import get_match_events

'''Messi pass map'''

matches, events, match_id = get_match_events(11, 26)

passes = events[(events['type'] == 'Pass') & (events['player'] == 'Lionel Andrés Messi Cuccittini')]

passes['start_x'] = passes.location.str[0]
passes['start_y'] = passes.location.str[1]

passes['end_x'] = passes.pass_end_location.str[0]
passes['end_y'] = passes.pass_end_location.str[1]

passes['colour'] = passes['pass_outcome'].apply(lambda outcome: 'red' if pd.notnull(outcome) else 'blue')

pitch = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='white', stripe=True)
fig, ax = plt.subplots(figsize = (18,12))

pitch.draw(ax=ax)    
pitch.arrows(passes['start_x'], passes['start_y'], passes['end_x'], passes['end_y'], color = passes['colour'], ax=ax, alpha = 0.75, zorder = 3, width = 3)

match_info = matches[matches['match_id'] == match_id].iloc[0]
title = f"Lionel Messi pass map vs {match_info['away_team']}, {match_info['match_date']}"
ax.set_title(title, fontsize=15)
fig.tight_layout()
fig.savefig('outputs/messi_pass_map.png', dpi=150)