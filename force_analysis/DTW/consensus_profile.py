'''
Generates an SMP and Scope consensus profile for each pit.
'''


import pandas as pd
import numpy as np
from tslearn.barycenters import dtw_barycenter_averaging
from tslearn.metrics import dtw_path
import os
import ast

all_pen_paths = pd.read_csv('../../data/all_profiles_thinned.csv')

def parse_paths(val):
    if pd.isna(val) or not isinstance(val, str) or val.strip() in ['', 'nan', '[]']:
        return []
    try:
        res = ast.literal_eval(val)
        if isinstance(res, list):
            valid_paths = []
            for p in res:
                path_str = str(p).strip()
                # 1. Skip dummy string values
                if not path_str or path_str.lower() in ['nan', 'none']:
                    continue
                # 2. Check if the file actually exists on disk
                if os.path.exists(path_str):
                    valid_paths.append(path_str)
                else:
                    print(f"⚠File not found on disk: {path_str}")

            return valid_paths
        return []
    except (ValueError, SyntaxError):
        return []


def smp_head(path_in):
    '''
    Reads in raw foce/distance SMP profile
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

def scope_head(df):
    idx_init = df[df.iloc[:, 0] == 'depth (mm)'].index[0]
    scope_prof = df.iloc[idx_init + 1:].reset_index(drop=True).astype(float)
    scope_prof.columns = ['depth', 'force']
    # convert from kPa to N
    scope_prof['force'] *= 1000 * 0.0000554
    return scope_prof