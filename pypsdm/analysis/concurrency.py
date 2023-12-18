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
def glg_plot_1(x, y, sim_curve, quantile_95_tot):
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

def glg_plot_2(x,y, quantile_95_tot):

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

    glg_plot_2(x,y,quantile_95_tot)

    # Plot 1
    glg_plot_1(x,y,sim_curve,quantile_95_tot)

    # Plot 3
    glg_plot_3(x,y)




"""
Kurvenanpassung
"""

# https://www.askpython.com/python/examples/curve-fitting-in-python
# Die Kurvenanpassung wird nur für den Bereich vorgenommen, an dem die Funktion differenzierbar ist (wenn GZ nicht mehr 1)

# allgemeine Gleichung der erweiterten GZ-Funktion

def fit_function(n, *args):
    a, b, c = args
    return a * np.power(n, -b) + c

def fit_sim_curve(x_values, y_values):
    # Initialisierung mit Werten EV ungesteuert Dis Kippelt
    p0 = [1.785, 0.631, 0.112]
    popt, pcov = curve_fit(fit_function, x_values, y_values, p0, maxfev=10000)
    # Anzahl der Datenpunkte
    n = len(y_values)
    # Anzahl der Fit-Parameter
    p = len(popt)
    # Mittelwert der abhängigen Variable
    y_mean = np.mean(y_values)
    # Regressionsabweichungen berechnen
    residuals = y_values - fit_function(x_values, *popt)
    # Summe der quadrierten Regressionsabweichungen
    ss_res = np.sum(residuals ** 2)
    # Gesamtsumme der quadrierten Abweichungen
    ss_tot = np.sum((y_values - y_mean) ** 2)
    # Bestimmtheitsmaß berechnen
    r_squared = 1 - (ss_res / (n - p - 1)) / (ss_tot / (n - 1))
    return popt, pcov, r_squared

# popt ist ein Array aus den optimalen Parametern, sodass die Summe der Fehlerquadrate minimiert ist
# pcov ist die zugehörige Kovarianzmatrix

def curve_regression(quantile_95_indices, quantile_95, quantile_95_tot):
        # Kurvenregression
        param_opt, param_cov, r_squared = fit_sim_curve(quantile_95_indices, quantile_95)
        a_opt, b_opt, c_opt = param_opt
        fitted_sim = fit_function(quantile_95_indices, a_opt, b_opt, c_opt)

        x = np.arange(1, len(quantile_95_tot[0]) + 1)
        y = np.ones_like(quantile_95_tot[0])
        y[quantile_95_tot[0] < 1] = fitted_sim[:len(fitted_sim)]

        return x,y

# Get the folder path where the files are located
"""
 Gleichzeitigkeit
"""


def calculate_gz(df, df_inst, len_curve, num_mc):
    sim_curve = pd.DataFrame(np.zeros((len_curve, 1)))
    quantile_95 = pd.DataFrame(np.zeros((len_curve, 1)))

    for n in range(1, len_curve + 1):
        temp_sim_max_abs = np.zeros(num_mc)
        temp_sim_max_norm = np.zeros(num_mc)
        print("Calculate GZ for ev-number " + str(n))
        for mc in range(num_mc):
            # Random choice n profiles
            profile_col = np.random.choice(df.columns, size=n, replace=False)

            #  aggr. installierte Leistung der Profile bestimmen
            filtered_df = df_inst[df_inst.index.isin(profile_col)]

            # agg_inst_power = filtered_df.s_rated_em_load_direction.sum()/1000
            agg_inst_power = 0.003 * n

            # do MC choice
            profile_row = np.random.choice(df.index, size=1, replace=False)

            # get mc profiles
            mc_profile = df.loc[profile_row, profile_col]

            tmp_abs = mc_profile.sum(axis=1).max()
            temp_sim_max_abs[mc] = tmp_abs

            tmp_norm = tmp_abs / agg_inst_power
            temp_sim_max_norm[mc] = tmp_norm

        sim_curve.iloc[n - 1, 0] = temp_sim_max_norm.max()
        quantile_95.iloc[n - 1, 0] = np.percentile(temp_sim_max_norm, 95, method='linear')

    return sim_curve, quantile_95


def calc_glg(df, em_installed_capacity_res_2, len_curve, num_mc):

    # Start: GZ-Kurve
    sim_curve, quantile_95_tot = calculate_gz(df, em_installed_capacity_res_2, len_curve, num_mc)
    quantile_95_cut = quantile_95_tot.iloc[:, 0] < 1
    quantile_95 = quantile_95_tot.loc[quantile_95_cut, 0].to_numpy()
    quantile_95_indices = pd.Series(range(1, len(quantile_95) + 1)).to_numpy()

    return sim_curve, quantile_95, quantile_95_tot, quantile_95_indices

