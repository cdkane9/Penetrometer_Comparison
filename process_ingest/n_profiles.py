import pandas as pd
import os
from pathlib import Path
import re



def find_date(string:str):
    pattern = r'((?:19|20)\d{2})-?(0[1-9]|1[0-2])-?(0[1-9]|[12]\d|3[01])'
    match = re.search(pattern, string)

    if match:
        year = match.group(1)
        # Check if the match came from the hyphenated group or compact group
        month = match.group(2) if match.group(2) else match.group(4)
        day = match.group(3) if match.group(3) else match.group(5)

        # zfill(2) ensures single-digit months/days get a leading zero (e.g., '3' -> '03')

        return f"{year}{month.zfill(2)}{day.zfill(2)}"
    else:
        print(string)

    return None

def n_in_wateryear(data_list):



    wy24_start = pd.to_datetime('2023-10-01')
    wy25_start = pd.to_datetime('2024-10-01')
    wy26_start = pd.to_datetime('2025-10-01')
    wy27_start = pd.to_datetime('2026-10-01')


    data_24 = [i for i in data_list if wy24_start <= i < wy25_start]
    data_25 = [i for i in data_list if wy25_start <= i < wy26_start]
    data_26 = [i for i in data_list if wy26_start <= i < wy27_start]

    return {
        'wy24': data_24,
        'wy25': data_25,
        'wy26': data_26,
    }

def print_wy_totals(wy_dict):
    n_24 = len(wy_dict['wy24'])
    n_25 = len(wy_dict['wy25'])
    n_26 = len(wy_dict['wy26'])

    print('2024:\t', n_24)
    print('2025:\t', n_25)
    print('2026:\t', n_26)

# read in all the stratigraphy files
script_dir = Path(__file__).resolve().parent
pit_dir = script_dir.parent / 'data' / 'pit_matrix'
pit_list = [i for i in os.listdir(pit_dir) if i.endswith('_strat.csv')]
# extract dates
pit_dates = [pd.to_datetime(find_date(i)) for i in pit_list]
# sort into water year
pit_sorted = n_in_wateryear(pit_dates)

# read in ram files
ram_dir = script_dir.parent / 'data' / 'pen_profiles' / 'ram_files'
ram_list = [i for i in os.listdir(ram_dir) if i.endswith('_sram.csv')]
ram_dates = [pd.to_datetime(find_date(i)) for i in ram_list]
ram_sorted = n_in_wateryear(ram_dates)

# read in sheets containing all relevant scope and SMP profiles
scope_sheet = pd.read_excel('scope_cleaning_all.xlsx')
smp_sheet = pd.read_excel('smp_cleaning_all.xlsx')

# extract dates
smp_pits = list(smp_sheet[0])
smp_dates = [pd.to_datetime(find_date(i)) for i in smp_pits]
#sort into water year
smp_sorted = n_in_wateryear(smp_dates)

# extract dates
scope_pits = list(scope_sheet[0])
scope_dates = [pd.to_datetime(find_date(i)) for i in scope_pits]

# determine n_profs for multiple diurnal time series
am_ts_start = pd.to_datetime('2026-05-14')
am_ts_end = pd.to_datetime('2026-05-15')

bdg_ts_start = pd.to_datetime('2026-05-19')
bdg_ts_end = pd.to_datetime('2026-05-22')

am_scopes = [i for i in scope_dates if (i <= am_ts_end) and (i >= am_ts_start)]
am_rams = [i for i in ram_dates if (i <= am_ts_end) and (i >= am_ts_start)]

bdg_scopes = [i for i in scope_dates if (i <= bdg_ts_end) and (i >= bdg_ts_start)]
bdg_rams = [i for i in ram_dates if (i <= bdg_ts_end) and (i >= bdg_ts_start)]
bdg_smps = [i for i in smp_dates if (i <= bdg_ts_end) and (i >= bdg_ts_start)]
print(len(bdg_smps))
print(len(bdg_scopes))
print(len(bdg_rams))

# sort into water year
scope_sorted = n_in_wateryear(scope_dates)

'''
print('PITS')
print(print_wy_totals(pit_sorted))
print()
print('*'*40)
print('SCOPE')
print(print_wy_totals(scope_sorted))
print()
print('*'*40)
print('SMP')
print(print_wy_totals(smp_sorted))
print()
print('*'*40)
print('RAM')
print(print_wy_totals(ram_sorted))
'''

#########################################################################################################


