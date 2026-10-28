import pandas as pd
import numpy as np
import os
from pathlib import Path

'''

Read in scope(smp)_cleaning_all.xlsx, which has flags set for instances 
    where a profile has an air gap, ground strike, overload, or should
    not be included in further analysis.  

'''


# get paths to directories for respective instruments
script_dir = Path(__file__).resolve().parent.parent
smp_path = os.path.join(script_dir,'data', 'pen_profiles', 'smp_profiles_exports')
scope_path = os.path.join(script_dir, 'data', 'pen_profiles', 'Snow_Scope')


all_scopes = pd.read_excel(script_dir / 'data' / 'scope_cleaning_all.xlsx')
all_smps = pd.read_excel(script_dir / 'data' / 'smp_cleaning_all.xlsx')



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
    df_data = pd.read_csv(path_in, skiprows=data_start_line +1, header=None)

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
    profile_df.to_csv(path_out, index=False, mode='a', header=False)


def trim_prof(file_path, ground, surface, pen_type, testing=False):
    '''
    Remove air gap, remove ground strike
    :param file_path: path to profile
    :param ground: depth location of ground
    :param surface: snow surface location
    :return: re-writes scope profile
    '''
    if testing:
        export_path = '/Users/colemankane_1/Desktop/prof_test_cleaning'
    else:
        export_path = os.path.dirname(file_path)

    out_file = os.path.join(export_path, os.path.basename(file_path))

    print('Trimming profile: ', os.path.basename(file_path))

    pen_map = {
        'scope': {
            'path': scope_path,
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
    prof.columns = [depth_col, force_col] + list(prof.columns[2:])

    # remove ground strike
    if ground != 0:
        prof = prof[prof[depth_col] < ground]

    # remove air gap
    if surface != 0:
        prof = prof[prof[depth_col] >= surface]

        # reset depth so snow surface occurs @ 0mm
        old_surface_value = prof[depth_col].iloc[0]
        prof[depth_col] -= old_surface_value

    if pen_type == 'smp':

        prof.to_csv(out_file, index=False)
    else:
        write_scope_profile(out_file, header, prof)


def process_spreadsheets(df, pen_path: str, pen_type):
    '''
    Filters out bad profiles, renames columns to match trim_prof, then passes to trim_prof
    :param df: either smp or scope cleaning.xlsx
    :return:
    '''
    # filter out bad profiles
    valid_profiles = df[(df['toss'] == 0) & (df['overload'] == 0)].copy()


    # rename columns
    valid_profiles['file_path'] = valid_profiles[1].apply(lambda fname: os.path.join(pen_path, fname))
    valid_profiles['surface'] = valid_profiles['air gap']
    valid_profiles['pen_type'] = pen_type
    valid_profiles['testing'] = False # change to True if writing to another directory is desired

    # trim to relevant columns
    args_df = valid_profiles[['file_path', 'ground', 'surface', 'pen_type', 'testing']]

    # pass to trim_prof
    for record in args_df.to_dict('records'):
        trim_prof(**record)

# pass the cleaning spreadsheets onto the trimming functions, write
process_spreadsheets(all_smps, smp_path, 'smp')
process_spreadsheets(all_scopes, scope_path, 'scope')





# The following was a bit of code to test the trimming function
#   by writing to a dummy directory on my desktop.
'''
if __name__ == '__main__':
    smp_profiles = os.path.join(script_dir, 'data', 'pen_profiles', 'smp_profiles_exports')
    scope_profiles = os.path.join(script_dir, 'data', 'pen_profiles', 'Snow_Scope')

    smp_test_path = os.path.join(smp_profiles, 'S19M1097.PNT_samples.csv')
    scope_test_path = os.path.join(scope_profiles, '2025-01-16_1128_Profile44_SN00340.csv')

    # test with a few sample profiles
    _, smp_test = smp_head(smp_test_path)
    smp_ag = 66 # air gap
    smp_g = 0 # ground

    trim_prof(smp_test_path, smp_g, smp_ag, 'smp', testing=True)
    _, trim_smp = smp_head('/Users/colemankane_1/Desktop/prof_test_cleaning/S19M1097.PNT_samples.csv')

    # quick plot to compare original and trimmed
    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.plot(smp_test['force'], smp_test['distance'])
    ax1.invert_yaxis()
    ax1.set_title('OG')


    ax2.plot(trim_smp['force'], trim_smp['distance'])
    ax2.invert_yaxis()
    ax2.set_title('Trimmed')
    

    _, scope_test = scope_head(scope_test_path)
    scope_g = 1543 # ground
    scope_ag = 0

    trim_prof(scope_test_path, scope_g, scope_ag, 'scope', testing=True)
    _, trim_scope = scope_head(scope_test_path)
    print(scope_test.tail)

'''

