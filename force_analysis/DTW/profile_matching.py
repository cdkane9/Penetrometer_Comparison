'''
Various functions required to match two profiles together
'''

import pandas as pd
import numpy as np
from tslearn.barycenters import dtw_barycenter_averaging
from tslearn.metrics import dtw_path_from_metric
from scipy.signal import savgol_filter


def smooth_profile_savgol(df, window_length=10, polyorder=2):
    '''
    Smoothes a penetrometer force profile using a Savitzky-Golay filter.

    :param df: DataFrame with ['depth', 'force']
    :param window_length: Number of sampling points in the filter window (must be an odd int)
    :param polyorder: Order of the polynomial used to fit samples
    :return: Copy of DataFrame with smoothed force values
    '''
    df_smooth = df.copy().sort_values('depth').reset_index(drop=True)

    # Ensure window_length is odd and does not exceed data length
    wl = min(window_length, len(df_smooth))
    if wl % 2 == 0:
        wl -= 1

    # Only smooth if profile has enough data points
    if wl > polyorder:
        df_smooth['force'] = savgol_filter(df_smooth['force'].values, window_length=wl, polyorder=polyorder)

    return df_smooth

def normalize_force(force):
    '''
    Normalize force using z-score normalization
    :param force: 1D array of force values
    :return: normalized force values
    '''

    force_std = np.std(force)

    if force_std == 0:
        return np.zeros_like(force)

    return (force - np.mean(force)) / force_std

def prep_profs(prof1, prof2):
    '''
    Resamples two profiles with a common depth grid
    :param prof1: df with columns ['depth', 'force'] --> considered truth
    :param prof2: df with columns ['depth', 'force'] --> profile to be stretched
            Both prof1 and prof2 should be in units of mm
    :return: Interpolated force profiles, common depth array
        formatted_profiles - returns prof1, prof2
    '''

    required_cols = {'depth', 'force'}
    missing_prof1 = required_cols.difference(prof1.columns)
    missing_prof2 = required_cols.difference(prof2.columns)

    if missing_prof1:
        raise ValueError(f'prof1 is missing required columns: {sorted(missing_prof1)}')
    if missing_prof2:
        raise ValueError(f'prof2 is missing required columns: {sorted(missing_prof2)}')

    prof1 = prof1[['depth', 'force']].copy()
    prof2 = prof2[['depth', 'force']].copy()

    prof1['depth'] = pd.to_numeric(prof1['depth'], errors='coerce')
    prof1['force'] = pd.to_numeric(prof1['force'], errors='coerce')
    prof2['depth'] = pd.to_numeric(prof2['depth'], errors='coerce')
    prof2['force'] = pd.to_numeric(prof2['force'], errors='coerce')

    prof1 = prof1.replace([np.inf, -np.inf], np.nan).dropna(subset=['depth', 'force'])
    prof2 = prof2.replace([np.inf, -np.inf], np.nan).dropna(subset=['depth', 'force'])

    prof1 = prof1.sort_values('depth').drop_duplicates(subset='depth')
    prof2 = prof2.sort_values('depth').drop_duplicates(subset='depth')

    if prof1.empty:
        raise ValueError('prof1 has no valid depth/force rows after cleaning.')
    if prof2.empty:
        raise ValueError('prof2 has no valid depth/force rows after cleaning.')

    min_depth = int(np.ceil(max(prof1['depth'].min(), prof2['depth'].min())))
    max_depth = int(np.floor(min(prof1['depth'].max(), prof2['depth'].max())))

    if max_depth <= min_depth:
        raise ValueError(
            'Profiles do not have an overlapping depth range. '
            f'prof1 range=({prof1["depth"].min()}, {prof1["depth"].max()}), '
            f'prof2 range=({prof2["depth"].min()}, {prof2["depth"].max()})'
        )

    prof1 = prof1[(prof1['depth'] >= min_depth) & (prof1['depth'] <= max_depth)]
    prof2 = prof2[(prof2['depth'] >= min_depth) & (prof2['depth'] <= max_depth)]

    if prof1.empty:
        raise ValueError('prof1 has no samples inside the shared depth range.')
    if prof2.empty:
        raise ValueError('prof2 has no samples inside the shared depth range.')

    prof1 = smooth_profile_savgol(prof1, window_length=10, polyorder=3)
    prof2 = smooth_profile_savgol(prof2, window_length=10, polyorder=3)

    if prof1.empty:
        raise ValueError('prof1 became empty after smoothing.')
    if prof2.empty:
        raise ValueError('prof2 became empty after smoothing.')

    common_depths = np.arange(min_depth, max_depth + 1, 1)

    prof1_interp = np.interp(
        common_depths,
        prof1['depth'].values,
        prof1['force'].values
    )
    prof2_interp = np.interp(
        common_depths,
        prof2['depth'].values,
        prof2['force'].values
    )

    formatted_profiles = np.array([prof1_interp, prof2_interp])[..., np.newaxis]

    return formatted_profiles, common_depths


