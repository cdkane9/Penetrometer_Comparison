'''
Compares force values measured across consensus profiles generated for each pit
'''

import pandas as pd
import numpy as np
from pathlib import Path
import os
import re
from force_analysis.DTW.consensus_profile import prep_prof


script_dir = Path(__file__).resolve().parent.parent


def get_ids(list):
    ''' Returns list of SITE_YYYYMMDD ids'''
    pattern = r'^.*?\d{8}(?:_TS_\d+)?'
    return [re.match(pattern, f).group(0) for f in list if re.match(pattern, f)]

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

    # conver top and bot to depths, add 20% buffer
    hs = top.iloc[0]
    delta = top - bot
    t_depth = ((hs - top) + (0.1 * delta))
    b_depth = ((hs - bot) - (0.1 * delta))

    # identify indices of penetromter that fall within given layers
    layer_ix = pen_df.index[(pen_df['depth'] >= t_depth) &
                            (pen_df['depth'] <= b_depth)]

    if layer_ix.empty: return np.nan, np.nan, np.nan
    else:
        layer_mean = np.nanmean(pen_df.loc[layer_ix, 'force'])
        layer_max = np.nanmax(pen_df.loc[layer_ix, 'force'])
        layer_min = np.nanmin(pen_df.loc[layer_ix, 'force'])

    return layer_mean, layer_max, layer_min
def ram_scope():
    common_ids = list(set(ram_ids).intersection(scope_ids, strat_ids))

    for site_date in common_ids:
        ram_path = os.path.join(ram_dir, site_date + '_sram.csv')
        scope_path = os.path.join(scope_dir, site_date + '_match_scope.csv')
        strat_path = os.path.join(strat_dir, site_date + '_strat.csv')
    pass


def ram_smp():
    common_ids = list(set(ram_ids).intersection(smp_ids, strat_ids))

    for site_date in common_ids:
        ram_path = os.path.join(ram_dir, site_date + '_sram.csv')
        smp_path = os.path.join(smp_dir, site_date + '_match_smp.csv')
        strat_path = os.path.join(strat_dir, site_date + '_strat.csv')

        # read in data files
        strat_df = pd.read_csv(strat_path)
        ram_df = pd.read_csv(ram_path)
        smp_path = pd.read_csv(smp_path)

        # find top and bottom of layers, convert to depth, mm
        top_cm = strat_df['top_cm']
        bot_cm = strat_df['bottom_cm']
        hs = top_cm.iloc[0]

        top_d_cm = top_cm - hs
        bot_d_cm = bot_cm - hs

        top_d_mm = top_d_cm / 10
        bot_d_mm = bot_d_cm / 10


    pass
ram_smp()

def smp_scope():
    common_ids = list(set(smp_ids).intersection(scope_ids, strat_ids))

    for site_date in common_ids:
        smp_path = os.path.join(smp_dir, site_date + '_match_smp.csv')
        scope_path = os.path.join(scope_dir, site_date + '_match_scope.csv')
        strat_path = os.path.join(strat_dir, site_date + '_strat.csv')

        if not os.path.exists(scope_path):
            print(scope_path)
    pass
