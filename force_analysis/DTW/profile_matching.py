'''
Various functions required to match two profiles together
'''

import pandas as pd
import numpy as np
from tslearn.barycenters import dtw_barycenter_averaging
from tslearn.metrics import dtw_path
from scipy.signal import savgol_filter


def smooth_profile_savgol(df, window_length=11, polyorder=2):
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
def prep_profs(prof1, prof2):
    '''
    Resamples two profiles with a common depth grid
    :param prof1: df with columns ['depth', 'force'] --> considered truth
    :param prof2: df with columns ['depth', 'force'] --> profile to be stretched
            Both prof1 and prof2 should be in units of mm
    :return: Interpolated force profiles, common depth array
        formatted_profiles - returns prof1, prof2
    '''

    # find depth of the shallowest profile
    max_depth = min(prof1['depth'].max(), prof2['depth'].max()).astype(int)

    prof1 = smooth_profile_savgol(prof1[prof1['depth'] < max_depth], window_length=10, polyorder=3)
    prof2 = smooth_profile_savgol(prof2[prof2['depth'] < max_depth], window_length=10, polyorder=3)

    #prof1 = prof1[prof1['depth'] < max_depth]
    #prof2 = prof2[prof2['depth'] < max_depth]

    # create common depth grid to map profiles to
    common_depths = np.arange(0, max_depth + 1, 1)

    prof1_interp = np.interp(common_depths, prof1['depth'].values,
                             prof1['force'].values)
    prof2_interp = np.interp(common_depths, prof2['depth'].values,
                             prof2['force'].values)
    formatted_profiles = np.array([prof1_interp, prof2_interp])[..., np.newaxis]

    return formatted_profiles, common_depths


def match_profile(profiles, depths, radius=15, max_iter=30, tol=1e-5):
    '''
    Warps prof2 (target) onto the depth grid of prof1 (reference) via DTW.

    :param profiles: 3D array returned by prep_profs
                     profiles[0] = prof1_force (Reference/Truth)
                     profiles[1] = prof2_force (To be warped)
    :param depths: 1D common depth grid array
    :param radius: Sakoe-Chiba constraint radius (mm)
    :return: (prof1_ref, prof2_matched)
             prof1_ref: Unaltered reference profile on common depth grid
             prof2_matched: prof2 warped onto prof1's depth axis
    '''
    prof1_ref_force = profiles[0, :, 0]  # Reference (Truth)
    prof2_to_warp_force = profiles[1, :, 0]  # To be warped

    # Set constraint window
    metric_params = {}
    if radius is not None and radius > 0:
        metric_params['sakoe_chiba_radius'] = int(radius)

    # Compute optimal alignment path: idx1 -> prof1 (ref), idx2 -> prof2 (warp)
    path, _ = dtw_path(
        prof1_ref_force.reshape(-1, 1),
        prof2_to_warp_force.reshape(-1, 1),
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
    trimmed, matched = match_profile(fmt_profs, depths, max_iter=30, tol=1e-5, radius=20)

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


