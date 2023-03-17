import numpy
import argparse
import matplotlib.pyplot as plt
import h5py
import glob
import re
from typing import List, Optional, Callable, Tuple, Any, Dict
import pandas as pd


def search_files(
    folder_path: str, file_name: str = None, file_format: str = None, sort: bool = False
) -> List[str]:

    if file_name == None:
        file_name = "*"
    if file_format == None:
        file_format = "*"

    files = list(
        glob.iglob(rf"{folder_path}/**/{file_name}.{file_format}", recursive=True)
    )

    if sort == True:
        files = sorted(files, key=lambda x: int(x.split("/")[8][4:]))

    return files[:-1]


def str_to_seconds(time_string: str) -> float:
    # check format
    r = re.compile(".*:.*:.*.*")
    if r.match(time_string) is None or len(time_string) != 14:
        raise ValueError("Non expected format time (H:MM:SS.UUUUUU)")

    hours = int(time_string[0])
    minutes = int(time_string[2:3])
    seconds = float(time_string[5:])
    return 3600 * hours + 60 * minutes + seconds


def format_proc_time(time_table: numpy.ndarray) -> numpy.ndarray:
    time_table_in_seconds = []

    for i in time_table:
        time_string = i.decode("utf-8")
        time_in_seconds = str_to_seconds(time_string)
        time_table_in_seconds.append(time_in_seconds)
    return time_table_in_seconds


def get_stats(file_path: str) -> Dict[str, Any]:
    f = h5py.File(file_path, "r")
    center_theory = numpy.array(f["center"])[:2]
    center_calc = numpy.array(f["center_calc"])[:2]
    ref_image_id = list(numpy.array(f["ref_index"]))[:2]
    param_value = numpy.array(f["param_value_opt"])

    processing_time = numpy.array(f["processing_time"])[:2]
    processing_time = format_proc_time(processing_time)

    err_x_px = abs(center_calc[:, 0] - center_theory[:, 0])
    rel_err_x = err_x_px / center_theory[:, 0]

    err_y_px = abs(center_calc[:, 1] - center_theory[:, 1])
    rel_err_y = err_y_px / center_theory[:, 1]
    return {
        "err_x_px": list(err_x_px),
        "err_y_px": list(err_y_px),
        "rel_err_x": list(rel_err_x),
        "rel_err_y": list(rel_err_y),
        "processing_time": processing_time,
        "ref_id": ref_image_id,
        "param_value": param_value,
    }


def detect_outliers(
    df: pd.DataFrame, mean: bool = True, cut_px: int = None, cut_percent: float = None
):

    std = df.std()
    mean = df.mean()
    if cut_percent is None:
        if mean is True:
            lim_x = [0, mean.err_x_px + cut_px * std.err_x_px]
            lim_y = [0, mean.err_y_px + cut_px * std.err_y_px]
            non_outliers_x = df.err_x_px.between(lim_x[0], lim_x[1])
            non_outliers_y = df.err_y_px.between(lim_y[0], lim_y[1])
        else:
            lim_x = [0, cut_px]
            lim_y = [0, cut_px]
            non_outliers_x = df.err_x_px.between(lim_x[0], lim_x[1])
            non_outliers_y = df.err_y_px.between(lim_y[0], lim_y[1])
    else:
        if cut_px is not None:
            raise ValueError("Either cut by pixel or percentage.")
        if mean is True:
            lim_x = [0, mean.rel_err_x + cut_percent * std.rel_err_x]
            lim_y = [0, mean.rel_err_y + cut_percent * std.rel_err_y]
            non_outliers_x = df.rel_err_x.between(lim_x[0], lim_x[1])
            non_outliers_y = df.rel_err_y.between(lim_y[0], lim_y[1])
        else:
            lim_x = [0, cut_percent]
            lim_y = [0, cut_percent]
            non_outliers_x = df.rel_err_x.between(lim_x[0], lim_x[1])
            non_outliers_y = df.rel_err_y.between(lim_y[0], lim_y[1])
    outliers_x = ~non_outliers_x
    outliers_y = ~non_outliers_y

    return [outliers_x, outliers_y]


