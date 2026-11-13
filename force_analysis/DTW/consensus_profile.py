import openpyxl
import pandas as pd
import numpy as np
from tslearn.barycenters import dtw_barycenter_averaging
from tslearn.metrics import dtw_path_from_metric
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
def dba_absolute_distance(X, max_iter=30, tol=1e-5,
                          itakura_max_slope=2):
    '''
    Uses absolute distance (cityblock) to calculate distance between profiles
    :param X: 3D numpy array w/ shape (n_profiles, length, 1)
    :param max_iter: total number of iterations (might remove)
    :param tol: cost improvement threshold (might remove)
    :param sakoe_chiba_radius:
    :return: 1D numpy array of consensus force values
    '''

    n_series, length, _ = X.shape

    # generate initial consensus profile (i.e. mean of all profiles)
    barycenter = np.median(X, axis=0)
    prev_cost = np.inf

    constraint_kwargs = {}
    if itakura_max_slope is not None and itakura_max_slope > 0:
        constraint_kwargs = {
            'global_constraint': 'itakura',
            'itakura_max_slope': int(itakura_max_slope)
        }

    for _ in range(max_iter):
        aligned_values = [[] for _ in range(length)]
        total_cost = 0

        # align each profile to current consensus using absolute distance
        for i in range(n_series):
            path, cost = dtw_path_from_metric(
                barycenter,
                X[i],
                metric='cityblock',
                **constraint_kwargs
            )
            total_cost += cost
            for idx_b, idx_x in path:
                aligned_values[idx_b].append(X[i, idx_x, 0])

        # update new consensus profile with mean of wapred profiles
        new_barycenter = np.copy(barycenter)
        for t in range(length):
            if aligned_values[t]:
                new_barycenter[t] = np.median(aligned_values[t])

        barycenter = new_barycenter

        # check convergence
        if abs(prev_cost - total_cost) < tol:
            break
        prev_cost = total_cost

    return barycenter.ravel()

######################################################
def export_consensus_profile(row, output_dir, pen):
    pit_id = row['id']
    formatted_arr = row['formatted']
    depths = row['common_depth']

    if formatted_arr is None or depths is None or len(formatted_arr) == 0:
        print(f"Skipping pit '{pit_id}': No valid formatted data.")
        return None

    try:
        consensus_force = dba_absolute_distance(
            formatted_arr,
            max_iter=30,
            tol=1e-5,
            itakura_max_slope=3
        )

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