def match_profile(profiles, depths,
                  itakura_max_slope=2,
                  max_iter=30,
                  tol=1e-5,
                  smooth_window_length=10,
                  smooth_polyorder=2):
    '''
    Warps prof2 (target) onto the depth grid of prof1 (reference) via DTW.

    :param profiles: 3D array returned by prep_profs
                     profiles[0] = prof1_force (Reference/Truth)
                     profiles[1] = prof2_force (To be warped)
    :param depths: 1D common depth grid array
    :param itakura_max_slope: Maximum slope for the Itakura parallelogram constraint
    :param max_iter: Kept for API compatibility; not used by pairwise DTW matching
    :param tol: Kept for API compatibility; not used by pairwise DTW matching
    :param smooth_window_length: Savitzky-Golay smoothing window applied after matching
    :param smooth_polyorder: Savitzky-Golay polynomial order applied after matching
    :return: (prof1_ref, prof2_matched)
             prof1_ref: Reference profile on common depth grid, smoothed after matching
             prof2_matched: prof2 warped onto prof1's depth axis, smoothed after matching
    '''

    prof1_ref_force = profiles[0, :, 0]  # Reference (Truth)
    prof2_to_warp_force = profiles[1, :, 0]  # To be warped

    prof1_ref_force_norm = normalize_force(prof1_ref_force)
    prof2_to_warp_force_norm = normalize_force(prof2_to_warp_force)

    # Set constraint window
    #metric_params = {'itakura_max_slope': 1}
    metric_params = {}
    if itakura_max_slope is not None and itakura_max_slope > 0:
        metric_params = {
            'global_constraint': 'itakura',
            'itakura_max_slope': int(itakura_max_slope)
        }



    # Compute optimal alignment path: idx1 -> prof1 (ref), idx2 -> prof2 (warp)
    path, _ = dtw_path_from_metric(
        prof1_ref_force_norm.reshape(-1, 1),
        prof2_to_warp_force_norm.reshape(-1, 1),
        metric='cityblock',
        **metric_params
    )

    # Warp prof2 force values onto prof1's depth axis (idx1)
    matched_f2 = np.zeros(len(depths))
    counts = np.zeros(len(depths))

    for idx1, idx2 in path:
        matched_f2[idx1] += prof2_to_warp_force[idx2]
        counts[idx1] += 1

    # Average force values where multiple indices map to one depth point
    mask = counts > 0
    if not np.all(mask):
        valid_idx = np.where(mask)[0]
        unmapped_idx = np.where(~mask)[0]
        matched_f2[mask] /= counts[mask]
        # Interpolate unmapped points
        matched_f2[unmapped_idx] = np.interp(unmapped_idx, valid_idx, matched_f2[mask])
    else:
        matched_f2 /= counts

    # DataFrame 1: Reference profile (Unwarped)
    prof1_ref = pd.DataFrame({
        'depth': depths,
        'force': prof1_ref_force
    })

    # DataFrame 2: Warped profile (Aligned to prof1)
    prof2_matched = pd.DataFrame({
        'depth': depths,
        'force': matched_f2
    })

    # smooth return profiles
    prof1_ref = smooth_profile_savgol(
        prof1_ref,
        window_length=smooth_window_length,
        polyorder=smooth_polyorder
    )

    prof2_matched = smooth_profile_savgol(
        prof2_matched,
        window_length=smooth_window_length,
        polyorder=smooth_polyorder
    )

    return prof1_ref, prof2_matched

if __name__ == '__main__':
    from matplotlib import pyplot as plt
    site = 'BDG_20260520_TS_1745'

    smp_df = pd.read_csv(f'/Users/colemankane_1/Documents/BSU/penetrometer_analysis_v2/data/consensus/smp/{site}_match_smp.csv')
    ram = pd.read_csv(f'/Users/colemankane_1/Documents/BSU/penetrometer_analysis_v2/data/pen_profiles/ram_files/{site}_sram.csv')

    ram_df = pd.DataFrame({
        'depth': ram['l_cm'] * 10,
        'force': ram['rr_N']
    })

    truth = smp_df
    to_warp = ram_df

    fmt_profs, depths = prep_profs(truth, to_warp)
    trimmed, matched = match_profile(fmt_profs, depths, max_iter=30, tol=1e-5, itakura_max_slope=2)

    fig1, (ax1, ax2, ax3) = plt.subplots(1, 3)

    ax1.step(matched['force'], matched['depth'])
    ax1.set_title('Matched profile')
    ax1.invert_yaxis()


    ax2.step(trimmed['force'], trimmed['depth'], where='post')
    ax2.set_title('Trimmed profile')
    ax2.invert_yaxis()

    ax3.step(to_warp['force'], to_warp['depth'])
    ax3.set_title('original profile')
    ax3.invert_yaxis()

    plt.tight_layout()
    plt.show()


