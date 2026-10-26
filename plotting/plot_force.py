'''Plotting penetration force across stratigraphic layers'''

import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

project_dir = Path(__file__).resolve().parent.parent
cache_dir = project_dir / 'data' / 'cache'

ram_smp = pd.read_pickle(cache_dir / 'ram_smp.pkl')
scope_smp = pd.read_pickle(cache_dir / 'smp_scope.pkl')
print(scope_smp.columns)
ram_scope = pd.read_pickle(cache_dir / 'ram_scope.pkl')

axis_labels = {
    'ram_mean_N': 'Ram Resistance [N]',
    'scope_mean_N': 'Scope Force [N]',
    'smp_mean_N': 'SMP Force [N]',
    'grain avg_mm': 'Grain Size [mm]',
    'type': 'Grain Type',
}

def plot_force(df, pen_x, pen_y, shadeby=None, markerby=None, err_bars=None):
    '''
    Plot force comparison between instruments
    :param df: comparison dataframe
    :param pen_x: column name, x-axis
    :param pen_y: column name, y-axis
    :param shadeby: column name, which parameter to shade markers
    :param markerby: column name, which parameter to dictcate markers
    :return: figure
    '''

    #title = input('Enter plot title: ')
    title = ''

    x = df[pen_x]
    y = df[pen_y]

    fig, ax = plt.subplots()
    ax.scatter(x, y, s=15, alpha=1)
    ax.set_xlabel(axis_labels[pen_x])
    ax.set_ylabel(axis_labels[pen_y])
    ax.set_title(title)
    plt.show()


    pass

plot_force(ram_smp, 'smp_mean_N', 'ram_mean_N')
plot_force(ram_scope, 'ram_mean_N', 'scope_mean_N')
plot_force(scope_smp, 'smp_mean_N', 'scope_mean_N')
