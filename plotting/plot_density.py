'''Plotting penetration force against density'''
import numpy as np

from plot_force import three_panel_force, axis_labels, reg_line, plot_force
import pandas as pd
from pathlib import Path


project_dir = Path(__file__).resolve().parent.parent
cache_dir = project_dir / 'data' / 'cache'

ram_smp = pd.read_pickle(cache_dir / 'ram_smp.pkl')
scope_smp = pd.read_pickle(cache_dir / 'smp_scope.pkl')
ram_scope = pd.read_pickle(cache_dir / 'ram_scope.pkl')


ram_smp['density_kgm3'] = ram_smp['density_kgm3'].replace(['#DIV/0!', '#VALUE!'], np.nan).astype(float)
ram_scope['density_kgm3'] = ram_scope['density_kgm3'].replace(['#DIV/0!', '#VALUE!'], np.nan).astype(float)
scope_smp['density_kgm3'] = scope_smp['density_kgm3'].replace(['#DIV/0!', '#VALUE!'], np.nan).astype(float)



if __name__ == '__main__':
    three_panel_force(ram_smp, 'smp_mean_N', 'density_kgm3', model='log')
    three_panel_force(ram_scope, 'ram_mean_N', 'density_kgm3', model='log')
    three_panel_force(ram_scope, 'scope_mean_N', 'density_kgm3', model='log')
    pass