'''Plotting penetration force across stratigraphic layers'''

import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression, HuberRegressor
import mplcursors

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
    'ram_max_N': 'Max Ram Resistance [N]',
    'scope_max_N': 'Max Scope Force [N]'
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

def three_panel_force(df, pen_x, pen_y):
    '''
    plot four panels: PP/DF, equilibrium, kinetic, and melt forms
    :param df:
    :param pen_x:
    :param pen_y:
    :return:
    '''

    df['major_grain_type'] = df['type'].astype(str).str[:2]
    df['process'] = df['major_grain_type'].map(grain_type)

    ns_df = df[df['major_grain_type'].isin(['PP', 'DF'])]
    eq_df = df[df['major_grain_type'] == 'RG']
    kn_df = df[df['major_grain_type'].isin(['FC', 'DH'])]
    mf_df = df[df['major_grain_type'] == 'MF']



    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(6, 6))
    ax1, ax2, ax3, ax4 = axes.flat
    # added functionality for determining pit_id of certain points
    '''
    ax1.set_title('PP/DF')
    ax1.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax1.set_xlabel(axis_labels[pen_x])
    ax1.set_ylabel(axis_labels[pen_y])

    # 1. Capture the PathCollection returned by scatter
    sc1 = ax1.scatter(ns_df[pen_x], ns_df[pen_y], s=15, alpha=1, label='NS')

    # 2. Attach mplcursors hover tooltips to ax1's scatter plot
    cursor1 = mplcursors.cursor(sc1, hover=True)

    @cursor1.connect("add")
    def on_add_ax1(sel):
        # Extract pit_id matching the hovered scatter point's index
        pit_id = ns_df['pit_id'].iloc[sel.index]
        sel.annotation.set_text(f"pit_id: {pit_id}")
        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9, edgecolor="gray")'''

    ax1.set_title('PP/DF')
    ax1_domain, ax1_m, ax1_b, ax1_r = reg_line(ns_df[pen_x], ns_df[pen_y])
    ax1.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax1.set_xlabel(axis_labels[pen_x])
    ax1.set_ylabel(axis_labels[pen_y])
    ax1.scatter(ns_df[pen_x], ns_df[pen_y], s=15, alpha=1, label='NS')
    ax1.plot(ax1_domain, ax1_m * ax1_domain + ax1_b,
             color='red',
             linewidth=2,
             label=f'y = {ax1_m:.4f}x + {ax1_b:.4f}, r= {ax1_r:.2f}')
    ax1.legend()

    ax2.set_title('RG')
    ax2_domain, ax2_m, ax2_b, ax2_r = reg_line(eq_df[pen_x], eq_df[pen_y])
    ax2.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax2.set_xlabel(axis_labels[pen_x])
    ax2.set_ylabel(axis_labels[pen_y])
    ax2.scatter(eq_df[pen_x], eq_df[pen_y], s=15, alpha=1, label='EQ')
    ax2.plot(ax2_domain, ax2_m * ax2_domain + ax2_b,
             color='red',
             linewidth=2,
             label=f'y = {ax2_m:.4f}x + {ax2_b:.4f}, r= {ax2_r:.2f}')
    ax2.legend()

    ax3.set_title('FC/DH/SH')
    ax3_domain, ax3_m, ax3_b, ax3_r = reg_line(kn_df[pen_x], kn_df[pen_y])
    ax3.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax3.set_xlabel(axis_labels[pen_x])
    ax3.set_ylabel(axis_labels[pen_y])
    ax3.scatter(kn_df[pen_x], kn_df[pen_y], s=15, alpha=1, label='KN')
    ax3.plot(ax3_domain, ax3_m * ax3_domain + ax3_b,
             color='red',
             linewidth=2,
             label=f'y = {ax3_m:.4f}x + {ax3_b:.4f}, r= {ax3_r:.2f}')
    ax3.legend()


    ax4.set_title('MF')
    ax4_domain, ax4_m, ax4_b, ax4_r = reg_line(mf_df[pen_x], mf_df[pen_y])
    ax4.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax4.set_xlabel(axis_labels[pen_x])
    ax4.set_ylabel(axis_labels[pen_y])
    ax4.scatter(mf_df[pen_x], mf_df[pen_y], s=15, alpha=1, label='MF')
    ax4.plot(ax4_domain, ax4_m * ax4_domain + ax4_b,
             color='red',
             linewidth=2,
             label=f'y = {ax4_m:.4f}x + {ax4_b:.4f}, r= {ax4_r:.2f}')
    ax4.legend()


    fig.suptitle(f'{pen_x} vs. {pen_y}')
    plt.tight_layout()
    plt.show()

    return


three_panel_force(scope_smp, 'smp_mean_N', 'scope_mean_N')
three_panel_force(ram_smp, 'smp_mean_N', 'ram_mean_N')
three_panel_force(ram_scope, 'ram_mean_N', 'scope_mean_N')

#plot_force(ram_smp, 'smp_mean_N', 'ram_mean_N', markerby='type', title='SMP vs. Ram')
#plot_force(ram_scope, 'ram_mean_N', 'scope_mean_N', markerby='type', title='Ram vs. Scope')
#plot_force(scope_smp, 'smp_mean_N', 'scope_mean_N', markerby='type', title='SMP vs. Scope')
