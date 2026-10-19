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
for i in smp_ids:
    print(i)
scope_dir = os.path.join(consensus_dir, 'scope')
scope_files = os.listdir(scope_dir)
scope_ids = get_ids(scope_files)

ram_dir = os.path.join(script_dir, 'data', 'pen_profiles', 'ram_files')
ram_files = os.listdir(ram_dir)
ram_ids = get_ids(ram_files)

strat_dir = os.path.join(script_dir, 'data', 'pit_matrix')
strat_files = [i for i in os.listdir(strat_dir) if i.endswith('_strat.csv')]
strat_ids = get_ids(strat_files)


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

    pass


def smp_scope():
    common_ids = list(set(smp_ids).intersection(scope_ids, strat_ids))

    for site_date in common_ids:
        smp_path = os.path.join(smp_dir, site_date + '_match_smp.csv')
        scope_path = os.path.join(scope_dir, site_date + '_match_scope.csv')
        strat_path = os.path.join(strat_dir, site_date + '_strat.csv')

        if not os.path.exists(scope_path):
            print(scope_path)
    pass
