import openpyxl
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use('TkAgg')

from matplotlib import pyplot as plt
from matplotlib.widgets import CheckButtons, Button, TextBox
from pathlib import Path




'''
plot profiles in 'scope(smp)_cleaning_YEAR_filled.xlsx' and identify if there's an 
air gap, ground strike, overload, of if profile needs to be tossed

'''

script_dir = Path(__file__).resolve().parent.parent




def smp_head(path_in):
    try:
        prof_raw = pd.read_csv(path_in, low_memory=False, skiprows=0, usecols=[1, 2])
        prof_raw.columns = ['depth', 'force']
    except pd.errors.ParserError:
        prof_raw = pd.read_csv(path_in, low_memory=False)
        prof_raw.columns = ['depth', 'force']
    return prof_raw


def scope_head(path_in):

    df = pd.read_csv(path_in, skiprows=1, usecols=[0, 1])
    idx_init = df[df.iloc[:, 0] == 'depth (mm)'].index[0]
    scope_prof = df.iloc[idx_init + 1:].reset_index(drop=True).astype(float)
    scope_prof.columns = ['depth', 'force']
    # convert from kPa to N
    scope_prof['force'] *= 1000 * 0.0000554
    return scope_prof

pen_type = 'smp'#scope or smp
pen_path = 'smp_profiles_exports' #Snow_Scope or smp_profiles_exports
pen_func = smp_head # scope_head or #smp_head

#excel_path = f'{pen_type}_cleaning_25_filled.xlsx'
excel_path = script_dir / 'data' / f'{pen_type}_cleaning_all.xlsx'
caca = pd.read_excel(excel_path)
flag_cols = ['viewed', 'air gap', 'toss', 'ground', 'overload']

for col in flag_cols:
    if col in caca.columns:
        caca[col] = caca[col].fillna(0.0).astype(float)

unviewed_indices = caca[caca['viewed'] == 0].index

plt.ioff()
plt.close('all')

stop_loop = False
processed_groups = set()
previous_fig = None

profile_flag_cols = [col for col in flag_cols if col != 'viewed']


def enlarge_checkbuttons(check, label_size=12, box_scale=1.8, line_width=2.0):
    """Make CheckButtons labels, boxes, and check marks easier to see."""
    for label in check.labels:
        label.set_fontsize(label_size)

    if hasattr(check, 'rectangles'):
        for rect in check.rectangles:
            rect.set_width(rect.get_width() * box_scale)
            rect.set_height(rect.get_height() * box_scale)

    if hasattr(check, 'lines'):
        for line_pair in check.lines:
            for line in line_pair:
                line.set_linewidth(line_width)


