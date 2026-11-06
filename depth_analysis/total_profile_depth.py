'''
Plots manual vs digital profile depth from Snow Scope, and depth error as function of depth
'''

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
from scipy.stats import linregress

project_dir = Path(__file__).resolve().parent.parent
scope_matrix_path = project_dir / 'data' / 'pit_matrix'

scope_mats = [i for i in os.listdir(scope_matrix_path)
              if i.endswith('_scope.csv')]

def rmse(y_true, y_pred):
    return np.sqrt(np.mean((y_true - y_pred) ** 2))

# initialize dictionary to store manual and digital profile depths
man_dig = {
    'd_m': [],
    'd_d': [],
    'date':[],
}

def get_WY(filename: str) -> str:
    '''
    Pulls out date from filename and returns 2-digit water year
    '''
    match = re.search(r'20\d{6}', filename)
    if not match:
        raise ValueError(f"No valid date found in filename: {filename}")

    date_str = match.group(0)
    year = int(date_str[:4])
    month = int(date_str[4:6])

    # If month is October, November, or December, it belongs to the next Water Year
    water_year = year + 1 if month >= 10 else year

    # Return 2-digit format (e.g., "26")
    return str(water_year)[-2:]


def percent_diff(row):
    return (row['d_d'] - row['d_m']) / row['d_m'] * 100

def add_reg_line_to_plot(df, col_x, col_y, axis, RMSE=False):
    x = df[col_x]
    y = df[col_y]

    domain = np.linspace(0, x.max(), 100)

    m, b, r_val, p_val, std_err = linregress(x, y)
    y_pred = m * x + b
    if RMSE:
        rmse_val = rmse(y_pred, y)
        axis.plot(domain, m*domain + b, color='black', linestyle='-', linewidth=2,
                label=f'y = {m:.2f}x + {b:.2f}, r = {r_val:.2f},\n RMSE = {rmse_val:.2f}')
    else:

        axis.plot(domain, m * domain + b, color='black', linestyle='-', linewidth=2,
                  label=f'y = {m:.2f}x + {b:.2f}, r = {r_val:.2f}')


    return axis



# pull out manual and digital depths from scope matrices
for matrix in scope_mats:
    df = pd.read_csv(os.path.join(scope_matrix_path, matrix))
    water_year = get_WY(matrix)

    depths = df[['Depth_m', 'Depth_d']].dropna()

    man_dig['d_m'].extend(depths['Depth_m'].to_list())
    man_dig['d_d'].extend(depths['Depth_d'].to_list())
    man_dig['date'].extend([water_year] * len(depths))


# convert to dataframe
depth_df = pd.DataFrame(man_dig)

# calculate errors
depth_df['error'] = depth_df['d_m'] - depth_df['d_d']
depth_df['percent_diff'] = depth_df.apply(percent_diff, axis=1)
depth_df['over'] = depth_df['d_d'] > depth_df['d_m']
depth_df['equal'] = depth_df['d_d'] == depth_df['d_m']


fig1, ax = plt.subplots(figsize=(5, 5))
ax.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
ax.scatter(depth_df['d_d'].iloc[depth_df['over'] ==1],
           depth_df['d_m'].iloc[depth_df['over'] ==1],
           alpha=0.7,
           marker='x',
           edgecolor='black',
           color='#D9381E',
           label='Overestimated')
ax.scatter(depth_df['d_d'].iloc[depth_df['over'] ==0],
           depth_df['d_m'].iloc[depth_df['over'] ==0],
           alpha=0.6,
           marker='o',
           color='#1F618D',
           label='Underestimated')
#ax.scatter(depth_df['d_d'].iloc[depth_df['equal'] ==1],
#           depth_df['d_m'].iloc[depth_df['equal'] ==1],
#           alpha=0.6,
#           marker='^',
#           color='#333333',
#           label='Exact')
add_reg_line_to_plot(depth_df, 'd_d', 'd_m', ax)
ax.set_xlabel('Digital Depth [cm]')
ax.set_ylabel('Manual Depth [cm]')
ax.set_title('Scope Digital vs. Manual Depth')

fig1_domain = ax.get_xlim()
# add 1-1 line
ax.plot(fig1_domain, fig1_domain,
        color='black',
        linestyle='--',
        label='1:1',
        alpha=0.5)
ax.legend()


fig2, ax2 = plt.subplots(figsize=(6, 5))
colors = plt.cm.tab20(np.linspace(0, 1, depth_df['date'].nunique()))


ax2.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
for color, (date, date_df) in zip(colors, depth_df.groupby('date')):
    ax2.scatter(
        date_df['d_d'],
        date_df['error'],
        alpha=0.75,
        marker='o',
        color=color,
        edgecolor='black',
        linewidth=0.3,
        label=date,
        zorder=3 if date == '24' else 2
    )
add_reg_line_to_plot(depth_df, 'd_m', 'error', ax2)
ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.7)
ax2.set_xlabel('Manual Depth [cm]')
ax2.set_ylabel(r'Manual $-$ Digital [cm]')
ax2.set_title('Scope Manual Depth vs. Error')
ax2.set_xlim(fig1_domain)
plt.legend()
fig2.tight_layout()



fig3, ax3 = plt.subplots(figsize=(3.2, 4.2))

percent_diff = depth_df['percent_diff'].dropna()

box = ax3.boxplot(
    percent_diff,
    vert=True,
    notch=False,
    patch_artist=True,
    widths=0.45,
    boxprops={
        'facecolor': '#4C78A8',
        'edgecolor': 'black',
        'linewidth': 1.2
    },
    medianprops={
        'color': '#F58518',
        'linewidth': 2
    },
    whiskerprops={
        'color': 'black',
        'linewidth': 1.2
    },
    capprops={
        'color': 'black',
        'linewidth': 1.2
    },
    flierprops={
        'marker': 'o',
        'markerfacecolor': 'white',
        'markeredgecolor': 'black',
        'markersize': 4,
        'alpha': 0.45
    }
)

ax3.axhline(
    0,
    color='gray',
    linestyle='--',
    linewidth=1,
    alpha=0.8
)

ax3.set_ylabel('Percent Error [%]')
ax3.set_xticks([])
ax3.set_title('')

ax3.grid(
    True,
    axis='y',
    linestyle='--',
    linewidth=0.5,
    color='gray',
    alpha=0.4
)

ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()
