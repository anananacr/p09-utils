#!/usr/bin/env python3.7

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
sys.path.append("../centering/")
from dash_stats import get_center_theory

def main():
    parser = argparse.ArgumentParser(description="Merge summed up PILATUS images.")
    parser.add_argument(
        "-i", "--input", type=str, action="store", help="path to list of data files"
    )
    parser.add_argument(
        "-m", "--mask", type=str, action="store", help="path to list of mask files"
    )
    parser.add_argument(
        "-b",
        "--bragg",
        type=int,
        action="store",
        help="analyse bragg peaks and/or background",
    )
    parser.add_argument(
        "-center",
        "--center",
        type=str,
        action="store",
        help="path to list of theoretical center positions file in .txt",
    )
    args = parser.parse_args()
    print(args)
    files = open(args.input, "r")
    paths = files.readlines()

    mask_files = open(args.mask, "r")
    mask_paths = mask_files.readlines()

    table_real_center, loaded_table = get_center_theory(paths, args.center)

    for idx, i in enumerate(paths):
        file_format = get_format(i)
        if file_format == "cbf":
            frame = np.array(fabio.open(f"{i[:-1]}").data)

        elif file_format == "h5":
            hdf5_file = str(i[:-1])
            f = h5py.File(hdf5_file, "r")
            print(f.keys())
            frame = np.array(f["entry/data/data"][idx])

        file_format = get_format(mask_paths[idx])
        if file_format == "cbf":
            xds_mask = np.array(fabio.open(f"{mask_paths[idx][:-1]}").data)
            mask = np.ones_like(xds_mask)
            mask[np.where(xds_mask <= 0)] = 0
            mask[np.where(xds_mask > 0)] = 1
            print(mask.shape)

        elif file_format == "h5":
            hdf5_file = str(mask_paths[idx][:-1])
            f = h5py.File(hdf5_file, "r")
            # print(f.keys())
            mask = np.array(f["data/data"][idx])

        # print(indices)
        from models import PF8Info, PF8

        ##get peaks from pf8
        pf8_info = PF8Info(
            max_num_peaks=10000,
            pf8_detector_info=dict(
                asic_nx=mask.shape[1], asic_ny=mask.shape[0], nasics_x=1, nasics_y=1
            ),
            adc_threshold=9,
            minimum_snr=3,
            min_pixel_count=2,
            max_pixel_count=200,
            local_bg_radius=3,
            min_res=0,
            max_res=1200,
            _bad_pixel_map=mask
        )
        real_center = table_real_center[idx][::-1]
        pf8_info_mask.modify_radius(center_x=center_theory[0], center_y=center_theory[1])
        pf8 = PF8(pf8_info)

        peak_list = pf8.get_peaks_pf8(data=frame)
        #print(peak_list)
        indices = (
            np.array(peak_list["ss"], dtype=int),
            np.array(peak_list["fs"], dtype=int),
        )
        num_pixels = np.array(peak_list["num_pixels"], dtype=int)

        mask[indices] = 0

        surrounding_positions = []
        count = 0
        for index in zip(indices[0], indices[1]):
            n = 3
            row, col = index
            for i in range(-1 * n, n):
                for k in range(-1 * n, n):
                    surrounding_positions.append((row + i, col + k))
            count += 1

        # print(args.bragg)
        if args.bragg == 1:
            surrounding_mask = np.zeros_like(mask)
            for pos in surrounding_positions:
                row, col = pos
                if 0 <= row < mask.shape[0] and 0 <= col <= mask.shape[1]:
                    surrounding_mask[row, col] = 1
        elif args.bragg == -1:
            surrounding_mask = np.ones_like(mask)
        else:
            surrounding_mask = np.ones_like(mask)
            for pos in surrounding_positions:
                row, col = pos
                if 0 <= row < mask.shape[0] and 0 <= col <= mask.shape[1]:
                    surrounding_mask[row, col] = 0

        surrounding_mask[np.where(xds_mask <= 0)] = 0
        mask = surrounding_mask
        mask[np.where(frame > 7000)] = 0

        center = autocenter(frame, mask)
        
        
        x, y = azimuthal_average(frame, real_center, mask)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        ax1.imshow(frame * mask, vmax=10)
        ax1.scatter(center[1], center[0], color="r", marker="o", label="autocenter")
        ax1.scatter(real_center[1], real_center[0], color="k", marker="o", label="xds")
        print(f"Center xds X = {real_center[1]} Y = {real_center[0]}")
        print(f"Center autocenter X = {center[1]} Y = {center[0]}")
        center = proc2d.center_of_mass(frame * mask)
        ax1.scatter(center[0], center[1], color="g", marker="o", label="diffractem")
        print(f"Center diffractem  X = {center[0]} Y = {center[1]}")

        ax2.plot(x, y)
        ax2.set_title("Radial average")
        ax1.legend()
        plt.show()


if __name__ == "__main__":
    main()
