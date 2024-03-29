import os
import pickle
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from scipy import stats as st

from scipy.interpolate import UnivariateSpline
from noise_reduction import *
from feature_extraction import *
from peak_detection import *
from main import *


fs_dict_BVP = 60  # frequency
cycle = 15
file_path = "trained_binary_model/pt1.csv"
temp_ths = [1.0, 2.0, 1.8, 1.5]  # std_, kurt, skews

models = ['AB_model', 'DT_model', 'GB_model',
          'KN_model', 'LDA_model', 'RF_model', 'SVM_model']

feats = ['HR_mean', 'HR_std', 'meanNN', 'SDNN', 'medianNN', 'meanSD', 'SDSD', 'RMSSD', 'pNN20', 'pNN50', 'TINN', 'LF', 'HF', 'ULF', 'VLF', 'LFHF',
         'total_power', 'lfp', 'hfp', 'SD1', 'SD2', 'pA', 'pQ', 'ApEn', 'shanEn', 'D2']


def PPG_ML_output(dataframe, feats, models):
    results = []

    # mean_std = pd.read_csv(mean_std_path, index_col=0).values
    mean = [7.59829670e+01, 1.10479738e+01, 8.31784498e+02, 1.23090146e+02, 8.16199267e+02, 1.19642124e+02, 1.09777805e+02, 1.63360789e+02,
            9.61310363e-03, 6.86243424e-03, 5.43510428e+02, 1.57929844e+18, 7.41346968e+18, 0.00000000e+00, 3.57286785e+17, 5.03060620e-01,
            9.35005490e+18, 2.68481955e-01, 6.42010059e-01, 1.16222863e+02, 4.45791619e+04, 6.10478333e+06, 3.31720393e-03, 1.93333810e-01, 4.40096395e+00, 1.21661119e+00]

    std = [1.42100639e+01, 4.22814853e+00, 1.33128019e+02, 3.26321332e+01, 1.40609127e+02, 4.63001917e+01, 2.87340068e+01, 5.14587972e+01, 2.59335452e-03, 2.32686887e-03, 5.42938134e+01, 3.53368583e+19, 1.73862281e+20, 1, 7.87884550e+18, 4.66362630e-01,
           2.16846564e+20, 1.07021633e-01, 1.45102434e-01, 3.67691019e+01, 2.56393920e+04, 4.98834484e+06, 1.67620506e-03, 2.02594461e-01, 3.79818465e-01, 3.07081347e-01]

    data = dataframe[feats].values
    x = data[0]-mean
    # print(x)
    np.seterr(invalid='ignore')
    np.seterr(divide='ignore', invalid='ignore')
    x = np.divide(x, std)
    # print(x)
    where_are_NaNs = np.isnan(x)
    x[where_are_NaNs] = 0
    where_are_inf = np.isinf(x)
    x[where_are_inf] = 0
    # print("x: ", x)
    for model in models:
        saved_model = joblib.load(model + '.pkl')
        y_pred = saved_model.predict([x])[0]
        print(model, ': ', y_pred)
        results.append(y_pred)
        # result = st.mode(results).mode[0]
    return results


def EDA_ML_output(dataframe, feats, models):
    results = []

    # mean_std = pd.read_csv(mean_std_path, index_col=0).values
    mean = [9.722679, 0.130046, 0.27907]

    std = [4.137142, 1.216917, 1.341929]

    data = dataframe[feats].values
    x = data[0]-mean
    # print(x)
    np.seterr(invalid='ignore')
    np.seterr(divide='ignore', invalid='ignore')
    x = np.divide(x, std)
    # print(x)
    where_are_NaNs = np.isnan(x)
    x[where_are_NaNs] = 0
    where_are_inf = np.isinf(x)
    x[where_are_inf] = 0
    # print("x: ", x)
    for model in models:
        saved_model = joblib.load(model + '.pkl')
        y_pred = saved_model.predict([x])[0]
        y_pred = int(y_pred)
        print(model, ': ', y_pred)
        results.append(y_pred)
        # results = st.mode(results).mode[0]
    return results

