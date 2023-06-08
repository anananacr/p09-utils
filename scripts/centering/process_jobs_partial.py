import numpy
import argparse
import matplotlib.pyplot as plt
import h5py
import glob
import os
import re
from typing import List, Optional, Callable, Tuple, Any, Dict
import pandas as pd
from dash_stats import get_stats, detect_outliers, mergeDictionary

def search_files_filtered(
    folder_path: str, file_name: str = None, file_format: str = None, sort: bool = False, label_output_file: str=None
) -> List[str]:

    if file_name == None:
        file_name = "*"
    if file_format == None:
        file_format = "*"

    files = list(
        glob.iglob(rf"{folder_path}/**/{file_name}.{file_format}", recursive=True)
    )
    files=[x for x in files if x.split('/')[-1]!='gen_images_refs.h5']
    if sort == True:
        files = sorted(files, key=lambda x: int((x.split("/")[-1]).split("_")[-1][:-3])) 
    
    filtered_files=exclude_processed_data(files, label_output_file)
    
    filered_files=exclude_incomplete_data(filtered_files)

    return filered_files

def exclude_processed_data(files: List[str], label_output_file: str) -> List[str]:
    file_exists=int(os.path.exists(f"{label_output_file}_mean.csv"))
    if file_exists==0:
        df=initialize_files(label_output_file)
    else:
        df=pd.read_csv(label_output_file+"_mean.csv", usecols=["param_value"], dtype=int)
    id_to_process=[int((x.split('/')[-1]).split('_')[-1][:-3]) for x in files]
    files_to_process=[]
    files_to_process=[x for idx,x in enumerate(files) if id_to_process[idx] not in df.values]
    return files_to_process

def initialize_files(label_output_file: str):
    func = ["mean", "median"]
    df={"err_x_px": [],
            "err_y_px": [],
            "rel_err_x": [],
            "rel_err_y": [],
            "processing_time": [],
            "param_value": [],
            "x_outliers": [],
            "y_outliers": []}
    df=pd.DataFrame.from_dict(data=df)

    for i in func:
        df.to_csv(f"{label_output_file}_{i}.csv", index=False, mode="w", header=True)
        df.to_csv(f"{label_output_file}_{i}_std.csv", index=False, mode="w", header=True)
   
    return df

def exclude_incomplete_data(files: List[str]) -> List[str]:
    id_to_process=[int((x.split('/')[-1]).split('_')[-1][:-3]) for x in files]
    files_to_process=[]
    count=0
    last_id=-1
    for idx in range(len(id_to_process)):
        if last_id==id_to_process[idx]:
            count+=1
        else:
            if count==4:
                while count>0:
                    files_to_process.append(files[idx+count-5])
                    count-=1
        last_id=id_to_process[idx]
    #print(files_to_process)
    return files_to_process


def get_data_func(files: List[str], func: str, center_file: str =None, loaded_table_center: Dict=None) -> pd.DataFrame:
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
        "param_value": []
        
        }

    last_param=-1
    mean_data = []
    std_data = []

    for idx, i in enumerate(files):
        
        stats, update_table_center = get_stats(i, center_file, loaded_table_center)
        if idx==0:
            loaded_table_center=update_table_center.copy()
        param_value = stats["param_value"][0]
        #print(param_value, last_param)
        if param_value==last_param or last_param==-1:
            merged_stats=mergeDictionary(stats, merged_stats)

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
            merged_stats={"err_x_px": [],
            "err_y_px": [],
            "rel_err_x": [],
            "rel_err_y": [],
            "processing_time": [],
            "ref_id": [],
            "param_value": []}
        last_param=param_value
    try:
        mean_data = pd.concat(mean_data).reset_index()[c]
        std_data = pd.concat(std_data).reset_index()[d]
    except(ValueError):
        mean_data = pd.DataFrame(mean_data).reset_index()[c]
        std_data = pd.DataFrame(std_data).reset_index()[d]
    
    return mean_data, std_data


def process_files(files: List[str], center_file: str, label_output_file:str):

    func = ["mean", "median"]
    
    for i in func:
        mean_data, std_data = get_data_func(files, i, center_file)
        mean_data.to_csv(f"{label_output_file}_{i}.csv", index=False, mode="a", header=False)
        std_data.to_csv(f"{label_output_file}_{i}_std.csv", index=False, mode="a", header=False)

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

    parser.add_argument(
        "-c",
        "--center",
        type=str,
        action="store",
        help="path to the cbf data file list used to optimize.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        action="store",
        help="path to save mean and medians of error in each ID parameter.",
    )
    
    args = parser.parse_args(raw_args)
    center_file=args.center
    label=args.output
    

    folder_path = f"{args.input}"
    files = search_files_filtered(
        folder_path, file_name="gen_images*", file_format="h5", sort=True, label_output_file=label
    )
    
    global total_images
    with open(args.list) as f:
        total_images=len(f.readlines())
    
    print("Start processing")
    global loaded_table_center
    loaded_table_center = None


    process_files(files, center_file, label)


if __name__ == "__main__":
    main()
