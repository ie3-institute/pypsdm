import os
import pandas as pd
import numpy as np
import csv
from datetime import datetime
from pypsdm.processing.series import (add_series,quarter_hourly_mean_resample )
from pypsdm.models.result import (entity, )
from pypsdm.models import (enums,gwr )
from scipy.optimize import curve_fit
from matplotlib import pyplot as plt
from pypsdm.processing.series import quarter_hourly_mean_resample


"""
Plots
"""

def save_plot_func(plt, folder, filename):
    file = filename + '.png'
    plt.savefig(
        os.path.join(folder, file))

def glg_plot_1(x, y, sim_curve, quantile_95_tot, save_plot, folder, filename, show_plot):
    # Plot 1
    plt.clf()
    plt.plot((sim_curve.index + 1), sim_curve, label='Maximale Gleichzeitigkeit', color=(0.6, 0.6, 0.6))
    plt.grid(color='lightgrey', linestyle='-')
    plt.plot((quantile_95_tot.index + 1), quantile_95_tot, '.', label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.plot(x, y, label='Regressionskurve', color=(0.3, 0.3, 0.3))
    plt.xlabel('Anzahl der Systemteilnehmer')
    plt.ylim(0, 1.1)
    plt.xlim(0, 155)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    plt.legend()
    if save_plot:
        save_plot_func(plt, folder, filename)
    if show_plot:
        plt.show()



def glg_plot_2a(x,y, quantile_95_tot, save_plot,folder, filename, show_plot):
    plt.clf()
    # plt.plot(x, gz_bi, label='V2G (Laden)', color=(0.517, 0.721, 0.094))
    # plt.plot(x, gz_bi_dis, label='V2G (Entladen)', color=(0.3, 0.3, 0.3))
    plt.plot(x, y, label='', color=(0.717, 0.921, 0.294))
    # plt.plot(x_unc, gz_unc, label='Ungesteuertes Laden', color=(0.6, 0.6, 0.6))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Systemteilnehmer')
    plt.ylim(0, 1.3)
    plt.xlim(0, 155)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    # plt.legend()
    if save_plot:
        save_plot_func(plt, folder, filename)
    if show_plot:
        plt.show()

def glg_plot_2b(x, y, quantile_95_tot, save_plot, folder, filename, show_plot):
    plt.clf()
    plt.plot(x, y, label='Regressionskurve', color=(0.6, 0.6, 0.6))
    plt.plot((quantile_95_tot.index + 1), quantile_95_tot, '.', label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Systemteilnehmer')
    plt.ylim(0, 1.1)
    plt.xlim(0, 155)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    plt.legend()
    if save_plot:
        save_plot_func(plt, folder, filename)
    if show_plot:
        plt.show()

def glg_plot_3(x,y, save_plot,folder, filename, show_plot):
    plt.clf()
    plt.plot(x, y, label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Systemteilnehmer')
    plt.ylim(0, 1.1)
    plt.xlim(0, 155)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    if save_plot:
        save_plot_func(plt, folder, filename)
    if show_plot:
        plt.show()


def show_all_glg_plots(x,y, sim_curve, quantile_95_tot, show_plot):
    # Plot 2

    glg_plot_2a(x,y,quantile_95_tot, False, 'nn', 'nn', show_plot)
    glg_plot_2b(x, y, quantile_95_tot, False, 'nn', 'nn', show_plot)

    # Plot 1
    glg_plot_1(x,y,sim_curve,quantile_95_tot, False, 'nn', 'nn', show_plot)

    # Plot 3
    glg_plot_3(x,y, False, 'nn','nn', show_plot)

def results_to_csv(x,y, sim_curve, quantile_95_tot, quantile_95, quantile_95_indices, folder, filename):
    data = {'x': x, 'y': y, 'sim_curve': sim_curve[0], 'quantile_95_tot': quantile_95_tot[0],
            'quantile_95': quantile_95[0], 'quantile_95_indicies': quantile_95_indices}
    df = pd.DataFrame(data).set_index('x')
    filename= filename + '.csv'
    folder_filename= os.path.join(folder, filename)
    df.to_csv(folder_filename)

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



"""
get installed capacity
"""
def get_installed_capacity(df_input, gwr_container):
    em_installed_capacity_res = pd.DataFrame(columns=['s_rated_em_load_direction', 's_rated_em_feedin_direction'])
    ems_grid = gwr_container.grid.participants.ems
    for item in df_input:
        val = getEmInstalledCapacatiyFromUuid(item, ems_grid, gwr_container)
        em_installed_capacity_res.loc[item]= [val.values[0][0], val.values[0][1]]
    return em_installed_capacity_res


def getEmInstalledCapacatiyFromUuid(em_uuid, ems_grid, gwr_container):
    load_srated = 0
    hp_srated = 0
    evcs_srated = 0
    bs_srated = 0
    pv_srated = 0
    total_s_rated_em_load_direction = 0
    total_s_rated_em_feedin_direction = 0
    em_installed_capacity = pd.DataFrame(columns=['s_rated_em_load_direction', 's_rated_em_feedin_direction'])

    for conected_asset in ems_grid.connected_assets.get(em_uuid):
        if gwr_container.grid.participants.loads.__contains__(conected_asset):
            load_srated = gwr_container.grid.participants.loads.get(conected_asset)['s_rated']
        if gwr_container.grid.participants.hps.__contains__(conected_asset):
            hp_srated = gwr_container.grid.participants.hps.get(conected_asset)['s_rated']
        if gwr_container.grid.participants.evcs.__contains__(conected_asset):
            evcs_srated = gwr_container.grid.participants.evcs.get(conected_asset)['power']
        if gwr_container.grid.participants.storages.__contains__(conected_asset):
            bs_srated = gwr_container.grid.participants.storages.get(conected_asset)['s_rated']
        if gwr_container.grid.participants.pvs.__contains__(conected_asset):
            pv_srated = gwr_container.grid.participants.pvs.get(conected_asset)['s_rated']

    ##### TODO FIXME: LOAD INCLUDED HERE OR NOT, alternative: find load.s.max() from time-series and take it into account
    #FIXME: p or s?
    # FIXME: BS included here or not?
    s_rated_em_load_direction = load_srated + hp_srated + evcs_srated + bs_srated
    s_rated_em_feedin_direction = evcs_srated + bs_srated + pv_srated
    em_installed_capacity.loc[em_uuid] = [s_rated_em_load_direction, s_rated_em_feedin_direction]

    return em_installed_capacity


"""
 Gleichzeitigkeit
"""


def calculate_coincidence_curve_load_direction(df, df_inst, len_curve, num_mc):
    coincidence_curve = pd.DataFrame(np.zeros((len_curve, 1)))
    quantile_95 = pd.DataFrame(np.zeros((len_curve, 1)))

    for n in range(1, len_curve + 1):
        temp_sim_max_abs = np.zeros(num_mc)
        temp_sim_max_norm = np.zeros(num_mc)
        #print("Calculate coincidence factor for system participant number " + str(n))
        for mc in range(num_mc):
            # Randomly choose n profiles
            profile_col = np.random.choice(df.columns, size=n, replace=False)

            # Filter DF of installed capacities by the choosen n profiles
            df_inst_filtered = df_inst[df_inst.index.isin(profile_col)]

            # get aggr. installed power of the choosen profiles in load direction in MW
            agg_inst_power = df_inst_filtered.s_rated_em_load_direction.sum()/1000

            # do MC choice
            profile_row = np.random.choice(df.index, size=1, replace=False)

            # get mc profiles
            mc_profile = df.loc[profile_row, profile_col]

            tmp_abs = mc_profile.sum(axis=1).max()
            temp_sim_max_abs[mc] = tmp_abs

            tmp_norm = tmp_abs / agg_inst_power
            temp_sim_max_norm[mc] = tmp_norm

        coincidence_curve.iloc[n - 1, 0] = temp_sim_max_norm.max()
        quantile_95.iloc[n - 1, 0] = np.percentile(temp_sim_max_norm, 95, method='linear')

    return coincidence_curve, quantile_95


def calc_glg(df, em_installed_capacity_res_2, len_curve, num_mc):

    # Start: GZ-Kurve
    sim_curve, quantile_95_tot = calculate_coincidence_curve_load_direction(df, em_installed_capacity_res_2, len_curve, num_mc)
    quantile_95_cut = quantile_95_tot.iloc[:, 0] < 1
    quantile_95 = quantile_95_tot.loc[quantile_95_cut, 0].to_numpy()
    quantile_95_indices = pd.Series(range(1, len(quantile_95) + 1)).to_numpy()

    return sim_curve, quantile_95, quantile_95_tot, quantile_95_indices


def getCasesFromConditions(dict, cond1, cond2, cond3, cond4):
    filtered_uuids = data_frame[
        (data_frame[0] == cond1) &
        (data_frame[1] == cond2) &
        (data_frame[2] == cond3) &
        (data_frame[3] == cond4)
    ].index.tolist()


def getCasesFromConditions2(data_frame, **conditions):
    filtered_indices = data_frame.index.copy()  # Initialize with all indices

    for col_name, cond in conditions.items():
        if col_name in data_frame.columns:
            filtered_indices = filtered_indices[data_frame[col_name] == cond]
        else:
            print(f"Column '{col_name}' not found.")

    return filtered_indices.tolist()

def start_simultaneity_analysis(folder_inputs, folder_glz_cases, folder_res, output_folder, endtime, num_of_mc):
    #folder_inputs = folder_inputs + '\grid'
    #folder_glz_cases = folder_inputs + '\GLZ'
    file_name_glz_cases = 'em_to_case_dict.csv'
    em_cases_dict = pd.read_csv(os.path.join(folder_glz_cases, file_name_glz_cases), index_col=0).rename_axis(
        index='em_uuid')

    gwr_container = gwr.GridWithResults.from_csv('flex_minigrid', folder_inputs, folder_res, simulation_end=endtime)
    df_input = em_cases_dict.index.tolist()
    em_installed_capacity_res_2 = get_installed_capacity(df_input,gwr_container)
    cases = [
        (1, 1, 1, 1),
        (1, 1, 1, 0),
        (1, 1, 0, 1),
        (1, 1, 0, 0),
        (1, 0, 1, 1),
        (1, 0, 1, 0),
        (1, 0, 0, 1),
        (1, 0, 0, 0),
        (0, 1, 1, 1),
        (0, 1, 1, 0),
        (0, 1, 0, 1),
        (0, 1, 0, 0),
        (0, 0, 1, 1),
        (0, 0, 1, 0),
        (0, 0, 0, 1),
        (0, 0, 0, 0),
    ]

    for item in cases:
        bs = item[0]
        ev = item[1]
        hp = item[2]
        hp_new = item[3]
        filename = 'pv1_bs' + str(bs) + '_ev' + str(ev) + '_hp' + str(hp) + '_hpnew' + str(hp_new)
        ems_of_item_case = em_cases_dict[
            (em_cases_dict['0'] == bs)
            & (em_cases_dict['1'] == ev)
            & (em_cases_dict['2'] == hp)
            & (em_cases_dict['3'] == hp_new)
            ]

        dfs = []

        for em_uuid in ems_of_item_case.index:
            data_for_item = gwr_container.results.participants.ems[em_uuid].p
            # Create a DataFrame for each em_uuid and append it to the list
            df = pd.DataFrame({em_uuid: data_for_item})
            dfs.append(df)

        # Concatenate all the DataFrames in the list along the columns axis
        new_df = pd.concat(dfs, axis=1)

        len_of_ems = len(new_df.columns)
        # len_curve = 150  # Ziel: 150, gibt die maximale Anzahl an EV innerhalb der GZ-Kurve an
        len_curve = min(len(new_df.columns), 150)  # Ziel: 150, gibt die maximale Anzahl an Elementen innerhalb der GZ-Kurve an
        num_mc = num_of_mc  # Ziel: 1000, Anzahl an Monte-Carlo-Iterationen pro Punkt in der GZ-Kurve
        show_plots = False

        """
         Initialisierung
        """

        # Einlesen der Daten:
        if len_of_ems > 2:
            # FIXME: s anstatt P?
            df_resample = quarter_hourly_mean_resample(new_df)
            df = df_resample

            sim_curve, quantile_95, quantile_95_tot, quantile_95_indices = calc_glg(df, em_installed_capacity_res_2,
                                                                                    len_curve, num_mc)
            x, y = curve_regression(quantile_95_indices, quantile_95, quantile_95_tot)

            glg_plot_1(x, y, sim_curve, quantile_95_tot, True, output_folder, filename + 'plot1', show_plots)
            glg_plot_2a(x, y, quantile_95_tot, True, output_folder, filename + 'plot2a', show_plots)
            glg_plot_2b(x, y, quantile_95_tot, True, output_folder, filename + 'plot2b', show_plots)
            glg_plot_3(x, y, True, output_folder, filename + 'plot3', show_plots)
            csv_file = filename + '_csv'
            results_to_csv(x, y, sim_curve, quantile_95_tot, quantile_95, quantile_95_indices, output_folder, csv_file)
            print('Done for ' + filename + ' containing ' + len_of_ems.__str__() + ' elements')
        else:
            print('Warning, dataset ' + filename + ' contains less than 3 elements. Evaluation not possible.')