def final(results, models):
    weights = {'AB_model':2, 'DT_model':3, 'GB_model':7,'KN_model':6, 'LDA_model':10, 'RF_model':6, 'SVM_model':7,'EDA_AB_model':1,
               'EDA_DT_model':1, 'EDA_KN_model':1, 'EDA_GB_model':1, 'EDA_LDA_model':1, 'EDA_RF_model':1, 'EDA_SVM_model':1}
    total = 0
    tot_weights = 0
    for i in range(len(results)):
        total += weights[models[i]] * results[i]
        tot_weights += weights[models[i]]
    threshold = tot_weights/2
    print("Total: ", total)
    print("Threshold: ", threshold)
    if total > threshold:
        return 1, total, threshold
    else:
        return 0, total, threshold


def get_samples(data, label, ma_usage):
    global feat_names
    WINDOW_IN_SECONDS = 40
    ENSEMBLE = True
    samples = []

    # 64*60 , sliding window: 0.25 sec (60*0.25 = 15)
    window_len = fs_dict_BVP * WINDOW_IN_SECONDS
    sliding_window_len = int(fs_dict_BVP * WINDOW_IN_SECONDS * 0.25)

    winNum = 0
    method = True

    i = 0
    while sliding_window_len * i <= len(data) - window_len:

        # Include all windows corresponding to one window
        w = data[sliding_window_len * i: (sliding_window_len * i) + window_len]
        # Calculate stats for window
        wstats = get_window_stats_27_features(ppg_seg=w["BVP"].tolist(), window_length_sec=WINDOW_IN_SECONDS, label=label,
                                              ensemble=ENSEMBLE, ma_usage=True, fs = fs_dict_BVP)
        winNum += 1

        if wstats == []:
            i += 1
            continue
        # Seperating sample and label
        x = pd.DataFrame(wstats, index=[i])

        samples.append(x)
        i += 1
    if samples == []:
        return pd.DataFrame()
    return pd.concat(samples)

def convert_string_to_array(my_string):
    my_list = list(map(float, my_string.strip('[]').split(',')))
    my_array = np.array(my_list)
    return my_array

def create_data(ppg_data, device, fs_dict_BVP, eda_data = [], fs_dict_EDA = 4):
    if device == 1:
        data = convert_string_to_array(ppg_data)
        length = len(data)
        # Define the original sampling rate
        original_sampling_rate = int(length / 90)

        # Define the new sampling rate
        new_sampling_rate = fs_dict_BVP

        # Define the cutoff frequency of the low-pass filter
        cutoff_frequency = 11
        

        # Apply a low-pass filter to the original signal
        b, a = signal.butter(4, cutoff_frequency / (0.5 * new_sampling_rate), 'low')
        filtered_signal = signal.filtfilt(b, a, data)

        # Calculate the resampling factor
        resampling_factor = new_sampling_rate / original_sampling_rate

        # Calculate the new length of the signal
        new_length = int(len(data) * resampling_factor)

        # Resample the filtered signal
        df_BVP = signal.resample(filtered_signal, new_length)

        return df_BVP

    elif device == 2:
        ppg_data = convert_string_to_array(ppg_data)
        eda_data = convert_string_to_array(eda_data)
        length = len(ppg_data)
        # Define the original sampling rate
        original_sampling_rate = int(length / 90)

        # Define the new sampling rate
        new_sampling_rate = fs_dict_BVP

        # Define the cutoff frequency of the low-pass filter
        cutoff_frequency = 11

        # Apply a low-pass filter to the original signal
        b, a = signal.butter(4, cutoff_frequency / (0.5 * new_sampling_rate), 'low')
        filtered_signal = signal.filtfilt(b, a, ppg_data)

        # Calculate the resampling factor
        resampling_factor = new_sampling_rate / original_sampling_rate

        # Calculate the new length of the signal
        new_length = int(len(ppg_data) * resampling_factor)

        # Resample the filtered signal
        df_BVP = signal.resample(filtered_signal, new_length)
        return df_BVP, eda_data

