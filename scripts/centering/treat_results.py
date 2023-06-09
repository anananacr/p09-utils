import numpy as np
import argparse
import matplotlib.pyplot as plt
from typing import List, Optional, Callable, Tuple, Any, Dict
import pandas as pd


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
    parser.add_argument(
        "-p",
        "--param",
        type=str,
        action="store",
        help="path to the  HDF5 data file after centering by genetic algorithm.",
    )

    args = parser.parse_args(raw_args)
    file_path = f"{args.input}"
    df = pd.read_csv(file_path, usecols=["rel_err_x", "rel_err_y", "param_value"])

    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    # df.plot(kind="scatter", x="rel_err_x", y="rel_err_y")
    # plt.show()

    file_path = f"{args.param}"
    df_id = pd.read_csv(file_path)

    merged_df = pd.DataFrame({"g": [], "r": [], "t": [], "l": []})
    for i in df.param_value[:]:
        param = df_id.iloc[[int(i)], [0, 1, 2, 3]]
        merged_df = pd.concat([merged_df, param], ignore_index=True)

    final_df = pd.concat([df, merged_df], axis=1, ignore_index=False)
    x = np.array(final_df.rel_err_x)
    y = np.array(final_df.rel_err_y)
    z = np.array(final_df.g)
    param_value = np.array(final_df.param_value)
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    ax.scatter(x, y, z, marker="o")

    ax.set_xlabel("rel_err_x [%]")
    ax.set_ylabel("rel_err_y [%]")
    ax.set_zlabel("Generations")

    selected_index = np.where((x < 0.05) & (y < 0.05))
    x_cut = x[selected_index]
    y_cut = y[selected_index]
    z_cut = z[selected_index]
    id_cut = param_value[selected_index]
    print(id_cut)
    ax.scatter(x_cut, y_cut, z_cut, marker="o", color="red")

    plt.show()
    print(final_df.head)


if __name__ == "__main__":
    main()
