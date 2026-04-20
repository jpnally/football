import pandas as pd
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch, Radar, FontManager, grid
import numpy as np
from adjustText import adjust_text
from tools import search_competition, load_comp_data, clean_filename
import re
from sklearn.preprocessing import MinMaxScaler

def save_forward_data(matches, chosen_season):
    events_list = []

    forward_positions = ['Center Forward', 'Left Wing', 'Right Wing', 'Left Center Forward', 'Right Center Forward']
    event_type = ['Goal', 'Shot', 'Carry', 'Pressure']

    for match_id in matches['match_id']:
        match_events = sb.events(match_id = match_id)
        
        forward_data = match_events[(match_events['position'].isin(forward_positions)) & (match_events['type'].isin(event_type))].copy()

        forward_data['is_shot'] = forward_data['type'] == 'Shot'
        forward_data['is_shot_ot'] = forward_data['shot_outcome'].isin(['Goal', 'Saved'])
        forward_data['is_pressure'] = forward_data['type'] == 'Pressure'
        forward_data['is_goal'] = (forward_data['shot_outcome'] == 'Goal') & (forward_data['shot_type'] != 'Penalty')

        events_list.append(forward_data)

    season = pd.concat(events_list, ignore_index = True)

    csv_filename = f"data/{clean_filename(chosen_season['competition_name'])}_{clean_filename(chosen_season['season_name'])}_forwards.csv"
    season.to_csv(csv_filename, index=False)
    print("CSV saved.")

def get_forward_data():
    season = pd.read_csv("data/1__Bundesliga_2015_2016_forwards.csv", low_memory=False)

    shot_stats = season.groupby('player').agg(
                total_shots=('is_shot', 'sum'),
                shots_ot=('is_shot_ot', 'sum'),
                xg = ('shot_statsbomb_xg', 'sum'),
                non_pen_goals = ('is_goal', 'sum')
            ).reset_index()

    shot_stats['sot_rate'] = shot_stats['shots_ot'] / shot_stats['total_shots']
    shot_stats['xg_per_shot'] = shot_stats['xg'] / shot_stats['total_shots']
    shot_stats['shot_conversion_rate'] = shot_stats['non_pen_goals'] / shot_stats['total_shots']

    pressure_stats = season.groupby('player').agg(
                    total_pressures=('is_pressure', 'sum')
                ).reset_index()

    table = pd.merge(shot_stats, pressure_stats, on='player', how='outer')
    table = table.fillna(0)

    regular_players = table[(table['total_shots'] >= 20) & (table['total_pressures'] >= 20)]

    return regular_players


def find_top_forwards(df, weights={'sot_rate':0.5, 'xg_per_shot':2, 'total_pressures':1, 'non_pen_goals': 3, 'shot_conversion_rate': 1.5}):

    metrics = list(weights.keys())
    temp_df = df[metrics].copy()

    scaler = MinMaxScaler()
    temp_df[metrics] = scaler.fit_transform(temp_df[metrics])

    df = df.copy()
    df['score'] = sum(temp_df[m] * w for m, w in weights.items())
    
    result = df.sort_values('score', ascending = False).head(10)

    print(result)
    return result


def radar_chart():
    
    column_dict = {
            'non_pen_goals'         : 'Goals',
            'shot_conversion_rate'  : 'Shot Conversion Rate',
            'sot_rate'              : 'Shot on Target Rate',
            'xg_per_shot'           : 'xG per Shot',
            'total_pressures'       : 'Total Pressures',
            'score'                 : 'Score'
    }

    param_names = list(column_dict.keys())
    display_names = list(column_dict.values())

    top_players = find_top_forwards(data)

    low = data[param_names].min().to_list()
    high = data[param_names].max().to_list()

    radar = Radar(params=display_names,
                  min_range=low,
                  max_range=high,
                  num_rings=3, 
                  center_circle_radius=1)

       


if __name__ == "__main__":

    # matches, chosen_season = load_comp_data()
    # if matches is not None:    
    #     save_forward_data(matches, chosen_season)


    data = get_forward_data()
    #radar_chart()
    find_top_forwards(data)



    