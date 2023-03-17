import numpy
import argparse
import matplotlib.pyplot as plt
import h5py
import glob
import re
from typing import List, Optional, Callable, Tuple, Any, Dict
import pandas as pd
from dash_stats import get_stats, detect_outliers, search_files


def get_data_func(files: List[str], func: str) -> pd.DataFrame:
    if func == "mean":
        function = lambda df: df.mean()
    elif func == "var":
        function = lambda df: df.var()
    elif func == "median":
        function = lambda df: df.median()

    mean_data = []
    for idx, i in enumerate(files[:]):
        stats = get_stats(i)
        df_stats = pd.DataFrame.from_dict(data=stats)
        param_value = df_stats["param_value"]
        outliers = detect_outliers(df_stats, cut_px=None, cut_percent=0.1, mean=False)
        n_outliers_x = outliers[0].sum()
        n_outliers_y = outliers[1].sum()
        mean = function(df_stats)
        tmp_data = pd.DataFrame(mean).transpose()
        tmp_data = tmp_data.loc[:, tmp_data.columns != "ref_id"]
        tmp_data["x_outliers"] = n_outliers_x
        tmp_data["y_outliers"] = n_outliers_y
        tmp_data["param_value"] = param_value
        c = tmp_data.columns
        mean_data.append(tmp_data)
    mean_data = pd.concat(mean_data).reset_index()[c]

    return mean_data


def plot_mean_data(df: pd.DataFrame, func: str):
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
    start = round(df.iloc[0]["param_value"], 2)
    step = (
        round(df.iloc[-1]["param_value"], 2) - round(df.iloc[0]["param_value"], 2)
    ) / 6
    stop = round(df.iloc[-1]["param_value"] + step, 2)
    # print(start,stop,step)
    x_ticks = numpy.arange(start, stop, round(step, 2))

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
        xlabel=f"{param}",
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
        ylabel=f"Number of outliers {label}",
        marker="o",
        xticks=x_ticks,
    )
    df.plot(
        x="param_value",
        y=["rel_err_x", "rel_err_y"],
        figsize=(10, 5),
        ax=axes[0, 1],
        grid=True,
        legend=True,
        ylabel=f"Absolute relative error {label}",
        marker="o",
        xlabel=f"{param}",
        xticks=x_ticks,
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
        xticks=x_ticks,
    )


def open_dashboard(files: List[str]):

    func = ["mean", "median", "var"]
    for i in func:
        mean_data = get_data_func(files, i)
        plot_mean_data(mean_data, i)
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
    args = parser.parse_args(raw_args)

    folder_path = f"{args.input}"
    files = search_files(
        folder_path, file_name="gen_images", file_format="h5", sort=True
    )

    open_dashboard(files)


if __name__ == "__main__":
    main()
