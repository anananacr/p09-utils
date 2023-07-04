#!/usr/bin/env python3.10

from typing import List, Optional, Callable, Tuple, Any, Dict
import sys
from skued import autocenter, azimuthal_average
import fabio
import argparse
import h5py
import numpy as np
import matplotlib.pyplot as plt
from models import PF8, PF8Info
from utils import get_format
from diffractem import proc2d
from multiprocessing import Pool
from datetime import datetime
import pandas as pd
import sys
sys.path.append("../centering/")
from dash_stats import get_center_theory


def mask_peaks_and_calc_center(raw_data_index: int) -> List[Any]:
    data = raw_data[raw_data_index]
    
    xds_mask = mask_data[raw_data_index]
    
    pf8_info_mask=pf8_info.copy_and_modify_mask(xds_mask)
    center_theory=center_theory_table[raw_data_index]
    pf8_info_mask.modify_radius(center_x=center_theory[0], center_y=center_theory[1])
    pf8 = PF8(pf8_info_mask)
    print(pf8_info_mask)
    start = datetime.now()

    peak_list = pf8.get_peaks_pf8(data=data)
    indices = (
        np.array(peak_list["ss"], dtype=int),
        np.array(peak_list["fs"], dtype=int),
    )
    
    surrounding_positions = []

    for index in zip(indices[0], indices[1]):
        n = args.box_size
        row, col = index
        for i in range(-1 * n, n):
            for k in range(-1 * n, n):
                surrounding_positions.append((row + i, col + k))

    if args.bragg == 1:
        surrounding_mask = np.zeros_like(xds_mask)
        for pos in surrounding_positions:
            
            row, col = pos
            if 0 <= row < xds_mask.shape[0] and 0 <= col <= xds_mask.shape[1]:
                surrounding_mask[row, col] = 1
    elif args.bragg == -1:
        surrounding_mask = xds_mask.copy()
    else:
        surrounding_mask = np.ones_like(xds_mask)
        for pos in surrounding_positions:
            row, col = pos
            if 0 <= row < xds_mask.shape[0] and 0 <= col <= xds_mask.shape[1]:
                surrounding_mask[row, col] = 0
        
    mask = surrounding_mask
    mask[np.where(xds_mask <= 0)] = 0
    mask[np.where(data > args.hot_pixels_value)] = 0

    if args.auto==1:
        y, x = autocenter(data, mask)
        y = int(y)
        x = int(x)
    else:
        #center of mass
        x,y = proc2d.center_of_mass(data*mask)
        y=int(y)
        x=int(x)

    end = datetime.now()

    time_delta = end - start
    proc_time = str(time_delta)

    return [raw_data_index, proc_time, x, y]