def is_stressed(raw_ppg, raw_eda, clear_siganl_begining, device = 1):
    if device == 1:
        fs_dict_BVP = 64  # frequency

        raw_ppg = create_data(raw_ppg, device, fs_dict_BVP)

        cycle = 15
        temp_ths = [1.0, 2.0, 1.8, 1.5]  # std_, kurt, skews

        models = ['AB_model', 'DT_model',  'KN_model', 'GB_model',
                  'LDA_model', 'RF_model', 'SVM_model']

        feats = ['HR_mean', 'HR_std', 'meanNN', 'SDNN', 'medianNN', 'meanSD', 'SDSD', 'RMSSD', 'pNN20', 'pNN50', 'TINN',
                 'LF', 'HF', 'ULF', 'VLF', 'LFHF',
                 'total_power', 'lfp', 'hfp', 'SD1', 'SD2', 'pA', 'pQ', 'ApEn', 'shanEn', 'D2']

        # Standardize
        mean = np.mean(raw_ppg)
        std = np.std(raw_ppg)
        ppg_data = ((raw_ppg - mean) / std)[64:]
        # print(data)

        # Signal preprocessing

        # Bp
        bp_bvp = butter_bandpassfilter(ppg_data, 0.5, 10, fs_dict_BVP, order=2)

        # Time
        fwd = moving_average(bp_bvp, size=3)
        bwd = moving_average(bp_bvp[::-1], size=3)
        bp_bvp = np.mean(np.vstack((fwd, bwd[::-1])), axis=0)

        signal_5_percent = int(len(bp_bvp) * 0.05)
        # print(signal_5_percent)
        clean_signal = bp_bvp[clear_siganl_begining:
                              clear_siganl_begining + signal_5_percent]
        ths = statistic_threshold(clean_signal, fs_dict_BVP, temp_ths)
        len_before, len_after, time_signal_index = eliminate_noise_in_time(
            bp_bvp, fs_dict_BVP, ths, cycle)
        # print('len_before ', len_before, ' len_after ', len_after)
        # print(time_signal_index)
        df = pd.DataFrame(bp_bvp, columns=['BVP'])

        df = df.iloc[time_signal_index, :]
        df = df.reset_index(drop=True)

        # plt.plot(df)
        # plt.show()

        features_of_windows = get_samples(df, 0, True)
        if features_of_windows.empty:
            return [2, 0]
        features = features_of_windows.mean().transpose()
        print("features: ", features)
        ppg_res = PPG_ML_output(features, feats, models)
        # ppg_res = st.mode(ppg_res).mode[0]
        results = ppg_res
        final_res, total, threshold = final(results, models)
        print(final_res)
    elif device == 2:
        fs_dict_BVP = 64  # ppg frequency
        fs_dict_EDA = 4  # eda frequency
        raw_ppg, raw_eda = create_data(raw_ppg, device, fs_dict_BVP, raw_eda, fs_dict_EDA)

        #EDA

        eda_models = ['EDA_AB_model', 'EDA_DT_model', 'EDA_KN_model', 'EDA_GB_model',
                  'EDA_LDA_model', 'EDA_RF_model', 'EDA_SVM_model']

        eda_feats = ['number_of_peaks', 'mean_gsr', 'max_of_peaks']

        mean_eda = np.mean(raw_eda)
        std_eda = np.std(raw_eda)
        eda_data = ((raw_eda - mean_eda) / std_eda)[4:]

        # print(raw_eda)
        m, wd, eda_clean = process_statistical(eda_data, use_scipy=True, sample_rate=4,
                                               new_sample_rate=4, segment_width=40,
                                               segment_overlap=0)

        eda_features = pd.DataFrame(columns=['number_of_peaks', 'mean_gsr', 'max_of_peaks'])
        for i in range(len(m['segment_indices'])):
            eda_features = eda_features.append(
                {'number_of_peaks': m['number_of_peaks'][i], 'mean_gsr': m['mean_gsr'][i],
                 'max_of_peaks': m['max_of_peaks'][i]}, ignore_index=True)

        # print(eda_features)
        if eda_features.empty:
            return [2, 0]
        eda_features = eda_features.mean().transpose()
        print("features: ", eda_features)
        eda_res = EDA_ML_output(eda_features, eda_feats, eda_models)
        print(eda_res)



        #PPG

        cycle = 15
        temp_ths = [1.0, 2.0, 1.8, 1.5]  # std_, kurt, skews

        models = ['AB_model', 'DT_model', 'KN_model', 'GB_model',
                  'LDA_model', 'RF_model', 'SVM_model']

        feats = ['HR_mean', 'HR_std', 'meanNN', 'SDNN', 'medianNN', 'meanSD', 'SDSD', 'RMSSD', 'pNN20', 'pNN50', 'TINN',
                 'LF', 'HF', 'ULF', 'VLF', 'LFHF',
                 'total_power', 'lfp', 'hfp', 'SD1', 'SD2', 'pA', 'pQ', 'ApEn', 'shanEn', 'D2']

        # Standardize
        mean = np.mean(raw_ppg)
        std = np.std(raw_ppg)
        ppg_data = ((raw_ppg - mean) / std)[64:]
        # print(data)

        # Signal preprocessing

        # Bp
        bp_bvp = butter_bandpassfilter(ppg_data, 0.5, 10, fs_dict_BVP, order=2)

        # Time
        fwd = moving_average(bp_bvp, size=3)
        bwd = moving_average(bp_bvp[::-1], size=3)
        bp_bvp = np.mean(np.vstack((fwd, bwd[::-1])), axis=0)

        signal_5_percent = int(len(bp_bvp) * 0.05)
        # print(signal_5_percent)
        clean_signal = bp_bvp[clear_siganl_begining:
                              clear_siganl_begining + signal_5_percent]
        ths = statistic_threshold(clean_signal, fs_dict_BVP, temp_ths)
        len_before, len_after, time_signal_index = eliminate_noise_in_time(
            bp_bvp, fs_dict_BVP, ths, cycle)
        # print('len_before ', len_before, ' len_after ', len_after)
        # print(time_signal_index)
        df = pd.DataFrame(bp_bvp, columns=['BVP'])

        df = df.iloc[time_signal_index, :]
        df = df.reset_index(drop=True)

        # plt.plot(df)
        # plt.show()

        features_of_windows = get_samples(df, 0, True)
        if features_of_windows.empty:
            return [2, 0]
        features = features_of_windows.mean().transpose()
        print("features: ", features)
        ppg_res = PPG_ML_output(features, feats, models)
        results =  ppg_res + eda_res
        final_res, total, threshold = final(results, models + eda_models)
        print(final_res)
        # res = st.mode(results).mode[0]
    print("Stressed") if final_res else print("Not stressed")
    return [final_res, features['HR_mean'], total, threshold]

