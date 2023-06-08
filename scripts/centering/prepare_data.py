import numpy as np
import argparse
import matplotlib.pyplot as plt
import h5py
import fabio
from typing import List, Optional, Callable, Tuple, Any, Dict
from generate_artificial import generate_image

def main(raw_args=None):
    parser = argparse.ArgumentParser(
        description="Prepare data colelcted to centering with genetic.py and create artificial reference images for centering."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        action="store",
        help="Files list .lst with path to cbf files.",
    )
    parser.add_argument(
        "-n",
        "--n_images",
        type=int,
        action="store",
        help="Number of sequential images to create.",
    )
    parser.add_argument(
        "-r_in",
        "--r_in",
        type=int,
        action="store",
        help="Size of inner circle in pixels.",
    )
    parser.add_argument(
        "-r_out",
        "--r_out",
        type=int,
        action="store",
        help="Size of outer circle in pixels.",
    )
    parser.add_argument(
        "-o", "--output", type=str, action="store", help="Path to the output hdf5 file."
    )
    args = parser.parse_args(raw_args)

    n_images = args.n_images
    
    gen_images = []
    center_pos = []

    ## open list file
    f=open(args.input, 'r')
    files=f.readlines()
    total_frames=len(files)
    ## choose an image from list
    image_index = np.random.choice(total_frames, n_images)

    for i in image_index:
        file_name=files[i][:-1]
        data=np.array(fabio.open(f"{file_name}").data)
        gen_images.append(data)
        ## get theoretical center_pos
        center_pos.append([835,985])

    ## close list file    
    f.close()

    f = h5py.File(f"{args.output}/gen_images.h5", "w")
    f.create_dataset("data", data=gen_images)
    f.create_dataset("center", data=center_pos)
    f.close()

    h = data.shape[0]
    w = data.shape[1]
    center_pos = [round(w / 2), round(h / 2)]
    gen_images = []
    for i in range(n_images):
        gen_images.append(
            generate_image(
                h=h, w=w, r_in=args.r_in, r_out=args.r_out, center=center_pos
            )
        )

    index = np.arange(0, n_images)
    ref_index = np.random.choice(index, n_images)

    f = h5py.File(f"{args.output}/../gen_images_refs.h5", "w")
    f.create_dataset("data", data=gen_images)
    f.create_dataset("center", data=center_pos)
    f.create_dataset("ref_index", data=ref_index)
    f.close()


if __name__ == "__main__":
    main()