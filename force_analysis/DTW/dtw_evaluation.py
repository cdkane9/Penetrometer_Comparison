'''
Generate a number of plots/analyses to evaluate how well DTW algorithm performs
'''
import pandas as pd
from matplotlib import pyplot as plt
import os
from pathlib import Path
from consensus_profile import scope_head, smp_head

script_dir = Path(__file__).resolve().parent.parent.parent
all_profiles = pd.read_csv(os.path.join(script_dir, 'process_ingest', 'all_profiles.csv'))

# separate rows for scope, smp, and retain relevant columns
scope_data = all_profiles[all_profiles['scope_profile_paths'].notna()].copy()
scope_data = scope_data[['pit_id', 'scope_profile_paths']]

smp_data = all_profiles[all_profiles['smp_profile_paths'].notna()].copy()
smp_data = smp_data[['pit_id', 'smp_profile_paths']]


def plot_comparisons(df, pen_type:str):
    ids = df['pit_id']
    og_paths = df[df.columns[1]]

    consensus_paths = ids.apply(
        lambda x: os.path.join(script_dir, "data", "consensus", pen_type, f"{x}_match_{pen_type}.csv")
    )

    for pit_id, path, og_paths in zip(ids, consensus_paths, og_paths):
        consensus = pd.read_csv(path)
        


plot_comparisons(smp_data, pen_type='smp')
