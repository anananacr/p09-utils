import numpy as np
import argparse
import matplotlib.pyplot as plt
import h5py
import glob
import re
from typing import List, Optional, Callable, Tuple, Any, Dict
import pandas as pd
import json


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
    files = [x for x in files if x.split("/")[-1] != "gen_images_refs.h5"]

    if sort == True:

        files = sorted(files, key=lambda x: int(x.split("/")[-2][4:]))
    # print(files)
    return files


def table_of_center(
    crystal: int, rot: int, center_file: str = None, loaded_table_center: Dict = None
) -> List[int]:

    if loaded_table_center is None:
        if center_file is None:
            data = {
                "crystal": [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5],
                "rot": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2],
                "center_x": [
                    835,
                    838,
                    829,
                    834,
                    835,
                    836,
                    836,
                    837,
                    836,
                    835,
                    835,
                    838,
                    835,
                    837,
                    835,
                    834,
                    830,
                    829,
                    827,
                    835,
                ],
                "center_y": [
                    985,
                    974,
                    971,
                    965,
                    955,
                    920,
                    919,
                    917,
                    886,
                    877,
                    869,
                    844,
                    825,
                    816,
                    802,
                    787,
                    777,
                    766,
                    758,
                    753,
                ],
            }
        else:
            # print(center_file)
            data = get_table_center(center_file)

            # print(data)
        loaded_table_center = data.copy()

    data = loaded_table_center
    df = pd.DataFrame.from_dict(data)
    # print(df)
    match = df.loc[(df["crystal"] == crystal) & (df["rot"] == rot)].reset_index()

    return [match["center_x"][0], match["center_y"][0]], loaded_table_center


def get_table_center(center_file: str) -> Dict:
    data = open(center_file, "r").read().splitlines()
    data = [x.replace("'", '"') for x in data]
    data = [json.loads(d) for d in data]
    # print(data)
    return transpose_dict(data)


def transpose_dict(data: list) -> dict:
    """
    Transposes a list of dictionaries into a dictionary of lists.

    Parameters:
        data (list): A list of dictionaries to be transposed.

    Returns:
        dict: A dictionary with keys from the original dictionaries and values as lists
              containing the corresponding values from each dictionary.

    Example:
        >>> data = [{'key1': 1, 'key2': 2}, {'key1': 3, 'key2': 4}]
        >>> transpose_dict(data)
        {'key1': [1, 3], 'key2': [2, 4]}
    """
    result = {}
    for d in data:
        for k, v in d.items():
            if k not in result:
                result[k] = []
            result[k].append(v)

    return result


def get_center_theory(
    files_path: np.ndarray, center_file: np.ndarray, loaded_table_center: str = None
) -> List[int]:
    center_theory = []

    for i in files_path:

        label = str(i).split("/")[-1]
        # print(label)
        # crystal = int(label.split("_")[0][-2:])
        # rot = int(label.split("_")[1][-3:])
        crystal = int(label.split("_")[-3][:])
        rot = int(label.split("_")[-2][:])
        # print(crystal, rot)
        center, loaded_table_center = table_of_center(
            crystal, rot, center_file, loaded_table_center
        )
        center_theory.append(center)
    # print(center_theory)
    center_theory = np.array(center_theory)
    return center_theory, loaded_table_center


def str_to_seconds(time_string: str) -> float:
    # check format
    r = re.compile(".*:.*:.*.*")
    # print(time_string)
    if r.match(time_string) is None or len(time_string) > 14:
        raise ValueError("Non expected format time (H:MM:SS.UUUUUU)")

    hours = int(time_string[0])
    # print(hours)
    minutes = int(time_string[2:4])
    seconds = float(time_string[5:])
    return 3600 * hours + 60 * minutes + seconds


def format_proc_time(time_table: np.ndarray) -> np.ndarray:
    time_table_in_seconds = []

    for i in time_table:
        time_string = i.decode("utf-8")
        time_in_seconds = str_to_seconds(time_string)
        time_table_in_seconds.append(time_in_seconds)
    return time_table_in_seconds


def get_stats(
    file_path: str, center_file: str = None, loaded_table_center: Dict = None
) -> Dict[str, Any]:
    f = h5py.File(file_path, "r")
    # try:
    #    center_theory = np.array(f["center"])[:]
    # except:
    center_theory, loaded_table_center = get_center_theory(
        np.array(f["id"]), center_file, loaded_table_center
    )

    center_calc = np.array(f["center_calc"])[:]
    # ref_image_id = list(np.array(f["ref_index"]))[:]
    ref_image_id = np.zeros(len(center_theory))
    param_value = float(np.array(f["param_value_opt"]))
    param_value = np.ones(len(center_theory)) * param_value
    # print(param_value)
    size = np.array(f["dimensions"])

    processing_time = np.array(f["processing_time"])[:]
    processing_time = format_proc_time(processing_time)

    # err_x_px = abs(center_calc[:, 0] - center_theory[:, 0])
    # rel_err_x = 100*err_x_px / size[0]

    # err_y_px = abs(center_calc[:, 1] - center_theory[:, 1])
    # rel_err_y = 100*err_y_px / size[1]

    err_x_px = center_calc[:, 0] - center_theory[:, 0]
    rel_err_x = 100 * err_x_px / size[0]

    err_y_px = center_calc[:, 1] - center_theory[:, 1]
    rel_err_y = 100 * err_y_px / size[1]
    return {
        "err_x_px": list(err_x_px),
        "err_y_px": list(err_y_px),
        "rel_err_x": list(rel_err_x),
        "rel_err_y": list(rel_err_y),
        "processing_time": processing_time,
        "ref_id": list(ref_image_id),
        "param_value": list(param_value),
    }, loaded_table_center


