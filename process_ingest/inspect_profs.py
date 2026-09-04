import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.widgets import CheckButtons, Button, TextBox


'''
plot profiles in 'scope(smp)_cleaning_YEAR_filled.xlsx' and identify if there's an 
air gap, ground strike, overload, of if profile needs to be tossed

'''

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

excel_path = f'{pen_type}_cleaning_25_filled.xlsx'
caca = pd.read_excel(excel_path)
flag_cols = ['viewed', 'air gap', 'toss', 'ground', 'overload']

for col in flag_cols:
    if col in caca.columns:
        caca[col] = caca[col].fillna(0.0).astype(float)

unviewed_indices = caca[caca['viewed'] == 0].index

stop_loop = False
for ix in unviewed_indices:
    row = caca.loc[ix]
    pit_id = str(row.iloc[0]).replace('_scope.csv', '').replace('_smp.csv', '')

    full_profile_id = row.iloc[1]

    profile_id = '_'.join(str(row.iloc[1]).split('_'[-2:])).replace('.csv', '')

    profile_path = f'/Users/colemankane_1/Documents/BSU/penetrometer_analysis_v2/data/pen_profiles/{pen_path}/{full_profile_id}'

    profile = pen_func(profile_path)

    fig = plt.figure(figsize=[10, 8])
    plt.subplots_adjust(right=0.65)

    max_force = profile['force'].max()

    ax_plot = fig.add_subplot(111)
    ax_plot.plot(profile['force'], profile['depth'], linewidth=1)
    ax_plot.set_title(f'{pit_id}\n{profile_id}')
    ax_plot.set_xlabel('Force')
    ax_plot.set_ylabel('Depth')
    ax_plot.invert_yaxis()
    ax_plot.axvline(x=0, color='black', linestyle='dashed')
    ax_plot.set_xlim(-5, max_force +2)

    # 1. Interactive Checkboxes (viewed + error flags)
    ax_check = plt.axes([0.68, 0.52, 0.26, 0.38])
    initial_states = [bool(caca.at[ix, col]) if pd.notna(caca.at[ix, col]) else False for col in flag_cols]

    check = CheckButtons(ax_check, flag_cols, initial_states)
    for label in check.labels:
        label.set_fontsize(16)

    def on_toggle(label):
        current_val = caca.at[ix, label]
        caca.at[ix, label] = 0 if current_val == 1 else 1


    check.on_clicked(on_toggle)

    air_val = caca.at[ix, 'air gap']
    init_air_val = str(air_val) if (pd.notna(air_val) and air_val != 0) else ''
    ax_tb_air = plt.axes([0.68, 0.42, 0.26, 0.05])
    tb_air = TextBox(ax_tb_air, 'Air Gap: ', initial=init_air_val)

    # 3. Text Box for Ground Depth
    ground_val = caca.at[ix, 'ground']
    init_ground_val = str(ground_val) if (pd.notna(ground_val) and ground_val != 0) else ''
    ax_tb_ground = plt.axes([0.68, 0.33, 0.26, 0.05])
    tb_ground = TextBox(ax_tb_ground, 'Ground: ', initial=init_ground_val)


    # Helper function to parse and save depth text inputs
    def save_inputs():
        air_val = tb_air.text.strip()
        if air_val != '':
            caca.at[ix, 'air gap'] = float(air_val)

        else:
            caca.at[ix, 'air gap'] = 0

        ground_val = tb_ground.text.strip()
        if ground_val != '':
            caca.at[ix, 'ground'] = float(ground_val)
        else:
            caca.at[ix, 'ground'] = 0


    # 4. Next Profile Button
    ax_next = plt.axes([0.68, 0.18, 0.26, 0.07])
    btn_next = Button(ax_next, 'Next Profile', color='lightgreen', hovercolor='limegreen')


    def on_next(event):
        save_inputs()
        plt.close(fig)


    btn_next.on_clicked(on_next)

    # 5. Save & Quit Button
    ax_quit = plt.axes([0.68, 0.08, 0.26, 0.07])
    btn_quit = Button(ax_quit, 'Save & Quit', color='lightcoral', hovercolor='red')


    def on_quit(event):
        global stop_loop
        save_inputs()
        stop_loop = True
        plt.close(fig)


    btn_quit.on_clicked(on_quit)

    # Prevent garbage collection of Matplotlib GUI components
    fig._widgets = [check, tb_air, tb_ground, btn_next, btn_quit]

    plt.show()

    # Save to Excel after each profile window closes
    caca.to_excel(excel_path, index=False)

    if stop_loop:
        print("Inspection session paused. Excel file updated.")
        break