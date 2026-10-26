'''
Generates Data Frames with force values and stratigraphic properties
'''

import pandas as pd
import numpy as np
from pathlib import Path
import os
import re
from DTW.profile_matching import *
from matplotlib import pyplot as plt



script_dir = Path(__file__).resolve().parent.parent
cache_dir = script_dir / 'data' / 'cache'
cache_dir.mkdir(parents=True, exist_ok=True)

def cache_dataframe(df: pd.DataFrame, name:str) -> Path:
    '''Save a df to local cache directory'''
    cache_path = cache_dir / f'{name}.pkl'
    df.to_pickle(cache_path)
    return cache_path

def load_cached_dataframe(name: str) -> pd.DataFrame:
    '''load df from local cache directory'''
    cache_path = cache_dir / f'{name}.pkl'
    return pd.read_pickle(cache_path)

def get_cached_dataframe(name: str, generator_func, refresh: bool=False) -> pd.DataFrame:
    '''
    Load cached df if available, otherwise generate and cache it
    :param name: cache filename w/o extension
    :param generator_func: function that creates df
    :param refresh: if True, regenerate even if cache exists
    :return: df
    '''

    cache_path = cache_dir / f'{name}.pkl'

    if cache_path.exists() and not refresh:
        return pd.read_pickle(cache_path)

    df = generator_func()
    df.to_pickle(cache_path)
    return df

def get_ids(a_list):
    ''' Returns list of SITE_YYYYMMDD ids'''
    pattern = r'^.*?\d{8}(?:_TS_\d+)?'
    return [re.match(pattern, f).group(0) for f in a_list if re.match(pattern, f)]

# directory for smp, scope, and ram profiles, stratigraphy profiles
consensus_dir = os.path.join(script_dir, 'data', 'consensus')

smp_dir = os.path.join(consensus_dir, 'smp')
smp_files = os.listdir(smp_dir)
smp_ids = get_ids(smp_files)
scope_dir = os.path.join(consensus_dir, 'scope')
scope_files = os.listdir(scope_dir)
scope_ids = get_ids(scope_files)

ram_dir = os.path.join(script_dir, 'data', 'pen_profiles', 'ram_files')
ram_files = os.listdir(ram_dir)
ram_ids = get_ids(ram_files)

strat_dir = os.path.join(script_dir, 'data', 'pit_matrix')
strat_files = [i for i in os.listdir(strat_dir) if i.endswith('_strat.csv')]
strat_ids = get_ids(strat_files)

def get_hardness(pen_df:pd.DataFrame, top:pd.Series, bot:pd.Series):
    '''
    Function to calculate force across stratigraphic layers
    :param pen_df: data from penetrometer with columns ['depth', 'force']
    :param top: top of layer
    :param bot: bottom of layer
    :NOTE: top_depth and bot_depth should be in units that match penetrometer
        (i.e. [mm] for scope and SMP, [cm] for ram)
    :return:
    '''

    # convert top and bot to depths, add 20% buffer
    hs = top.iloc[0]
    delta = top - bot
    t_depths = ((hs - top) + (0.1 * delta))
    b_depths = ((hs - bot) - (0.1 * delta))

    means, maxs, mins = [], [], []

    # Iterate over each layer's scalar boundaries
    for t_depth, b_depth in zip(t_depths, b_depths):
        # Compare penetrometer depth Series against scalar floats
        mask = (pen_df['depth'] >= t_depth) & (pen_df['depth'] <= b_depth)
        layer_force = pen_df.loc[mask, 'force']

        if layer_force.empty:
            means.append(np.nan)
            maxs.append(np.nan)
            mins.append(np.nan)

        else:
            means.append(np.nanmean(layer_force))
            maxs.append(np.nanmax(layer_force))
            mins.append(np.nanmin(layer_force))


    return means, maxs, mins

def ram_smp() -> pd.DataFrame:
    '''
    Compares SMP and Ram force across stratigraphic layers
    :return: DF with stratigraphic parameters, max, min, mean force from each instrument
    '''
    common_ids = list(set(ram_ids).intersection(smp_ids, strat_ids))
    all_pit_dfs = []


    for site_date in common_ids:
        ram_path = os.path.join(ram_dir, site_date + '_sram.csv')
        smp_path = os.path.join(smp_dir, site_date + '_match_smp.csv')
        strat_path = os.path.join(strat_dir, site_date + '_strat.csv')

        # read in data files
        strat_df = pd.read_csv(strat_path).copy()
        ram_df_raw = pd.read_csv(ram_path)

        # pull out depth and force from ram profile
        ram_df = pd.DataFrame({
            'depth': ram_df_raw['l_cm'] * 10,
            'force': ram_df_raw['rr_N']
        })

        # read in consensus SMP profile
        smp_df = pd.read_csv(smp_path)
        '''
        # match the ram to the SMP profile
        formatted_profiles, common_depths = prep_profs(smp_df, ram_df)
        smp_trimmed, ram_matched = match_profile(formatted_profiles,
                                                 common_depths,
                                                 radius=15)

        
        fig, (ax1, ax2) = plt.subplots(1, 2)
        ax1.step(ram_trimmed['force'], ram_trimmed['depth'])
        ax1.set_title('Ram')
        ax1.invert_yaxis()


        ax2.plot(smp_matched['force'], smp_matched['depth'])
        ax2.set_title('MatchedSMP')
        ax2.invert_yaxis()
        fig.suptitle(site_date)
        plt.show()'''

        # find top and bottom of layers, convert to mm
        top_mm = strat_df['top_cm'] * 10
        bot_mm = strat_df['bottom_cm'] * 10

        ram_mean, ram_max, ram_min = get_hardness(ram_df, top_mm, bot_mm)
        smp_mean, smp_max, smp_min = get_hardness(smp_df, top_mm, bot_mm)

        # Assign identifiers and calculated stats directly to strat_df
        strat_df.insert(0, 'pit_id', site_date)

        strat_df['ram_mean_N'] = ram_mean
        strat_df['ram_min_N'] = ram_min
        strat_df['ram_max_N'] = ram_max

        strat_df['smp_mean_N'] = smp_mean
        strat_df['smp_min_N'] = smp_min
        strat_df['smp_max_N'] = smp_max

        # Collect the populated DataFrame
        all_pit_dfs.append(strat_df)
    master_df = pd.concat(all_pit_dfs, ignore_index=True)

    return master_df

