

import os
import pandas as pd

# Get the folder path where the files are located
folder_inputs = r'C:\tmp\20231121_flex_testminigrid_2023-11-21_08-37-58\input\grid'

# Filenames
file_names = [
    'em_input.csv',
    'evcs_input.csv',
    'hp_input.csv',
    'pv_input.csv',
    'load_input.csv',
    'storage_input.csv'
]

# Read input data
print('Input data loading')

data_input_em = pd.read_csv(os.path.join(folder_inputs,file_names[0]),index_col='uuid')


# Remove em-system
data_input_em = data_input_em[~data_input_em['id'].str.contains('em-system')]

data_input_ev = pd.read_csv(os.path.join(folder_inputs, file_names[1]),index_col='uuid')
data_input_hp = pd.read_csv(os.path.join(folder_inputs, file_names[2]),index_col='uuid')
data_input_pv = pd.read_csv(os.path.join(folder_inputs, file_names[3]),index_col='uuid')
data_input_lo = pd.read_csv(os.path.join(folder_inputs, file_names[4]),index_col='uuid')
data_input_bs = pd.read_csv(os.path.join(folder_inputs, file_names[5]),index_col='uuid')
data_input_em