def main():
    parser = argparse.ArgumentParser(
        description="Calculate center of diffraction patterns using pf8 + autocenter/diffractem"
    )
    parser.add_argument(
        "-i", "--input", type=str, action="store", help="path to list of data files .lst"
    )
    parser.add_argument(
        "-center", "--center", type=str, action="store", help="path to list of theoretical center positions file in .txt"
    )
    parser.add_argument(
        "-m", "--mask", type=str, action="store", help="path to list of mask files .lst"
    )
    parser.add_argument(
        "-o", "--output", type=str, action="store", help="path to output data files"
    )
    parser.add_argument(
        "-b", "--bragg", type=float, action="store", help="analyse bragg peaks and/or background"
    )
    parser.add_argument(
        "-t",
        "--adc_threshold",
        type=float,
        action="store",
        help="peakfinder8 parameter adc_threshold",
    )
    parser.add_argument(
        "-s",
        "--minimum_snr",
        type=float,
        action="store",
        help="peakfinder8 parameter minimum_snr",
    )
    parser.add_argument(
        "-c",
        "--min_pixel_count",
        type=int,
        action="store",
        help="pf8 parameter min_pixel_count",
    )
    parser.add_argument(
        "-l",
        "--local_bg_radius",
        type=int,
        action="store",
        help="peakfinder8 parameter local_bg_radius",
    )
    parser.add_argument(
        "-n", "--box_size", type=int, action="store", help="number of pixels of the box around the peak from -n to n"
    )
    parser.add_argument(
        "-v",
        "--hot_pixels_value",
        type=int,
        action="store",
        help="hot pixels value intensity cut off, values gretaer than v wont be considered in tthe analysis",
    )
    parser.add_argument(
        "-id",
        "--id_param",
        type=int,
        default=0,
        action="store",
        help="identification number of the combination of parameter being tested",
    )
    parser.add_argument(
        "-a",
        "--auto",
        type=int,
        default=0,
        action="store",
        help="choose method autocenter (scikit-ued) or center_of_mass (diffractem)",
    )
    global args
    args = parser.parse_args()
    
    files = open(args.input, "r")
    paths = files.readlines()
    files.close()

    mask_files = open(args.mask, "r")
    mask_paths = mask_files.readlines()
    mask_files.close()

    global raw_data
    global mask_data

    global center_theory_table
    center_theory_table, loaded_table = get_center_theory(paths, args.center)
    print(center_theory_table)
    
    file_format = get_format(args.input)
    if file_format == "lst":
        frames = []
        masks = []
        center_pos = []
        image_id = []
        total_frames = len(paths)        

        # for i in image_index:
        for i in range(total_frames):
            file_name = paths[i][:-1]
            if get_format(file_name) == "cbf":
                data = np.array(fabio.open(f"{file_name}").data)
                image_id.append(file_name)
                frames.append(data)

                mask_file_name = mask_paths[i][:-1]
                xds_mask = np.array(fabio.open(f"{mask_file_name}").data)
                masks.append(xds_mask)
            raw_data = np.array(frames)
            mask_data = np.array(masks)

        ## get peaks from peakfinder8
        global pf8_info

        pf8_info = PF8Info(
            max_num_peaks=10000,
            pf8_detector_info=dict(
                asic_nx=xds_mask.shape[1], asic_ny=xds_mask.shape[0], nasics_x=1, nasics_y=1
            ),
            adc_threshold=args.adc_threshold,
            minimum_snr=args.minimum_snr,
            min_pixel_count=args.min_pixel_count,
            max_pixel_count=200,
            local_bg_radius=args.local_bg_radius,
            min_res=0,
            max_res=1200,
            _bad_pixel_map=xds_mask
        )

    raw_data_index = np.arange(0, raw_data.shape[0])
    
    dimensions = [raw_data.shape[2], raw_data.shape[1]]
    with Pool(6) as p:
        result = p.map(mask_peaks_and_calc_center, raw_data_index)
    
    
    df = pd.DataFrame(
        result,  columns=["image_number", "proc_time", "center_x", "center_y"]
    )
    df.sort_values(by="image_number")
    print(df.proc_time)

    param_summary = [
        ["adc_threshold", f"{args.adc_threshold}"],
        ["minimum_snr", f"{args.minimum_snr}"],
        ["min_pixel_count", f"{args.min_pixel_count}"],
        ["local_bg_radius", f"{args.local_bg_radius}"],
        ["id_param", f"{args.id_param}"],
        ["box_size", f"{args.box_size}"],
        ["hot_pixels_values", f"{args.hot_pixels_value}"],
        ["opt_param", "id"],
    ]

    f = h5py.File(f"{args.output}", "w")
    f.create_dataset("id", data=image_id)
    f.create_dataset("center_calc", data=df[["center_x", "center_y"]])
    f.create_dataset("processing_time", data=list(df.proc_time))
    f.create_dataset("ref_index", data=[0])
    f.create_dataset("dimensions", data=dimensions)
    f.create_dataset("param_value_opt", data=args.id_param)
    f.create_dataset("param_collection", data=param_summary)
    f.close()


if __name__ == "__main__":
    main()