def ram_scope() -> pd.DataFrame:
    common_ids = list(set(ram_ids).intersection(scope_ids, strat_ids))
    all_pit_dfs = []

    for site_date in common_ids:
        ram_path = os.path.join(ram_dir, site_date + '_sram.csv')
        scope_path = os.path.join(scope_dir, site_date + '_match_scope.csv')
        strat_path = os.path.join(strat_dir, site_date + '_strat.csv')

        # read in data files
        strat_df = pd.read_csv(strat_path).copy()
        ram_df_raw = pd.read_csv(ram_path)

        # pull out depth and force from ram profile
        ram_df = pd.DataFrame({
            'depth': ram_df_raw['l_cm'] * 10,
            'force': ram_df_raw['rr_N']
        })


        # read in consensus SMP profile
        scope_df = pd.read_csv(scope_path)


        # match profiles
        #formatted_profiles, common_depths = prep_profs(scope_df, ram_df)
        #scope_trimmed, ram_matched = match_profile(formatted_profiles,
        #                                           common_depths,
        #                                           radius=15)

        # find top and bottom of layers, convert to mm
        top_mm = strat_df['top_cm'] * 10
        bot_mm = strat_df['bottom_cm'] * 10

        ram_mean, ram_max, ram_min = get_hardness(ram_df, top_mm, bot_mm)
        scope_mean, scope_max, scope_min = get_hardness(scope_df, top_mm, bot_mm)

        # add calculated stats to the stratigraphy df
        strat_df.insert(0, 'pit_id', site_date)

        strat_df['ram_mean_N'] = ram_mean
        strat_df['ram_min_N'] = ram_min
        strat_df['ram_max_N'] = ram_max

        strat_df['scope_mean_N'] = scope_mean
        strat_df['scope_min_N'] = scope_min
        strat_df['scope_max_N'] = scope_max

        all_pit_dfs.append(strat_df)

    master_df = pd.concat(all_pit_dfs, ignore_index=True)
    return master_df

def smp_scope() -> pd.DataFrame:
    common_ids = list(set(smp_ids).intersection(scope_ids, strat_ids))
    all_pit_dfs = []

    for site_date in common_ids:
        smp_path = os.path.join(smp_dir, site_date + '_match_smp.csv')
        scope_path = os.path.join(scope_dir, site_date + '_match_scope.csv')
        strat_path = os.path.join(strat_dir, site_date + '_strat.csv')
        if not os.path.exists(strat_path):
            continue

        # read in data files

        strat_df = pd.read_csv(strat_path).copy()
        scope_df = pd.read_csv(scope_path)
        smp_df = pd.read_csv(smp_path)

        # match the scope to the SMP
        formatted_profiles, common_depths = prep_profs(smp_df, scope_df)
        smp_trimmed, scope_matched = match_profile(formatted_profiles,
                                                   common_depths,
                                                   radius=15)

        # find top and bottom of stratigraphy layers, convert to mm
        top_mm = strat_df['top_cm'] * 10
        bot_mm = strat_df['bottom_cm'] * 10

        scope_mean, scope_max, scope_min = get_hardness(scope_matched, top_mm, bot_mm)
        smp_mean, smp_max, smp_min = get_hardness(smp_trimmed, top_mm, bot_mm)

        # add calculated stats to stratigraphy df
        strat_df.insert(0, 'pit_id', site_date)

        strat_df['smp_mean_N'] = smp_mean
        strat_df['smp_min_N'] = smp_min
        strat_df['smp_max_N'] = smp_max

        strat_df['scope_mean_N'] = scope_mean
        strat_df['scope_min_N'] = scope_min
        strat_df['scope_max_N'] = scope_max

        all_pit_dfs.append(strat_df)
    master_df = pd.concat(all_pit_dfs, ignore_index=True)
    return master_df

def get_ram_smp(refresh: bool=False) -> pd.DataFrame:
    return get_cached_dataframe('ram_smp', ram_smp, refresh=refresh)

def get_ram_scope(refresh: bool=False) -> pd.DataFrame:
    return get_cached_dataframe('ram_scope', ram_scope, refresh=refresh)

def get_smp_scope(refresh: bool=False) -> pd.DataFrame:
    return get_cached_dataframe('smp_scope', smp_scope, refresh=refresh)

if __name__ == '__main__':
    #smp_ram = get_ram_smp()
    #scope_ram = get_ram_scope()
    scope_smp = get_smp_scope(True)