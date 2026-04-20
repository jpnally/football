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

    shot_stats = season.groupby(['player', 'team']).agg(
                total_shots=('is_shot', 'sum'),
                shots_ot=('is_shot_ot', 'sum'),
                xg = ('shot_statsbomb_xg', 'sum'),
                non_pen_goals = ('is_goal', 'sum')
            ).reset_index()

    shot_stats['sot_rate'] = shot_stats['shots_ot'] / shot_stats['total_shots']
    shot_stats['xg_per_shot'] = shot_stats['xg'] / shot_stats['total_shots']
    shot_stats['shot_conversion_rate'] = shot_stats['non_pen_goals'] / shot_stats['total_shots']

    pressure_stats = season.groupby(['player']).agg(
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

    #print(result)
    return result


def radar_chart():
    
    URL1 = ('https://raw.githubusercontent.com/googlefonts/SourceSerifProGFVersion/main/fonts/'
        'SourceSerifPro-Regular.ttf')
    serif_regular = FontManager(URL1)
    URL2 = ('https://raw.githubusercontent.com/googlefonts/SourceSerifProGFVersion/main/fonts/'
            'SourceSerifPro-ExtraLight.ttf')
    serif_extra_light = FontManager(URL2)
    URL3 = ('https://raw.githubusercontent.com/google/fonts/main/ofl/rubikmonoone/'
            'RubikMonoOne-Regular.ttf')
    rubik_regular = FontManager(URL3)
    URL4 = 'https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Thin.ttf'
    robotto_thin = FontManager(URL4)
    URL5 = ('https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/'
            'RobotoSlab%5Bwght%5D.ttf')
    robotto_bold = FontManager(URL5)


    column_dict = {
            'non_pen_goals'         : 'Non-penalty Goals',
            'shot_conversion_rate'  : 'Shot Conversion Rate',
            'sot_rate'              : 'Shot on Target Rate',
            'xg_per_shot'           : 'xG per Shot',
            'total_pressures'       : 'Total Pressures'
    }

    param_names = list(column_dict.keys())
    display_names = list(column_dict.values())

    top_players = find_top_forwards(data)

    low = data[param_names].min().to_list()
    high = data[param_names].max().to_list()

    radar = Radar(params=display_names,
                  min_range=low,
                  max_range=high,
                  num_rings=4, 
                  center_circle_radius=1)


    '''most of radar chart code from mplsoccer documentation'''

    # fig, ax = radar.setup_axis(figsize=(10,10))  # format axis as a radar
    # rings_inner = radar.draw_circles(ax=ax, facecolor="#9e9e9e9e", edgecolor="#292929")  # draw circles
    # radar_output = radar.draw_radar(top_players.iloc[0][param_names], ax=ax,
    #                                 kwargs_radar={'facecolor': "#9c4c4c"},
    #                                 kwargs_rings={'facecolor': "#5bac3b"})  # draw the radar
    # radar_poly, rings_outer, vertices = radar_output
    # range_labels = radar.draw_range_labels(ax=ax, fontsize=15)  # draw the range labels
    # param_labels = radar.draw_param_labels(ax=ax, fontsize=15)  # draw the param labels
    
    # ax.set_title(top_players.iloc[0]['player'], fontsize=16, pad=20)
    # fig.set_facecolor('#1a1a2e')
    # fig.savefig('outputs/radar.png', dpi=150)


    fig, axs = grid(figheight=14, grid_height=0.915, title_height=0.06, endnote_height=0.025,
                title_space=0, grid_key='radar', axis=False, endnote_space=0)
    
    radar.setup_axis(ax=axs['radar'], facecolor='None')
    rings_inner = radar.draw_circles(ax=axs['radar'], facecolor="#2a2a4a", edgecolor="#343447", lw=1.5)
    radar_output = radar.draw_radar_compare(top_players.iloc[0][param_names], top_players.iloc[1][param_names], ax=axs['radar'],
                                        kwargs_radar={'facecolor': '#00d4ff', 'alpha': 0.4},
                                        kwargs_compare={'facecolor': '#ff6b6b', 'alpha': 0.4})
    radar_poly, radar_poly2, vertices1, vertices2 = radar_output
    range_labels = radar.draw_range_labels(ax=axs['radar'], fontsize=25,
                                       fontproperties=robotto_thin.prop, color="#DADADA")
    param_labels = radar.draw_param_labels(ax=axs['radar'], fontsize=25,
                                       fontproperties=robotto_thin.prop, color="#DADADA")
    
    axs['radar'].scatter(vertices1[:, 0], vertices1[:, 1],
                     c="#00d4ff", edgecolors='#6d6c6d', marker='o', s=150, zorder=2)
    axs['radar'].scatter(vertices2[:, 0], vertices2[:, 1],
                     c="#ff6b6b", edgecolors='#6d6c6d', marker='o', s=150, zorder=2)

    title1_text = axs['title'].text(0.01, 0.65, top_players.iloc[0]['player'], fontsize=25,
                                    fontproperties=robotto_bold.prop,
                                    ha='left', va='center', color="#00d4ff")
    title2_text = axs['title'].text(0.01, 0.25, top_players.iloc[0]['team'], fontsize=20,
                                    fontproperties=robotto_thin.prop,
                                    ha='left', va='center', color="#DADADA")
    title3_text = axs['title'].text(0.99, 0.65, top_players.iloc[1]['player'], fontsize=25,
                                    fontproperties=robotto_bold.prop,
                                    ha='right', va='center', color="#ff6b6b")
    title4_text = axs['title'].text(0.99, 0.25, top_players.iloc[1]['team'], fontsize=20,
                                    fontproperties=robotto_thin.prop,
                                    ha='right', va='center', color="#DADADA")
    title5_text = axs['endnote'].text(0.99, 0.4, '1. Bundesliga, 2015/2016', fontsize=20,
                                    fontproperties=robotto_bold.prop,
                                    ha='right', va='center', color="#A8A5A5")

    fig.set_facecolor('#1a1a2e')
       
    fig.savefig('outputs/comparison_radar.png', dpi=150)


if __name__ == "__main__":

    # matches, chosen_season = load_comp_data()
    # if matches is not None:    
    #     save_forward_data(matches, chosen_season)

    data = get_forward_data()
    radar_chart()
    # find_top_forwards(data)