# # Read the CSV file
# df = pd.read_csv(file_path)
#
# # Convert the DataFrame to a NumPy array
# data = df.columns.values
# data = np.array(data).astype(float)
#
# print(is_stressed(data, 1380))

# # Standardize
# mean = np.mean(data)
# std = np.std(data)
# data = ((data - mean) / std)[64:]
# # print(data)
#
# # Signal preprocessing
#
# # Bp
# bp_bvp = butter_bandpassfilter(data, 0.5, 10, fs_dict_BVP, order=2)
#
# # Time
# fwd = moving_average(bp_bvp, size=3)
# bwd = moving_average(bp_bvp[::-1], size=3)
# bp_bvp = np.mean(np.vstack((fwd, bwd[::-1])), axis=0)
#
# signal_5_percent = int(len(bp_bvp) * 0.05)
# # print(signal_5_percent)
# clean_signal = bp_bvp[3380:3380 + signal_5_percent]
# ths = statistic_threshold(clean_signal, fs_dict_BVP, temp_ths)
# len_before, len_after, time_signal_index = eliminate_noise_in_time(bp_bvp, fs_dict_BVP, ths, cycle)
# # print('len_before ', len_before, ' len_after ', len_after)
# # print(time_signal_index)
# df = pd.DataFrame(bp_bvp, columns=['BVP'])
#
# df = df.iloc[time_signal_index, :]
# df = df.reset_index(drop=True)
#
# # plt.plot(df)
# # plt.show()
#
# features_of_windows = get_samples(df, 0, True)
# features = features_of_windows.mean().transpose()
# print("features: ", features)
# print("Stressed") if ML_output(features, feats, models) else print("Not stressed")
