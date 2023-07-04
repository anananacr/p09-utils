import numpy as np
import argparse
import matplotlib.pyplot as plt
from typing import List, Optional, Callable, Tuple, Any, Dict
import pandas as pd


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        description="Hyperparameters grid-search optmization analysis for peakfinder8 optimization"
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
        help="path to the combination of parameters text file.",
    )

    args = parser.parse_args(raw_args)
    file_path = f"{args.input}"
    df = pd.read_csv(
        file_path, usecols=["rel_err_x", "rel_err_y", "processing_time", "param_value"]
    )

    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    ####
    # copy std parameters
    file_path=f"{args.input[:-4]}_std.csv"
    df_std = pd.read_csv(
       file_path, usecols=["rel_err_x", "rel_err_y", "processing_time", "param_value"]
    )

    df_std.dropna(inplace=True)
    df_std.reset_index(drop=True, inplace=True)
    df_std.columns=["rel_err_x_std", "rel_err_y_std", "processing_time_std", "param_value_std"]
    if df_std.param_value_std.equals(df.param_value):
        
        df = pd.concat([df,df_std], axis = 1)
    #print(df)

    ####

    #df.plot(kind="scatter", x="rel_err_x", y="rel_err_y")
    #plt.show()

    file_path = f"{args.param}"
    df_id = pd.read_csv(file_path)



    merged_df = pd.DataFrame({"s": [], "v": [], "c": [], "n": [], "t": [], "l": []})
    for i in df.param_value[:]:
        param = df_id.iloc[[int(i)], [0, 1, 2, 3, 4, 5, 6]]
        merged_df = pd.concat([merged_df, param], ignore_index=True)
    final_df = pd.concat([df, merged_df], axis=1, ignore_index=False)
    print(final_df.head())

    x = np.array(final_df.rel_err_x)
    y = np.array(final_df.rel_err_y)
    z = np.array(final_df.processing_time, dtype=np.int32)
    param_value = np.array(final_df.param_value)
    param_value_g = np.array(final_df.s)
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    ax.scatter(x, y, z, marker="o")

    ax.set_xlabel("rel_err_x (%)")
    ax.set_ylabel("rel_err_y (%)")
    ax.set_zlabel("Processing time (s)")
    #ax.set_zlim(0, 3600)
    selected_index = np.where((x < 0.06) & (y < 0.06))
    x_cut = x[selected_index]
    y_cut = y[selected_index]
    z_cut = z[selected_index]
    id_cut = param_value[selected_index]

    selected_index_2 = np.where((x < 0.06) & (y < 0.06) & (z < 3000))
    print(id_cut)

    gen_cut = param_value_g[selected_index_2]
    print(gen_cut)
    #print('rel_err_x', x[selected_index_2])
    #print('rel_err_y', y[selected_index_2])


    x_std = np.array(final_df.rel_err_x_std)
    y_std = np.array(final_df.rel_err_y_std)
    #print('rel_err_x_std', x_std[selected_index_2])
    #print('rel_err_y_std', y_std[selected_index_2])
    
    id_cut = np.array(final_df.param_value)

    best_id=pd.DataFrame({
        "rel_err_x": x[selected_index_2],
        "rel_err_y": y[selected_index_2],
        "rel_err_x_std": x_std[selected_index_2],
        "rel_err_y_std": y_std[selected_index_2],
        "id": id_cut[selected_index_2]
    })

    print(best_id)
    for i in best_id.keys()[:-1]:
        print(best_id.sort_values(i).index)
    
    ax.scatter(x_cut, y_cut, z_cut, marker="o", color="red")
    best_combination=int(best_id.id.iloc[0])
    print(final_df.loc[final_df.param_value == best_combination])
    plt.show()
    


if __name__ == "__main__":
    main()
