import pandas as pd
import numpy as np
import os

'''

Read in scope(smp)_cleaning_all.xlsx, which has flags set for instances 
    where a profile has an air gap, ground strike, overload, or should
    not be included in further analysis.  

'''

all_scopes = pd.read_excel('scope_cleaning_all.xlsx')
all_smps = pd.read_excel('smp_cleaning_all.xlsx')

scope_path = '/Users/colemankane_1/Documents/BSU/penetrometer_analysis_v2/data/pen_profiles/Snow_Scope'
smp_path = '/Users/colemankane_1/Documents/BSU/penetrometer_analysis_v2/data/pen_profiles/smp_profiles_exports'


def smp_head(path):
    try:
        prof_raw = pd.read_csv(path, low_memory=False, skiprows=0, usecols=[1, 2])
    except pd.errors.ParserError:
        prof_raw = pd.read_csv(path, low_memory=False)
    return None, prof_raw


def scope_head(path_in):
    '''
    Scope files have inconsistent header lines.
    Still want to manipulate force/depth profile, then resave with header lines
    :param path_in: path to
    :return:
    '''

    header_lines = []

    with open(path_in, 'r') as f:
        for line in f:
            header_lines.append(line)
            if 'depth (mm)' in line:
                break

    data_start_line = len(header_lines)
    df_data = pd.read_csv(path_in, skiprows=data_start_line, header=None, usecols=[0, 1])

    return header_lines, df_data

def write_scope_profile(path_out, header_lines, profile_df):
    '''
    Write header lines to file, then append with depth/force profile
    :param path_out:
    :param header_lines:
    :param profile_df:
    :return:
    '''
    with open(path_out, 'w') as f:
        f.writelines(header_lines)
    profile_df.tocsv(path_out, index=False, mode='a')


def trim_prof(file_path, ground, surface, pen_type):
    '''
    Remove air gap, remove ground strike
    :param file_path: path to profile
    :param ground: depth location of ground
    :param surface: snow surface location
    :return: re-writes scope profile
    '''
    pen_map = {
        'scope': {
            'path': scope_head,
            'func': scope_head,
            'depth_col': 'depth (mm)',
            'force_col': 'hardness (kpa)'
        },
        'smp': {
            'path': smp_path,
            'func': smp_head,
            'depth_col': 'distance',
            'force_col': 'force'
        }
    }

    # read in profile with appropriate function
    header, df = pen_map[pen_type]['func'](file_path)


    # assign appropriate column name
    depth_col = pen_map[pen_type]['depth_col']
    force_col = pen_map[pen_type]['force_col']
    prof = df.copy()
    prof.columns = [depth_col, force_col]

    # remove ground strike
    if ground != '':
        prof = prof[prof[depth_col] < ground]

    # remove air gap
    if surface != '':
        prof = prof[prof[depth_col] >= surface]

        # reset depth so snow surface occurs @ 0mm
        old_surface_value = prof[depth_col].iloc[0]
        prof[depth_col] -= old_surface_value

    if pen_type == 'smp':
        prof.to_csv(file_path)
    else:
        write_scope_profile(file_path, header, prof)




