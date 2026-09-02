import numpy as np
import pandas as pd
import os

'''
Determines penetration of standard ram tube weight alone
If Powder ram profile exists at same pit, fills leading values
    in standard ram profile with those of the powder ram.
Exports as _sram.csv in specified directory
'''


data_dir = '/Users/colemankane_1/Documents/BSU/penetrometer_analysis_v2/data/pen_profiles/ram_files'

data_lst = os.listdir(data_dir)
print(data_lst)

srams = [i for i in data_lst if i.endswith('sram.csv')]
print(len(srams))
prams = [i for i in data_lst if i.endswith('pram.csv')]


# find sram profiles that have accompanying pram profile
prams = [i for i in prams if any(i.startswith(j.replace('_sram.csv', '')) for j in srams)]

srams = [i for i in srams if any(i.startswith(j.replace('_pram.csv', '')) for j in prams)]

for x in range(len(srams)):
    pit_id = srams[x].replace('_sram.csv', '')
    print(pit_id)
    sram = pd.read_csv(os.path.join(data_dir, f'{pit_id}_sram.csv'))

    pram = pd.read_csv(os.path.join(data_dir, f'{pit_id}_pram.csv'))

    # find intial penetration with sram
    l_limit = sram['l_cm'].iloc[0]

    filtered_pram = pram[pram['l_cm'] < l_limit]

    sram = sram.iloc[1:]

    sram = pd.concat([filtered_pram, sram],ignore_index=True)

    sram.to_csv(os.path.join(data_dir, f'{pit_id}_sram.csv'))