for ix in unviewed_indices:
    print(ix)
    row = caca.loc[ix]
    pit_raw = row.iloc[0]

    if pit_raw in processed_groups:
        continue

    processed_groups.add(pit_raw)

    group_indices = caca[
        (caca.iloc[:, 0] == pit_raw) & (caca['viewed'] == 0)
    ].index.tolist()

    if len(group_indices) == 0:
        continue

    pit_id = str(pit_raw).replace('_scope.csv', '').replace('_smp.csv', '')

    n_profiles = len(group_indices)
    fig_width = max(14, 3.0 * n_profiles)

    if previous_fig is not None and plt.fignum_exists(previous_fig.number):
        plt.close(previous_fig)

    fig = plt.figure(figsize=[fig_width, 9.5])
    previous_fig = fig

    fig.suptitle(pit_id, fontsize=18, fontweight='bold')

    gs = fig.add_gridspec(
        4,
        n_profiles,
        height_ratios=[0.45, 5.0, 2.3, 0.45],
        hspace=0.35,
        wspace=0.35,
        top=0.90,
        bottom=0.06,
        left=0.06,
        right=0.98,
    )

    widget_refs = []
    text_boxes = {}
    shared_y_ax = None

    # One group-level "viewed" checkbox.
    ax_group_check = fig.add_subplot(gs[0, :])
    group_viewed_initial = all(
        bool(caca.at[row_ix, 'viewed']) if pd.notna(caca.at[row_ix, 'viewed']) else False
        for row_ix in group_indices
    )

    group_viewed_check = CheckButtons(
        ax_group_check,
        ['viewed'],
        [group_viewed_initial],
    )
    enlarge_checkbuttons(group_viewed_check, label_size=14, box_scale=2.0, line_width=2.2)

    def on_group_viewed_toggle(label):
        current_vals = [
            bool(caca.at[row_ix, 'viewed']) if pd.notna(caca.at[row_ix, 'viewed']) else False
            for row_ix in group_indices
        ]
        new_val = 0 if all(current_vals) else 1

        for row_ix in group_indices:
            caca.at[row_ix, 'viewed'] = new_val

    group_viewed_check.on_clicked(on_group_viewed_toggle)
    widget_refs.append(group_viewed_check)

    def make_toggle_callback(row_ix):
        def on_toggle(label):
            current_val = caca.at[row_ix, label]
            caca.at[row_ix, label] = 0 if current_val == 1 else 1

        return on_toggle

    for profile_num, row_ix in enumerate(group_indices):
        row = caca.loc[row_ix]

        full_profile_id = row.iloc[1]
        profile_id = Path(str(full_profile_id)).stem

        profile_path = script_dir / 'data' / 'pen_profiles' / pen_path / str(full_profile_id)
        profile = pen_func(profile_path)

        if shared_y_ax is None:
            ax_plot = fig.add_subplot(gs[1, profile_num])
            shared_y_ax = ax_plot
        else:
            ax_plot = fig.add_subplot(gs[1, profile_num], sharey=shared_y_ax)
            ax_plot.tick_params(labelleft=False)

        max_force = profile['force'].max()

        ax_plot.plot(profile['force'], profile['depth'], linewidth=1)
        ax_plot.set_title(profile_id, fontsize=10)
        ax_plot.set_xlabel('Force')
        ax_plot.invert_yaxis()
        ax_plot.axvline(x=0, color='black', linestyle='dashed')
        ax_plot.set_xlim(-5, max_force + 2)

        if profile_num == 0:
            ax_plot.set_ylabel('Depth')
        else:
            ax_plot.set_ylabel('')

        controls_gs = gs[2, profile_num].subgridspec(
            3,
            1,
            height_ratios=[2.0, 0.45, 0.45],
            hspace=0.32,
        )

        ax_check = fig.add_subplot(controls_gs[0, 0])
        initial_states = [
            bool(caca.at[row_ix, col]) if pd.notna(caca.at[row_ix, col]) else False
            for col in profile_flag_cols
        ]

        check = CheckButtons(ax_check, profile_flag_cols, initial_states)
        enlarge_checkbuttons(check, label_size=12, box_scale=1.8, line_width=2.0)
        check.on_clicked(make_toggle_callback(row_ix))

        air_val = caca.at[row_ix, 'air gap']
        init_air_val = str(air_val) if (pd.notna(air_val) and air_val != 0) else ''
        ax_tb_air = fig.add_subplot(controls_gs[1, 0])
        tb_air = TextBox(ax_tb_air, 'Air Gap: ', initial=init_air_val)

        ground_val = caca.at[row_ix, 'ground']
        init_ground_val = str(ground_val) if (pd.notna(ground_val) and ground_val != 0) else ''
        ax_tb_ground = fig.add_subplot(controls_gs[2, 0])
        tb_ground = TextBox(ax_tb_ground, 'Ground: ', initial=init_ground_val)

        text_boxes[row_ix] = {
            'air gap': tb_air,
            'ground': tb_ground,
        }

        widget_refs.extend([check, tb_air, tb_ground])

    def save_inputs():
        for row_ix, boxes in text_boxes.items():
            air_val = boxes['air gap'].text.strip()
            if air_val != '':
                caca.at[row_ix, 'air gap'] = float(air_val)
            else:
                caca.at[row_ix, 'air gap'] = 0

            ground_val = boxes['ground'].text.strip()
            if ground_val != '':
                caca.at[row_ix, 'ground'] = float(ground_val)
            else:
                caca.at[row_ix, 'ground'] = 0

    button_gs = gs[3, :].subgridspec(1, 4, wspace=0.35)

    ax_next = fig.add_subplot(button_gs[0, 1])
    btn_next = Button(
        ax_next,
        'Next Group',
        color='lightgreen',
        hovercolor='limegreen',
    )

    def on_next(event):
        save_inputs()
        plt.close(fig)

    btn_next.on_clicked(on_next)

    ax_quit = fig.add_subplot(button_gs[0, 2])
    btn_quit = Button(
        ax_quit,
        'Save & Quit',
        color='lightcoral',
        hovercolor='red',
    )

    def on_quit(event):
        global stop_loop
        save_inputs()
        stop_loop = True
        plt.close(fig)

    btn_quit.on_clicked(on_quit)

    widget_refs.extend([btn_next, btn_quit])

    # Prevent garbage collection of Matplotlib GUI components
    fig._widgets = widget_refs



    plt.show(block=True)

    if plt.fignum_exists(fig.number):
        plt.close(fig)

    previous_fig = None

    # Save to Excel after each grouped window closes
    caca.to_excel(excel_path, index=False)

    if stop_loop:
        print("Inspection session paused. Excel file updated.")
        break

    plt.close('all')