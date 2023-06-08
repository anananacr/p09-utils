import numpy as np
import argparse
import matplotlib.pyplot as plt
import h5py
import fabio
from typing import List, Optional, Callable, Tuple, Any, Dict
from generate_artificial import generate_image_v2
import cbf


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        description="Generate an simulated data collection for center finding using genetic.py."
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
        "-o", "--output", type=str, action="store", help="Path to the output hdf5 file."
    )
    args = parser.parse_args(raw_args)

    n_images = args.n_images

    ## open list file
    f = open(args.input, "r")
    files = f.readlines()
    total_frames = len(files)
    ## choose an image from list
    image_index = np.random.choice(total_frames, 1)[0]

    file_name = files[image_index][:-1]
    data = np.array(fabio.open(f"{file_name}").data)
    ## close list file
    f.close()

    h = data.shape[0]
    w = data.shape[1]

    index_x = np.arange(440, w - 440)
    index_y = np.arange(440, h - 440)

    center_pos = np.hstack(
        (
            np.random.choice(index_x, (n_images, 1)),
            np.random.choice(index_y, (n_images, 1)),
        )
    )
    center_pos.astype(np.int64)
    gen_images = []

    f = open("center_list.txt", "w")

    for idx, i in enumerate(center_pos):
        print(i)
        data = generate_image_v2(h=h, w=w, center=i)
        data.astype(int)
        print(data.dtype)
        frame = 1

        cbf.write(f"{args.output}/simulated_{idx:03}_001_{frame:05}.cbf", data)

        d = {"crystal": idx, "rot": 1, "center_x": i[0], "center_y": i[1]}
        f.write("%s\n" % (d))

    f.close()

    center_pos = [round(w / 2), round(h / 2)]
    gen_images = []
    for i in range(1):
        gen_images.append(generate_image_v2(h=h, w=w))

    index = np.arange(0, n_images)
    ref_index = np.random.choice(index, n_images)

    f = h5py.File(f"{args.output}/gen_images_refs.h5", "w")
    f.create_dataset("data", data=gen_images)
    f.create_dataset("center", data=center_pos)
    f.create_dataset("ref_index", data=ref_index)
    f.close()


if __name__ == "__main__":
    main()
