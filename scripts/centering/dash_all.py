import numpy
import argparse
import matplotlib.pyplot as plt
import h5py
import glob
import re
from typing import List, Optional, Callable, Tuple, Any, Dict
import pandas as pd
from dash_stats import get_stats, detect_outliers, search_files, mergeDictionary

global stacked_data
stacked_data = None

def get_data_func(files: List[str], func: str) -> pd.DataFrame:
    if func == "mean":
        function = lambda df: abs(df).mean()
    elif func == "var":
        function = lambda df: abs(df).var()
    elif func == "median":
        function = lambda df: abs(df).median()

    merged_stats={"err_x_px": [],
        "err_y_px": [],
        "rel_err_x": [],
        "rel_err_y": [],
        "processing_time": [],
        "ref_id": [],
        "param_value": []}
    last_param=-1
    mean_data = []
    std_data = []

    for idx, i in enumerate(files):
        
        stats = get_stats(i)
        param_value = stats["param_value"][0]
        if param_value==last_param or last_param==-1:
            
            merged_stats=mergeDictionary(stats, merged_stats)
            last_param=param_value

        if param_value!=last_param:# or idx==len(files)-1:   
            
            
            df_stats = pd.DataFrame.from_dict(data=(merged_stats))        
            outliers = detect_outliers(df_stats, cut_percent=2, mean=False)
            
            #n_images = len(df_stats.index)
            
            n_outliers_x = 100*(outliers[0]).sum() / total_images
            n_outliers_y = 100*(outliers[1]).sum() / total_images
            mean = function(df_stats)
            std = df_stats.std()

            tmp_data = pd.DataFrame(mean).transpose()
            tmp_data = tmp_data.loc[:, tmp_data.columns != "ref_id"]
            tmp_data["x_outliers"] = n_outliers_x
            tmp_data["y_outliers"] = n_outliers_y
            tmp_data["param_value"] = param_value
            c = tmp_data.columns
            mean_data.append(tmp_data)

            tmp_data_std = pd.DataFrame(std).transpose()
            tmp_data_std = tmp_data_std.loc[:, tmp_data_std.columns != "ref_id"]
            tmp_data_std["x_outliers"] = n_outliers_x
            tmp_data_std["y_outliers"] = n_outliers_y
            tmp_data_std["param_value"] = param_value
            d = tmp_data_std.columns
            std_data.append(tmp_data_std)
            last_param=-1
            merged_stats={}
            
    try:
        mean_data = pd.concat(mean_data).reset_index()[c]
        std_data = pd.concat(std_data).reset_index()[d]
    except(ValueError):
        mean_data = pd.DataFrame(mean_data).reset_index()[c]
        std_data = pd.DataFrame(std_data).reset_index()[d]
    
    return mean_data, std_data

def plot_mean_data(df: pd.DataFrame, func: str, std_data: pd.DataFrame):
    if func == "mean":
        label = " average "
        title = "Mean"
    if func == "median":
        label = " median "
        title = "Median"
    if func == "var":
        label = " variance"
        title = "Variance"

    fig, axes = plt.subplots(2, 2)
    plt.title(f"{title}", x=-1, y=2.2)

    axes[0, 0].yaxis.label.set_size(8)
    axes[0, 1].yaxis.label.set_size(8)
    axes[1, 0].yaxis.label.set_size(8)
    axes[1, 1].yaxis.label.set_size(8)

    # x_ticks=numpy.arange(0,df.shape[0],round(df.shape[0]/6))
    param = "Threshold"
    start = round(df.iloc[0]["param_value"], 3)
    step = (
        round(df.iloc[-1]["param_value"], 3) - round(df.iloc[0]["param_value"], 3)
    ) / 6
    stop = round(df.iloc[-1]["param_value"] + step, 3)
    # print(start,stop,step)
    try:
        x_ticks = numpy.arange(start, stop, round(step, 3))
    except(ValueError):
        x_ticks = numpy.arange(start, start+1, 1)
    print(std_data)
    print(df)

    df.plot(
        x="param_value",
        y=["processing_time"],
        figsize=(10, 5),
        ax=axes[0, 0],
        grid=True,
        legend=False,
        color="purple",
        ylabel=f"Processing time {label}[s]",
        marker="o",
        xticks=x_ticks,
        xlabel=f"{param}"
    )
    if func=='mean':
        axes[0, 0].errorbar(x=df["param_value"],
            y=df["processing_time"],
            yerr=std_data["processing_time"],
            color="purple",
        )

    df.plot(
        x="param_value",
        y=["x_outliers", "y_outliers"],
        figsize=(10, 5),
        ax=axes[1, 0],
        grid=True,
        legend=True,
        color=["gray", "lightpink"],
        xlabel=f"{param}",
        ylabel=f"Percentage of outliers {label}[%]",
        marker="o",
        xticks=x_ticks
    )

    df.plot(
        x="param_value",
        y=["rel_err_x", "rel_err_y"],
        figsize=(10, 5),
        ax=axes[0, 1],
        grid=True,
        legend=True,
        ylabel=f"Absolute relative error {label} [%]",
        marker="o",
        xlabel=f"{param}",
        xticks=x_ticks
        
    )
    if func=='mean':
        axes[0, 1].errorbar(x=df["param_value"],
            y=df["rel_err_x"],
            yerr=std_data["rel_err_x"],
            color='C0'
        )
        axes[0, 1].errorbar(x=df["param_value"],
            y=df["rel_err_y"],
            yerr=std_data["rel_err_y"],
            color='orange'
        )
    df.plot(
        x="param_value",
        y=["err_x_px", "err_y_px"],
        figsize=(10, 5),
        ax=axes[1, 1],
        grid=True,
        legend=True,
        color=["green", "red"],
        ylabel=f"Absolute error {label} [px]",
        xlabel=f"{param}",
        marker="o",
        xticks=x_ticks
        
    )
    if func=='mean':
        axes[1, 1].errorbar(x=df["param_value"],
            y=df["err_x_px"],
            yerr=std_data["err_x_px"],
            color='green'
        )
        axes[1, 1].errorbar(x=df["param_value"],
            y=df["err_y_px"],
            yerr=std_data["err_y_px"],
            color='red'
        )

def open_dashboard(files: List[str]):

    func = ["mean", "median"]
    for i in func:
        mean_data, std_data = get_data_func(files, i)
        plot_mean_data(mean_data, i, std_data)
    plt.show()


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        description="Find center of lysozyme patterns in CBF images from Pilatus 2M at P09-PETRA."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        action="store",
        help="path to the HDF5 data file after centering by genetic algorithm.",
    )

    parser.add_argument(
        "-l",
        "--list",
        type=str,
        action="store",
        help="path to the cbf data file list used to optimize.",
    )
    
    args = parser.parse_args(raw_args)

    folder_path = f"{args.input}"
    files = search_files(
        folder_path, file_name="gen_images*", file_format="h5", sort=True
    )
    
    global total_images
    with open(args.list) as f:
        total_images=len(f.readlines())

    #print(files)
    open_dashboard(files)


if __name__ == "__main__":
    main()
