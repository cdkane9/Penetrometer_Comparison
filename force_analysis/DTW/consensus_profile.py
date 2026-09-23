import pandas as pd
import numpy as np
from tslearn.barycenters import dtw_barycenter_averaging
from tslearn.metrics import dtw_path
import os
import ast
from pathlib import Path
project_dir = Path(__file__).resolve().parent.parent.parent
'''
Uses dynamic time warping (DTW) to generate a consensus SMP and Scope profile for each pit.
'''

######################################################
def parse_paths(val):
    '''
    Parses profile paths from all_profiles.csv
    '''
    if pd.isna(val) or not isinstance(val, str) or val.strip() in ['', 'nan', '[]']:
        return []

    valid_paths = []

    for p in val.split(','):
        path_str = p.strip()

        if not path_str or path_str.lower in ('nan', 'none', ''): continue
        if os.path.exists(os.path.join(project_dir, path_str)):
            valid_paths.append(path_str)
        else:
            print(f'File not found: {path_str}')
    return valid_paths
######################################################
# pull out depth and force columns from each penetrometer type
def smp_head(path_in):
    '''
    Reads in raw force/distance SMP profile
    :param path_in: path to raw force profile
    :return: .csv of force depth
    '''
    try:
        prof_raw = pd.read_csv(path_in, low_memory=False, skiprows=0, usecols=[1, 2])
        prof_raw.columns = ['depth', 'force']
    except pd.errors.ParserError:
        prof_raw = pd.read_csv(path_in, low_memory=False)
        prof_raw.columns = ['depth', 'force']
    return prof_raw
def scope_head(path_in):
    df = pd.read_csv(path_in, skiprows=1, usecols=[0, 1])
    idx_init = df[df.iloc[:, 0] == 'depth (mm)'].index[0]
    scope_prof = df.iloc[idx_init + 1:].reset_index(drop=True).astype(float)
    scope_prof.columns = ['depth', 'force']
    # convert from kPa to N
    scope_prof['force'] *= 1000 * 0.0000554
    return scope_prof
######################################################
def prep_prof(paths, penetrometer, step_mm=1.0):
    '''Reads in all profiles at a pit, then returns an array of profiles and common depth vector
        Essentially resamples all the profiles with common depth values before DTW
    '''
    raw_dfs = []
    # read in profiles
    for path in paths:
        if not os.path.exists(os.path.join(project_dir, path)):
            print(f' skip path')

        try:
            if penetrometer == 'smp':
                df = smp_head(os.path.join(project_dir, path))
            elif penetrometer == 'scope':
                df = scope_head(os.path.join(project_dir, path))
            #elif penetrometer == 'ram':
            #    df = ram_head(pd.read_csv(path))

            if df is not None and not df.empty:
                df = df.sort_values('depth').drop_duplicates(subset=['depth'])
                raw_dfs.append(df)
        except Exception as e:
            print(f"Error reading {path}: {e}")

        raw_dfs.append(df)

    # determine global max/min depth for all profiles
    min_depth = max(df['depth'].min() for df in raw_dfs)
    max_depth = min(df['depth'].max() for df in raw_dfs)

    # create common depth axis to map profiles to
    common_depths = np.arange(min_depth, max_depth, step_mm)

    resampled_forces = []
    for df in raw_dfs:
        forces_interp = np.interp(common_depths, df['depth'].values, df['force'].values)
        resampled_forces.append(forces_interp)

    formatted_profiles = np.array(resampled_forces)[..., np.newaxis]

    return formatted_profiles, common_depths
######################################################
def export_consensus_profile(row, output_dir, pen):
    pit_id = row['id']
    formatted_arr = row['formatted']
    depths = row['common_depth']

    if formatted_arr is None or depths is None or len(formatted_arr) == 0:
        print(f"Skipping pit '{pit_id}': No valid formatted data.")
        return None

    try:
        consensus_force = dtw_barycenter_averaging(
            formatted_arr,
            max_iter=20,
            tol=1e-3,
            metric_params={'sakoe_chiba_radius': 15}
        ).ravel()

        # 3. Create clean DataFrame
        matched_df = pd.DataFrame({
            'depth': depths,
            'force': consensus_force
        })

        # 4. Save to matched_scopes/{pit_id}_match_scope.csv
        filename = f"{pit_id}_match_{pen}.csv"
        filepath = os.path.join(output_dir, filename)

        matched_df.to_csv(filepath, index=False)
        print(f"Saved matched profile: {filepath}")
        return filepath


    except Exception as e:
        print(f"Error processing pit '{pit_id}': {e}")
        return None
######################################################

if __name__ == '__main__':
    # read in all_profiles.csv

    all_pen_paths = pd.read_csv(os.path.join(project_dir, 'process_ingest', 'all_profiles.csv'))

    # group all pit_id and scope_paths together
    scope_profs = pd.DataFrame({
        'id': all_pen_paths['pit_id'].tolist(),
        'scope_paths': all_pen_paths['scope_profile_paths'].apply(parse_paths)
    })

    # group all pit_id and smp_paths together
    smp_profs = pd.DataFrame({
        'id': all_pen_paths['pit_id'].tolist(),
        'smp_paths': all_pen_paths['smp_profile_paths'].apply(parse_paths)
    })

    # filter out empty rows from scope_profs and smp_profs
    scope_profs = scope_profs[scope_profs['scope_paths'].map(len) > 0].copy()
    smp_profs = smp_profs[smp_profs['smp_paths'].map(len) > 0].copy()

    # generate and export saved files
    scope_profs[['formatted', 'common_depth']] = scope_profs['scope_paths'].apply(
        lambda paths: pd.Series(prep_prof(paths, penetrometer='scope', step_mm=1.0))
    )
    scope_profs['output_filepath'] = scope_profs.apply(export_consensus_profile,
                                                       axis=1,
                                                       output_dir=os.path.join(project_dir, 'data/consensus/scope'),
                                                       pen='scope')

    smp_profs[['formatted', 'common_depth']] = smp_profs['smp_paths'].apply(
        lambda paths: pd.Series(prep_prof(paths, penetrometer='smp', step_mm=1.0))
    )
    smp_profs['output_filepath'] = smp_profs.apply(export_consensus_profile,
                                                   axis=1,
                                                   output_dir=os.path.join(project_dir, 'data/consensus/smp'),
                                                   pen='smp')