def detect_outliers(
    df: pd.DataFrame, mean: bool = True, cut_px: int = None, cut_percent: float = None
):

    std = df.std()
    mean = df.mean()
    if cut_percent is None:
        if mean is True:
            lim_x = [0, mean.abs(err_x_px) + cut_px * std.err_x_px]
            lim_y = [0, mean.abs(err_y_px) + cut_px * std.err_y_px]
            non_outliers_x = df.err_x_px.between(lim_x[0], lim_x[1])
            non_outliers_y = df.err_y_px.between(lim_y[0], lim_y[1])
        else:
            lim_x = [-1 * cut_px, cut_px]
            lim_y = [-1 * cut_px, cut_px]
            non_outliers_x = df.err_x_px.between(lim_x[0], lim_x[1])
            non_outliers_y = df.err_y_px.between(lim_y[0], lim_y[1])
    else:
        if cut_px is not None:
            raise ValueError("Either cut by pixel or percentage.")
        if mean is True:
            lim_x = [0, mean.abs(rel_err_x) + cut_percent * std.rel_err_x]
            lim_y = [0, mean.abs(rel_err_y) + cut_percent * std.rel_err_y]
            non_outliers_x = df.rel_err_x.between(lim_x[0], lim_x[1])
            non_outliers_y = df.rel_err_y.between(lim_y[0], lim_y[1])
        else:
            lim_x = [-1 * cut_percent, cut_percent]
            lim_y = [-1 * cut_percent, cut_percent]
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
        marker=".",
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
        marker=".",
    )
    df.plot(
        y=["rel_err_x", "rel_err_y"],
        figsize=(10, 5),
        ax=axes[0, 1],
        grid=True,
        legend=True,
        ylabel="Absolute relative error [%]",
        marker=".",
    )
    df.plot(
        y=["err_x_px", "err_y_px"],
        figsize=(10, 5),
        ax=axes[1, 1],
        grid=True,
        legend=True,
        xlabel="Image ID",
        ylabel="Absolute error [px]",
        marker=".",
    )
    if outliers is not None:
        index_outliers_x = df.index[outliers[0]]
        err = df.rel_err_x[outliers[0]]
        axes[0, 1].scatter(index_outliers_x, err, marker="x", color="r", s=100)

        index_outliers_y = df.index[outliers[1]]

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
    bins = np.arange(-5.5, 5.5, 0.5)
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
        label=["Relative error in y"],
        alpha=0.7,
        rwidth=0.5,
        width=0.5,
        bins=bins,
    )
    df.hist(
        column=["rel_err_x"],
        figsize=(10, 10),
        ax=axes[0, 1],
        grid=True,
        legend=False,
        stacked=True,
        label=["Relative error in x"],
        alpha=0.7,
        rwidth=0.5,
        width=0.5,
        bins=bins,
    )
    fig.legend()
    bins = np.arange(-80, 80, 4)
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
        rwidth=0.5,
        width=4,
        bins=bins,
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
        rwidth=0.5,
        width=4,
        bins=bins,
    )
    plt.legend()
    plt.show()


def mergeDictionary(
    dict_1: Dict[str, float], dict_2: Dict[str, float]
) -> Dict[str, float]:
    merged_dict = {**dict_1, **dict_2}
    # print(len(merged_dict['err_x_px']))
    new_list = []
    for key, list_of_values in merged_dict.items():
        if key in dict_1 and key in dict_2 and isinstance(dict_1[key], list):
            for x in dict_1[key]:
                list_of_values.append(x)
        merged_dict[key] = list_of_values
    # print(len(merged_dict['err_x_px']))
    return merged_dict


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
        folder_path, file_name="gen_images*", file_format="h5", sort=True
    )

    merged_stats = {
        "err_x_px": [],
        "err_y_px": [],
        "rel_err_x": [],
        "rel_err_y": [],
        "processing_time": [],
        "ref_id": [],
        "param_value": [],
    }

    for i in files:
        stats = get_stats(i)
        merged_stats = mergeDictionary(stats, merged_stats)

    df_stats = pd.DataFrame.from_dict(data=merged_stats)
    print(df_stats.param_value[0])
    title = f"individual_run"

    """Detect outliers in individual runs and higlight them in individual plots."""
    outliers = detect_outliers(df_stats, cut_percent=2, mean=False)
    generate_individual_plots(df_stats, title, outliers)
    generate_individual_hists(df_stats, title)


if __name__ == "__main__":
    main()
