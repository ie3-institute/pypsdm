import os
import pandas as pd
import numpy as np
import csv
from datetime import datetime
from pypsdm.processing.series import (add_series,quarter_hourly_mean_resample )
from pypsdm.models.result import (entity, )
from pypsdm.models import (enums, )
from scipy.optimize import curve_fit
from matplotlib import pyplot as plt
from pypsdm.processing.series import quarter_hourly_mean_resample


"""
Plots
"""
def glg_plot_1(sim_curve, quantile_95_tot):
    # Plot 1
    plt.plot((sim_curve.index + 1), sim_curve, label='Maximale Gleichzeitigkeit', color=(0.6, 0.6, 0.6))
    plt.grid(color='lightgrey', linestyle='-')
    plt.plot((quantile_95_tot.index + 1), quantile_95_tot, '.', label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.plot(x, y, label='Regressionskurve', color=(0.3, 0.3, 0.3))
    plt.xlabel('Anzahl der Fahrzeuge')
    plt.ylim(0, 1.1)
    plt.xlim(0, 155)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    plt.legend()
    plt.show()

def glg_plot_2(x,y):

    # plt.plot(x, gz_bi, label='V2G (Laden)', color=(0.517, 0.721, 0.094))
    # plt.plot(x, gz_bi_dis, label='V2G (Entladen)', color=(0.3, 0.3, 0.3))
    plt.plot(x, y, label='Unidirektional', color=(0.717, 0.921, 0.294))
    # plt.plot(x_unc, gz_unc, label='Ungesteuertes Laden', color=(0.6, 0.6, 0.6))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Fahrzeuge')
    plt.ylim(0, 1.3)
    plt.xlim(0, 155)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    # plt.legend()
    plt.show()

    plt.plot(x, y, label='Regressionskurve', color=(0.6, 0.6, 0.6))
    plt.plot((quantile_95_tot.index + 1), quantile_95_tot, '.', label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Fahrzeuge')
    plt.ylim(0, 1.1)
    plt.xlim(0, 155)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    plt.legend()
    plt.show()

def glg_plot_3(x,y):
    plt.plot(x, y, label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Fahrzeuge')
    plt.ylim(0, 1.1)
    plt.xlim(0, 155)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    plt.show()


def do_all_glg_plots(x,y, sim_curve, quantile_95_tot):
    # Plot 2

    glg_plot_2(x,y,)

    # Plot 1
    glg_plot_1(sim_curve,quantile_95_tot)

    # Plot 3
    glg_plot_3(x,y)


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


