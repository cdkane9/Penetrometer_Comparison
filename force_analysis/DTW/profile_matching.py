'''
Various functions required to match two profiles together
'''

import pandas as pd
import numpy as np
from tslearn.barycenters import dtw_barycenter_averaging
from tslearn.metrics import dtw_path

def prep_profs(prof1, prof2):
    '''
    Resamples two profiles with a common depth grid
    :param prof1: df with columns ['depth', 'force'] --> considered truth
    :param prof2: df with columns ['depth', 'force'] --> profile to be stretched
            Both prof1 and prof2 should be in units of mm
    :return: Interpolated force profiles, common depth array
    '''

    # find depth of the shallowest profile
    max_depth = min(prof1['depth'].max(), prof2['depth'].max()).astype(int)

    # create common depth grid to map profiles to
    common_depths = np.arange(0, max_depth + 1, 1)

    prof1_interp = np.interp(common_depths, prof1['depth'].values,
                             prof1['force'].values)
    prof2_interp = np.interp(common_depths, prof2['depth'].values,
                             prof2['force'].values)
    formatted_profiles = np.array([prof1_interp, prof2_interp])[..., np.newaxis]

    return formatted_profiles, common_depths

def match_profile(profiles, depths, max_iter, radius, tol):
    '''
    Computes matched profile
    :param profiles:
    :param depths:
    :return:
    '''

    metric_params = {}

    consensus_force = dtw_barycenter_averaging(
        profiles,
        max_iter=max_iter,
        tol=tol,
        metric_params=metric_params
    ).ravel()

    matched_prof = pd.DataFrame({
        'depth': depths,
        'force': consensus_force
    })



if __name__ == '__main__':
    from matplotlib import pyplot as plt
    smp_df = pd.read_csv('/Users/colemankane_1/Documents/BSU/penetrometer_analysis_v2/data/consensus/smp/FRE_20250109_match_smp.csv')
    ram = pd.read_csv('/Users/colemankane_1/Documents/BSU/penetrometer_analysis_v2/data/pen_profiles/ram_files/FRE_20250109_sram.csv')

    ram_df = pd.DataFrame({
        'depth': ram['l_cm'],
        'force': ram['rr_N']
    })

    fig1, (ax1, ax2) = plt.subplots(1, 2)

    ax1.step(ram_df['force'], ram_df['depth'] * 10)
    ax1.invert_yaxis()


    ax2.plot(smp_df['force'], smp_df['depth'])
    ax2.invert_yaxis()
    plt.show()