def generate_individual_plots(
    df: pd.DataFrame, title: str = None, outliers: List[bool] = None
):

    fig, axes = plt.subplots(2, 2)
    plt.title(f"{title}", x=-1, y=2.2)
    df.plot(
        y=["processing_time"],
        figsize=(10, 5),
        ax=axes[0, 0],
        grid=True,
        legend=False,
        color="purple",
        ylabel="Processing time [s]",
        marker="o",
    )
    df.plot(
        y=["ref_id"],
        figsize=(10, 5),
        ax=axes[1, 0],
        xlabel="Image ID",
        grid=True,
        legend=False,
        color="gray",
        ylabel="Reference image ID",
        marker="o",
    )
    df.plot(
        y=["rel_err_x", "rel_err_y"],
        figsize=(10, 5),
        ax=axes[0, 1],
        grid=True,
        legend=True,
        ylabel="Absolute relative error",
        marker="o",
    )
    df.plot(
        y=["err_x_px", "err_y_px"],
        figsize=(10, 5),
        ax=axes[1, 1],
        grid=True,
        legend=True,
        xlabel="Image ID",
        ylabel="Absolute error [px]",
        marker="o",
    )
    if outliers is not None:
        index_outliers_x = df.index[outliers[0]]
        err = df.rel_err_x[outliers[0]]
        axes[0, 1].scatter(index_outliers_x, err, marker="x", color="r", s=100)

        index_outliers_y = df.index[outliers[1]]
        print(
            len(index_outliers_x),
            index_outliers_x,
            len(index_outliers_y),
            index_outliers_y,
        )
        err = df.rel_err_y[outliers[1]]
        axes[0, 1].scatter(index_outliers_y, err, marker="x", color="r", s=100)

        err = df.err_x_px[outliers[0]]
        axes[1, 1].scatter(index_outliers_x, err, marker="x", color="r", s=100)

        err = df.err_y_px[outliers[1]]
        axes[1, 1].scatter(index_outliers_y, err, marker="x", color="r", s=100)

        err = df.processing_time[outliers[0]]
        axes[0, 0].scatter(index_outliers_x, err, marker="x", color="r", s=100)
        err = df.processing_time[outliers[1]]
        axes[0, 0].scatter(index_outliers_y, err, marker="x", color="r", s=100)

        err = df.ref_id[outliers[0]]
        axes[1, 0].scatter(index_outliers_x, err, marker="x", color="r", s=100)
        err = df.ref_id[outliers[1]]
        axes[1, 0].scatter(index_outliers_y, err, marker="x", color="r", s=100)

    plt.show()


def generate_individual_hists(df: pd.DataFrame, title: str = None):
    fig, axes = plt.subplots(2, 2)

    df.hist(
        column=["processing_time"],
        figsize=(10, 10),
        ax=axes[0, 0],
        grid=True,
        legend=False,
        stacked=False,
        color="purple",
        alpha=0.8,
    )
    df.hist(
        column=["ref_id"],
        figsize=(10, 10),
        ax=axes[1, 0],
        grid=True,
        legend=False,
        stacked=False,
        color="gray",
        alpha=0.8,
    )

    df.hist(
        column=["rel_err_y"],
        figsize=(10, 10),
        ax=axes[0, 1],
        grid=True,
        legend=False,
        stacked=True,
        label=["Absolute relative error in y"],
        alpha=0.8,
    )
    df.hist(
        column=["rel_err_x"],
        figsize=(10, 10),
        ax=axes[0, 1],
        grid=True,
        legend=False,
        stacked=True,
        label=["Absolute relative error in x"],
        alpha=0.8,
    )
    fig.legend()

    df.hist(
        column=["err_y_px"],
        figsize=(10, 10),
        ax=axes[1, 1],
        grid=True,
        legend=False,
        stacked=True,
        label=["Absolute error in y [px]"],
        color="g",
        alpha=0.7,
    )
    df.hist(
        column=["err_x_px"],
        figsize=(10, 10),
        ax=axes[1, 1],
        grid=True,
        legend=False,
        stacked=True,
        label=["Absolute  error in x [px]"],
        color="r",
        alpha=0.7,
    )
    plt.legend()
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
        help="path to the  HDF5 data file after centering by genetic algorithm.",
    )
    args = parser.parse_args(raw_args)

    folder_path = f"{args.input}"
    files = search_files(
        folder_path, file_name="gen_images", file_format="h5", sort=True
    )

    stats = get_stats(files[7])
    df_stats = pd.DataFrame.from_dict(data=stats)

    title = "test_7"

    """Detect outliers in individual runs and higlight them in individual plots."""
    outliers = detect_outliers(df_stats, cut_px=10, cut_percent=None, mean=False)
    generate_individual_plots(df_stats, title, outliers)


if __name__ == "__main__":
    main()
