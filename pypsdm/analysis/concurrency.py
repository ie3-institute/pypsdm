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
from pypsdm.models.input.container.grid import GridContainer

"""
Plots
"""

def save_plot_func(plt, folder, filename):
    file = filename + '.png'
    plt.savefig(
        os.path.join(folder, file))

def glg_plot_1(x, y, sim_curve, quantile_95_tot, save_plot, folder, filename, show_plot, ylim, xlim):
    # Plot 1
    plt.clf()
    plt.plot((sim_curve.index + 1), sim_curve, label='Maximale Gleichzeitigkeit', color=(0.6, 0.6, 0.6))
    plt.grid(color='lightgrey', linestyle='-')
    plt.plot((quantile_95_tot.index + 1), quantile_95_tot, '.', label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.plot(x, y, label='Regressionskurve', color=(0.3, 0.3, 0.3))
    plt.xlabel('Anzahl der Systemteilnehmer')
    plt.ylim(0, ylim)
    plt.xlim(0, xlim)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    plt.legend()
    if save_plot:
        save_plot_func(plt, folder, filename)
    if show_plot:
        plt.show()



def glg_plot_2a(x,y, quantile_95_tot, save_plot,folder, filename, show_plot, ylim, xlim):
    plt.clf()
    # plt.plot(x, gz_bi, label='V2G (Laden)', color=(0.517, 0.721, 0.094))
    # plt.plot(x, gz_bi_dis, label='V2G (Entladen)', color=(0.3, 0.3, 0.3))
    plt.plot(x, y, label='', color=(0.717, 0.921, 0.294))
    # plt.plot(x_unc, gz_unc, label='Ungesteuertes Laden', color=(0.6, 0.6, 0.6))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Systemteilnehmer')
    plt.ylim(0, ylim)
    plt.xlim(0, xlim)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    # plt.legend()
    if save_plot:
        save_plot_func(plt, folder, filename)
    if show_plot:
        plt.show()

def glg_plot_2b(x, y, quantile_95_tot, save_plot, folder, filename, show_plot, ylim, xlim):
    plt.clf()
    plt.plot(x, y, label='Regressionskurve', color=(0.6, 0.6, 0.6))
    plt.plot((quantile_95_tot.index + 1), quantile_95_tot, '.', label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Systemteilnehmer')
    plt.ylim(0, ylim)
    plt.xlim(0, xlim)
    plt.ylabel('Gleichzeitigkeitsfaktor')
    plt.legend()
    if save_plot:
        save_plot_func(plt, folder, filename)
    if show_plot:
        plt.show()

def glg_plot_3(x,y, save_plot,folder, filename, show_plot, ylim, xlim):
    plt.clf()
    plt.plot(x, y, label='95% Quantil', color=(0.517, 0.721, 0.094))
    plt.grid(color='lightgrey', linestyle='-')
    plt.xlabel('Anzahl der Systemteilnehmer')
    plt.ylim(0, ylim)
    plt.xlim(0, xlim)
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

# popt ist ein Array aus den optimalen Parametern, sodass die Summe der Fehlerquadrate minimiert ist
# pcov ist die zugehörige Kovarianzmatrix
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
    if ss_tot == 0:
        r_squared = 1
    else:
        r_squared = 1 - (ss_res / (n - p - 1)) / (ss_tot / (n - 1))
    return popt, pcov, r_squared


"""
Kurvenregression
"""

def curve_regression(quantile_95_indices, quantile_95, quantile_95_tot):
        # Kurvenregression
        param_opt, param_cov, r_squared = fit_sim_curve(quantile_95_indices, quantile_95)
        a_opt, b_opt, c_opt = param_opt
        fitted_sim = fit_function(quantile_95_indices, a_opt, b_opt, c_opt)

        x = np.arange(1, len(quantile_95_tot[0]) + 1)
        y = np.ones_like(quantile_95_tot[0])
        y[quantile_95_tot[0] <= 1] = fitted_sim[:len(fitted_sim)]

        return x,y



def getFloatFromString(string):
    try:
        rated_power_str = string.split(',')[1].split(':')[1].strip()
        return float(rated_power_str.split()[0])
    except IndexError:
        return 0.0  # Return a default value (0.0) if the string does not have the expected format
    except ValueError:
        return 0.0  # Return a default value (0.0) if the extracted string cannot be converted to float


def getInstalledCapacatiy(grid_container: GridContainer):
    total_s_rated_load_direction = 0
    total_s_rated_feedin_direction = 0
    installed_capacity = pd.DataFrame(columns=['s_rated_load_direction', 's_rated_feedin_direction'])

    sp_count_and_power = grid_container.get_nodal_sp_count_and_power()

    # Alternativ: Taking max of time series as installed capacity instead of s_rated from input data
    # load_srated = gwr_container.results.participants.loads.get(connected_asset).p.max()*1000

    ##### TODO FIXME: LOAD INCLUDED HERE OR NOT, alternative: find load.s.max() from time-series and take it into account
    # FIXME: p or s?
    # FIXME: BS included here or not?
    for node in grid_container.nodes.node:
        data = sp_count_and_power.get(node, {})
        load_rated_power = getFloatFromString(data.get('load', ''))
        hp_rated_power = getFloatFromString(data.get('hp', ''))
        ev_rated_power = getFloatFromString(data.get('ev', ''))
        pv_rated_power = getFloatFromString(data.get('pv', ''))
        storage_rated_power = getFloatFromString(data.get('storage', ''))


        s_rated_load_direction = load_rated_power + hp_rated_power + ev_rated_power # + storage_rated_power
        s_rated_feedin_direction = ev_rated_power + pv_rated_power # + bs_srated
        installed_capacity.loc[node] = [s_rated_load_direction, s_rated_feedin_direction]

    return installed_capacity


"""
 Gleichzeitigkeit
"""


def calculate_coincidence_curve(load, df, df_inst, len_curve, num_mc):
    coincidence_curve = pd.DataFrame(np.zeros((len_curve, 1)))
    quantile_95 = pd.DataFrame(np.zeros((len_curve, 1)))

    for n in range(1, len_curve + 1):
        if n % 25 == 0 or n==1:
            if load:
                print("Lastrichtung")
            else:
                print("Einspeiserichtung")
            print("Starte für n=",n)

        temp_sim_max_abs = np.zeros(num_mc)
        temp_sim_max_norm = np.zeros(num_mc)

        for mc in range(num_mc):
            # Randomly choose n profiles
            profile_col = np.random.choice(df.columns, size=n, replace=False)

            # Filter DF of installed capacities by the choosen n profiles
            df_inst_filtered = df_inst[df_inst.index.isin(profile_col)]

            if load:
                # get aggr. installed power of the choosen profiles in load direction in MW
                agg_inst_power = df_inst_filtered.s_rated_load_direction.sum()/1000
            else:
                agg_inst_power = df_inst_filtered.s_rated_feedin_direction.sum() / 1000


            # get mc profiles
            mc_profile = df.loc[:, profile_col]

            #.abs um die Rückspeisungen im Feed-in Fall zu erhalten, sonst ist mc_profile.sum(axis=1).max() = 0!
            tmp_abs = mc_profile.sum(axis=1).abs().max()
            temp_sim_max_abs[mc] = tmp_abs

            if agg_inst_power == 0:
                tmp_norm = 0.0
            else:
                tmp_norm = tmp_abs / agg_inst_power
            temp_sim_max_norm[mc] = tmp_norm

        coincidence_curve.iloc[n - 1, 0] = temp_sim_max_norm.max()
        quantile_95.iloc[n - 1, 0] = np.percentile(temp_sim_max_norm, 95, method='linear')

    return coincidence_curve, quantile_95


def calc_glg(load, df, node_installed_capacity, len_curve, num_mc):
    if load:
        sim_curve, quantile_95_tot = calculate_coincidence_curve(True, df, node_installed_capacity, len_curve, num_mc)
    else:
        sim_curve, quantile_95_tot = calculate_coincidence_curve(False, df, node_installed_capacity, len_curve,
                                                                                num_mc)


    quantile_95_tot_modified = quantile_95_tot.copy()
    quantile_95_tot_modified.loc[quantile_95_tot_modified.iloc[:, 0] > 1.0, quantile_95_tot_modified.columns[0]] = 1.0
    quantile_95 = quantile_95_tot_modified.loc[:, 0].to_numpy()
    quantile_95_indices = pd.Series(range(1, len(quantile_95) + 1)).to_numpy()

    return sim_curve, quantile_95, quantile_95_tot_modified, quantile_95_indices


def simultaneity_analysis_with_ems(folder_inputs, folder_glz_cases, folder_res, endtime, len_of_curve, num_of_mc, show_plots, folder_output):
    print("Start Simultaneity Analysis:")
    # Ziel: 1000, Anzahl an Monte-Carlo-Iterationen pro Punkt in der GZ-Kurve
    if num_of_mc < 1000:
        print(f"Warning: Number of Monte-Carlo iterations (n={num_of_mc}) less than 1.000.")

    file_name_glz_cases = 'node_to_case_dict.csv'
    node_cases_dict = pd.read_csv(os.path.join(folder_glz_cases, file_name_glz_cases), index_col=0).rename_axis(
        index='em_uuid')

    gwr_container = gwr.GridWithResults.from_csv(folder_inputs, folder_res, ',', simulation_end=endtime)
    gwr_nodal_results = gwr_container.build_enhanced_nodes_result()
    node_installed_capacity = getInstalledCapacatiy(gwr_container.grid)
    cases = [
        (1, 1, 1, 1, 1, 1),
        (1, 1, 1, 1, 1, 0),
        (1, 1, 1, 1, 0, 1),
        (1, 1, 1, 1, 0, 0),
        (1, 1, 1, 0, 1, 1),
        (1, 1, 1, 0, 1, 0),
        (1, 1, 1, 0, 0, 1),
        (1, 1, 1, 0, 0, 0),
        (1, 1, 0, 1, 1, 1),
        (1, 1, 0, 1, 1, 0),
        (1, 1, 0, 1, 0, 1),
        (1, 1, 0, 1, 0, 0),
        (1, 1, 0, 0, 1, 1),
        (1, 1, 0, 0, 1, 0),
        (1, 1, 0, 0, 0, 1),
        (1, 1, 0, 0, 0, 0),
        (1, 0, 0, 1, 1, 1),
        (1, 0, 0, 1, 1, 0),
        (1, 0, 0, 1, 0, 1),
        (1, 0, 0, 1, 0, 0),
        (1, 0, 0, 0, 1, 1),
        (1, 0, 0, 0, 1, 0),
        (1, 0, 0, 0, 0, 1),
        (1, 0, 0, 0, 0, 0),
        (0, 1, 1, 1, 1, 1),
        (0, 1, 1, 1, 1, 0),
        (0, 1, 1, 1, 0, 1),
        (0, 1, 1, 1, 0, 0),
        (0, 1, 1, 0, 1, 1),
        (0, 1, 1, 0, 1, 0),
        (0, 1, 1, 0, 0, 1),
        (0, 1, 1, 0, 0, 0),
        (0, 1, 0, 1, 1, 1),
        (0, 1, 0, 1, 1, 0),
        (0, 1, 0, 1, 0, 1),
        (0, 1, 0, 1, 0, 0),
        (0, 1, 0, 0, 1, 1),
        (0, 1, 0, 0, 1, 0),
        (0, 1, 0, 0, 0, 1),
        (0, 1, 0, 0, 0, 0),
        (0, 0, 0, 1, 1, 1),
        (0, 0, 0, 1, 1, 0),
        (0, 0, 0, 1, 0, 1),
        (0, 0, 0, 1, 0, 0),
        (0, 0, 0, 0, 1, 1),
        (0, 0, 0, 0, 1, 0),
        (0, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 0, 0),
    ]

    for item in cases:
        em = item[0]
        pv = item[1]
        bs = item[2]
        ev = item[3]
        hp = item[4]
        hp_new = item[5]
        filename = 'em' + str(em)+ '_pv' + str(pv) + '_bs' + str(bs) + '_ev' + str(ev) + '_hp' + str(hp) + '_hpnew' + str(hp_new)
        node_of_item_case = node_cases_dict[
            (node_cases_dict['0'] == em)
            & (node_cases_dict['1'] == pv)
            & (node_cases_dict['2'] == bs)
            & (node_cases_dict['3'] == ev)
            & (node_cases_dict['4'] == hp)
            & (node_cases_dict['5'] == hp_new)
            ]

        dfs_load = []
        dfs_feedin = []
        if len(node_of_item_case) > 0:
            for node_uuid in node_of_item_case.index:
                data_for_item = pd.DataFrame(gwr_nodal_results[node_uuid].p)
                load_data_for_item = data_for_item['p'].apply(lambda x: max(0, x))
                feedin_data_for_item = data_for_item['p'].apply(lambda x: min(0, x))
                # Create a DataFrame for each node_uuid and append it to the list
                load_df = pd.DataFrame({node_uuid: load_data_for_item})
                feedin_df = pd.DataFrame({node_uuid: feedin_data_for_item})
                dfs_load.append(load_df)
                dfs_feedin.append(feedin_df)

            # Concatenate all the DataFrames in the list along the columns axis

            new_df_load = pd.concat(dfs_load, axis=1)
            new_df_feedin = pd.concat(dfs_feedin, axis=1)

            ##### LOAD DIRECTION

            len_of_load_df = len(new_df_load.columns)

            # len_curve = 150
            len_curve = min(len_of_load_df,len_of_curve)

            # Einlesen der Daten:
            if len_of_load_df > 4:
                # FIXME: s anstatt P?
                df_resample = quarter_hourly_mean_resample(new_df_load)

                sim_curve, quantile_95, quantile_95_tot, quantile_95_indices = calc_glg(True, df_resample, node_installed_capacity, len_curve, num_of_mc)

                x, y = curve_regression(quantile_95_indices, quantile_95, quantile_95_tot)

                y_modified = y.copy()
                y_modified[y_modified > 1.0] = 1.0

                glg_plot_1(x, y_modified, sim_curve, quantile_95_tot, True, folder_output, filename + 'plot1_load', show_plots, 1.1, len_curve+5)
                glg_plot_2a(x, y_modified, quantile_95_tot, True, folder_output, filename + 'plot2a_load', show_plots, 1.3, len_curve+5)
                glg_plot_2b(x, y_modified, quantile_95_tot, True, folder_output, filename + 'plot2b_load', show_plots, 1.1, len_curve+5)
                glg_plot_3(x, y_modified, True, folder_output, filename + 'plot3_load', show_plots, 1.1, len_curve+5)
                csv_file = filename + '_csv_load'
                results_to_csv(x, y_modified, sim_curve, quantile_95_tot, quantile_95, quantile_95_indices, folder_output, csv_file)
                print('Done for ' + filename + ' containing ' + len_of_load_df.__str__() + ' elements')
            else:
                print('Warning, dataset ' + filename + ' contains less than 5 elements. Evaluation not possible.')

            ##### FEEDIN DIRECTION

            len_of_feedin_df = len(new_df_feedin.columns)

            # len_curve = 150
            len_curve = min(len_of_feedin_df, len_of_curve)

            # Einlesen der Daten:
            if len_of_feedin_df > 4:
                # FIXME: s anstatt P?
                df_resample = quarter_hourly_mean_resample(new_df_feedin)

                sim_curve, quantile_95, quantile_95_tot, quantile_95_indices = calc_glg(False, df_resample,
                                                                                        node_installed_capacity,
                                                                                        len_curve, num_of_mc)

                x, y = curve_regression(quantile_95_indices, quantile_95, quantile_95_tot)

                y_modified = y.copy()
                y_modified[y_modified > 1.0] = 1.0

                glg_plot_1(x, y_modified, sim_curve, quantile_95_tot, True, folder_output, filename + 'plot1_feedin',
                           show_plots, 1.1, len_curve + 5)
                glg_plot_2a(x, y_modified, quantile_95_tot, True, folder_output, filename + 'plot2a_feedin', show_plots,
                            1.3, len_curve + 5)
                glg_plot_2b(x, y_modified, quantile_95_tot, True, folder_output, filename + 'plot2b_feedin', show_plots,
                            1.1, len_curve + 5)
                glg_plot_3(x, y_modified, True, folder_output, filename + 'plot3_feedin', show_plots, 1.1, len_curve + 5)
                csv_file = filename + '_csv_feedin'
                results_to_csv(x, y_modified, sim_curve, quantile_95_tot, quantile_95, quantile_95_indices,
                               folder_output, csv_file)
                print('Done for ' + filename + ' containing ' + len_of_feedin_df.__str__() + ' elements')
            else:
                print('Warning, dataset ' + filename + ' contains less than 5 elements. Evaluation not possible.')
            print("Simultaneity Analysis finished")

def start():
    folder_inputs = r''
    folder_glz_cases = r''
    folder_res = r''
    output_folder = r''
    endtime = datetime(2019, 12, 31)
    num_mc = 1000
    start_simultaneity_analysis(folder_inputs, folder_glz_cases, folder_res, output_folder, endtime, num_mc)