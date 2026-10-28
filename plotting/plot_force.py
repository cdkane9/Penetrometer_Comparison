'''Plotting penetration force across stratigraphic layers'''

import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression, HuberRegressor

project_dir = Path(__file__).resolve().parent.parent
cache_dir = project_dir / 'data' / 'cache'

ram_smp = pd.read_pickle(cache_dir / 'ram_smp.pkl')
#ram_smp = ram_smp[ram_smp['smp_mean_N'] < 6]
scope_smp = pd.read_pickle(cache_dir / 'smp_scope.pkl')
#scope_smp = scope_smp[scope_smp['smp_mean_N'] < 6]

ram_scope = pd.read_pickle(cache_dir / 'ram_scope.pkl')

print(ram_scope.columns)

axis_labels = {
    'ram_mean_N': 'Ram Resistance [N]',
    'scope_mean_N': 'Scope Force [N]',
    'smp_mean_N': 'SMP Force [N]',
    'grain avg_mm': 'Grain Size [mm]',
    'type': 'Grain Type',
    'density_kgm3': 'Density [kg/m3]',
}

grain_type = {
    'RG': 'EQ',
    'PP': 'NS',
    'DF': 'NS',
    'FC': 'KN',
    'DH': 'KN',
    'MF': 'MF',
    'IF': 'MF',
}

process_markers = {
    'EQ': 'o',
    'NS': '+',
    'KN': 's',
    'MF': r'$\infty$',
}

def reg_line(x, y):
    '''
    Calculate regression line for plotting
    :return:
    '''
    r = x.corr(y)

    x = np.asarray(x)
    y = np.asarray(y)


    valid = ~np.isnan(x) & ~np.isnan(y)

    x = x[valid].reshape(-1, 1)
    y = y[valid]

    domain = np.linspace(x.min(), x.max(), 100)
    model = HuberRegressor(fit_intercept=False)
    model.fit(x, y)

    m = model.coef_[0]
    b = model.intercept_
    return domain, m, b, r

def plot_force(df, pen_x, pen_y, shadeby=None, markerby=None, err_bars=None, title=None):
    '''
    Plot force comparison between instruments
    :param df: comparison dataframe
    :param pen_x: column name, x-axis
    :param pen_y: column name, y-axis
    :param shadeby: column name, which parameter to shade markers
    :param markerby: column name, which parameter to dictate markers
    :return: figure
    '''

    #title = input('Enter plot title: ')
    title = title

    columns = [pen_x, pen_y]
    if markerby is not None:
        columns.append(markerby)

    plot_df = df[columns].dropna().copy()

    x = plot_df[pen_x]
    y = plot_df[pen_y]

    domain, m, b, r = reg_line(x, y)

    fig, ax = plt.subplots()

    if markerby == 'type':
        plot_df['major_grain_type'] = plot_df[markerby].astype(str).str[:2]
        plot_df['process'] = plot_df['major_grain_type'].map(grain_type)

        for process, marker in process_markers.items():
            process_df = plot_df[plot_df['process'] == process]

            if process_df.empty:
                continue

            if process == 'KN':
                ax.scatter(
                    process_df[pen_x],
                    process_df[pen_y],
                    s=35,
                    marker=marker,
                    facecolors='none',
                    edgecolors='black',
                    alpha=0.5,
                    label=process,
                )
            else:
                ax.scatter(
                    process_df[pen_x],
                    process_df[pen_y],
                    s=35,
                    marker=marker,
                    color='black',
                    alpha=0.5,
                    label=process,
                )
    else:
        ax.scatter(x, y, s=15, alpha=1)

    ax.set_xlabel(axis_labels[pen_x])
    ax.set_ylabel(axis_labels[pen_y])

    ax.plot(domain, m * domain + b,
            color='red',
            linewidth=2,
            label=f'y = {m:.2f}x + {b:.2f}, r= {r:.2f}')

    ax.legend()
    ax.set_title(title)
    plt.show()

    return fig, ax




plot_force(ram_smp, 'smp_mean_N', 'ram_mean_N', markerby='type', title='SMP vs. Ram')
plot_force(ram_scope, 'ram_mean_N', 'scope_mean_N', markerby='type', title='Ram vs. Scope')
plot_force(scope_smp, 'smp_mean_N', 'scope_mean_N', markerby='type', title='SMP vs. Scope')
