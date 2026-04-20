import pandas as pd
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import numpy as np
from adjustText import adjust_text

comps = sb.competitions()
pl = comps[comps['competition_name'] == 'Premier League']
latest_pl = pl.sort_values('season_name', ascending = False).iloc[0]

pl_comp_id = latest_pl['competition_id']
pl_season_id = latest_pl['season_id']

pl_matches = sb.matches(competition_id=pl_comp_id, season_id=pl_season_id)

#print(pl_matches[['home_team', 'home_score', 'away_score', 'away_team', 'match_id', 'match_date']].head(20))

def save_data():
    events_list = []

    for match_id in pl_matches['match_id']:
        match_events = sb.events(match_id = match_id)
        
        passes_tackles = match_events[match_events['type'].isin(['Pass', 'Duel'])].copy()
        
        events_list.append(passes_tackles)

    season = pd.concat(events_list, ignore_index = True)

    season['pass_success'] = (season['type'] == 'Pass') & (season['pass_outcome'].isnull())
    season['tackle_success'] = (season['duel_type'] == 'Tackle') & (season['duel_outcome'].isin(['Won', 'Success', 'Success In Play']))

    if 'location' in season.columns:
        season['start_x'] = season['location'].str[0]
        season['start_y'] = season['location'].str[1]

    if 'pass_end_location' in season.columns:
        season['end_x'] = season['pass_end_location'].str[0]
        season['end_y'] = season['pass_end_location'].str[1]    

    csv_filename = "data/1516_pl_passes_tackles.csv"
    season.to_csv(csv_filename, index=False)
    print("CSV saved.")

season = pd.read_csv("data/1516_pl_passes_tackles.csv", low_memory=False)

# top_passers = season.groupby('player')['pass_success'].sum().sort_values(ascending=False)
# top_tacklers = season.groupby('player')['tackle_success'].sum().sort_values(ascending=False)

# print(top_passers.head(25))
# print(top_tacklers.head(25))

def get_pass_stats():

    pass_stats = season.groupby('player').agg(
            total_passes=('pass_success', 'count'),
            successful_passes=('pass_success', 'sum')
        ).reset_index()
    
    return pass_stats

def best_passers():

    pass_stats = get_pass_stats()

    regular_passers = pass_stats[pass_stats['total_passes'] > 400]
    regular_passers['pass_rate'] = (regular_passers['successful_passes'] / regular_passers['total_passes']) * 100
    best_pass_rate = regular_passers.sort_values('pass_rate', ascending=False)

    return best_pass_rate


def pass_vs_tackle():

    pass_stats = get_pass_stats()

    successful_passes = season[(season['pass_success'] == True) & (season['type'] == 'Pass')].copy()

    '''ball closer to goal by >10 yards'''
    successful_passes['pass_distance'] = np.sqrt( 
             (successful_passes['start_y'] - 40)**2 + (successful_passes['start_x'] - 120)**2 ) - np.sqrt(
         (successful_passes['end_y'] - 40)**2 + (successful_passes['end_x'] - 120)**2 )
    
    prog_passes_events = successful_passes[(successful_passes['pass_distance'] >= 10) & (successful_passes['start_x'] > 40)]

    prog_pass_stats = prog_passes_events.groupby('player').agg(
            prog_passes=('pass_distance', 'count')
        ).reset_index()

    
    tackles_events = season[season['type'] == 'Duel']
    tackles_stats = tackles_events.groupby('player').agg(
        total_tackles=('tackle_success', 'count'),
        successful_tackles=('tackle_success', 'sum')
    )

    table = pd.merge(prog_pass_stats, tackles_stats, on='player', how='outer')
    table = pd.merge(table, pass_stats, on='player', how='outer')

    table = table.fillna(0)

    regular_players = table[(table['total_passes'] > 400) & (table['total_tackles'] > 10)]

    return regular_players
    

def plot_graph():

    data = pass_vs_tackle()

    data['product'] = (data['prog_passes']/data['total_passes'] * data['successful_tackles'])
    data['pass_rate'] = (data['prog_passes']/data['total_passes'])
    top_players = data.sort_values('product', ascending=False).head(5)
    top_passers = data.sort_values('pass_rate', ascending=False).head(2)
    top_tacklers = data.sort_values('successful_tackles', ascending=False).head(2)

    fig, ax = plt.subplots(figsize = (20,12))

    ax.scatter(data['prog_passes']/data['total_passes'] * 100, data['successful_tackles'], marker = 'x', c = 'black')
    ax.scatter(top_players['prog_passes']/top_players['total_passes'] * 100, top_players['successful_tackles'], marker = 'x', c = 'red')
    ax.scatter(top_passers['prog_passes']/top_passers['total_passes'] * 100, top_passers['successful_tackles'], marker = 'x', c = 'red')
    ax.scatter(top_tacklers['prog_passes']/top_tacklers['total_passes'] * 100, top_tacklers['successful_tackles'], marker = 'x', c = 'red')
    
    texts = []
    for index, row in top_players.iterrows():
        texts.append(ax.text(
            x=row['prog_passes']/row['total_passes'] * 100,
            y=row['successful_tackles'],
            s=row['player'],
            fontsize=11,
            color='red',
            #weight='bold'
        ))
    for index, row in top_passers.iterrows():
        texts.append(ax.text(
            x=row['prog_passes']/row['total_passes'] * 100,
            y=row['successful_tackles'],
            s=row['player'],
            fontsize=11,
            color='red',
            #weight='bold'
        ))
    for index, row in top_tacklers.iterrows():
        texts.append(ax.text(
            x=row['prog_passes']/row['total_passes'] * 100,
            y=row['successful_tackles'],
            s=row['player'],
            fontsize=11,
            color='red',
            #weight='bold'
        ))    

    adjust_text(texts, ax=ax)

    title = f"Successful tackles vs progressive pass rate, Premier League 2015/16"
    ax.set_title(title, fontsize=18, pad=3)
    ax.set_xlabel("Progressive pass rate (% of total passes)", fontsize = 16)
    ax.set_ylabel("Successful tackles", fontsize = 16)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    fig.tight_layout()
    fig.savefig('outputs/passes_tackles.png', dpi=150)

    
if __name__ == "__main__":
    plot_graph()