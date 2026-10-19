'''
Generate a number of plots/analyses to evaluate how well DTW algorithm performs
'''
import pandas as pd
from matplotlib import pyplot as plt
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

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
    loaders = {'smp': smp_head, 'scope': scope_head}
    loader = loaders[pen_type]

    ids = df['pit_id']
    raw_og_paths_series = df[df.columns[1]]

    consensus_paths = ids.apply(
        lambda x: os.path.join(script_dir, "data", "consensus", pen_type, f"{x}_match_{pen_type}.csv")
    )

    for pit_id, path, og_paths_str in zip(ids, consensus_paths, raw_og_paths_series):
        consensus = pd.read_csv(path)
        og_file_paths = [os.path.join(script_dir, p.strip()) for p in og_paths_str.split(',')]

        fig, (ax1, ax2) = plt.subplots(1, 2)
        fig.suptitle(f"{pit_id}")
        ax1.set_title('Consensus proflie')
        ax1.plot(consensus['force'], consensus['depth'])
        ax1.invert_yaxis()

        for og_path in og_file_paths:
            og_prof = loader(og_path)
            ax2.plot(og_prof['force'], og_prof['depth'], linewidth=0.5)

        ax2.invert_yaxis()
        ax2.set_title('OG profiles')
        plt.show()
        plt.close(fig)

        fig = None
        ax1 = None
        ax2 = None



plot_comparisons(smp_data, pen_type='smp')
