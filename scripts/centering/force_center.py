from typing import List, Optional, Callable, Tuple, Any, Dict, Union
import h5py
import numpy as np
import fabio
import math
import argparse
import matplotlib.pyplot as plt
import matplotlib.colors as color


def bring_center_to_point(
    data: np.ndarray, center: List[int] = None, point: List[int] = None
) -> Union[np.ndarray, List[int]]:
    """
    Function shifts data center [xc,yc] to a point [xf,yf], so after transformation [xc,yc] -> [xf,yf]

    Parameters
    ----------
    data: np.ndarray
        Image that will be shifted.
    center: List[int]
        Center of the image that will be shifted to point.
    point: List[int]
        Final coordinates of the center after transformation.

    Returns
    ----------
    new_image: np.ndarray
        Image shifted
    shift: List[int]
        Number of pixels shifted in x and y.
    """
    h = data.shape[0]
    w = data.shape[1]
    if center == None:
        ##bring to center of the image
        center = (int(w / 2), int(h / 2))

    if point.all() == None:
        ##bring to center of the image
        img_center = (int(w / 2), int(h / 2))
    else:
        img_center = point

    shift = [round(img_center[0] - center[0]), round(img_center[1] - center[1])]
    new_image = np.zeros((h, w))

    if shift[0] <= 0 and shift[1] > 0:
        # move image to the left and up
        new_image[abs(shift[1]) :, : w - abs(shift[0])] = data[
            : -abs(shift[1]), abs(shift[0]) :
        ]
    elif shift[0] > 0 and shift[1] > 0:
        # move image to the right and up
        new_image[abs(shift[1]) :, abs(shift[0]) :] = data[
            : -abs(shift[1]), : -abs(shift[0])
        ]
    elif shift[0] > 0 and shift[1] <= 0:
        # move image to the right and down
        new_image[: h - abs(shift[1]), abs(shift[0]) :] = data[
            abs(shift[1]) :, : -abs(shift[0])
        ]
    elif shift[0] <= 0 and shift[1] <= 0:
        # move image to the left and down
        new_image[: h - abs(shift[1]), : w - abs(shift[0])] = data[
            abs(shift[1]) :, abs(shift[0]) :
        ]

    return new_image, shift


def diff_from_ref(img: np.ndarray) -> np.ndarray:
    """
    Function that calculates the difference of an image with its flipped image in both axis.

    Parameters
    ----------
    img: np.ndarray
        Image that will be shifted.

    Returns
    ----------
    diff_map: np.ndarray
        Subtracted image from itsself flipped in both axis.
    """
    # print(type(img))
    flip_img = img[::-1, ::-1]
    diff_map = img.copy()
    for i in range(diff_map.shape[0]):
        for j in range(diff_map.shape[1]):
            val = (img[i, j] - flip_img[i, j]) / img[i, j]
            diff_map[i, j] = val

    diff_map = np.nan_to_num(diff_map)
    diff_map[np.where(diff_map >= 1)] = 0
    diff_map[np.where(diff_map <= -1)] = 0

    # fh, ax = plt.subplots(1,1, figsize=(8, 8))
    # plt.imshow(diff_map, cmap='bwr',vmin=-1,vmax=1)
    # plt.show()

    return diff_map


def norm_intensity(img: np.ndarray) -> np.ndarray:
    """
    Function that normalizes an image intensity.

    Parameters
    ----------
    img: np.ndarray
        Image to normalize intensities.

    Returns
    ----------
    new_image: np.ndarray
        Normalized image.
    """

    norm = (img - np.min(img)) / (np.max(img) - np.min(img))

    return norm


def calc_score(img) -> float:
    """
    Function that calculates the score of a difference map.
    Parameters
    ----------
    img: np.ndarray
        Difference map to calculate the overall score (smoothness of the difference map).

    Returns
    ----------
    score: float
        Score of the difference map
    """

    mean = 0
    count = 0
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            if img[i, j] != 0:
                mean += (img[i, j]) ** 2
                count += 1
    mean /= count
    mean = math.sqrt(mean)

    return mean


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        description="Find center of lysozyme patterns in CBF images from Pilatus 2M at P09-PETRA."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        action="store",
        help="Path to the cbf file.",
    )
    parser.add_argument(
        "-m",
        "--mask",
        type=str,
        action="store",
        help="Path to the virtual H5 mask file.",
    )
    parser.add_argument(
        "-x1",
        "--x_min",
        type=int,
        action="store",
        help="Lower limit in x to perform search of the beam center position.",
    )
    parser.add_argument(
        "-x2",
        "--x_max",
        type=int,
        action="store",
        help="Higher limit in x to perform search of the beam center position.",
    )
    parser.add_argument(
        "-y1",
        "--y_min",
        type=int,
        action="store",
        help="Lower limit in y to perform search of the beam center position.",
    )
    parser.add_argument(
        "-y2",
        "--y_max",
        type=int,
        action="store",
        help="Higher limit in y to perform search of the beam center position.",
    )
    parser.add_argument(
        "-o", "--output", type=str, action="store", help="Path to the output H5 file."
    )
    parser.add_argument("-l", "--label", type=str, action="store", help="Sample label.")
    args = parser.parse_args(raw_args)

    file_name = f"{args.input}"
    data = np.array(fabio.open(f"{file_name}").data)

    f = h5py.File(f"{args.mask}", "r")
    mask = np.array(f["data/data"])
    f.close()

    norm_data = norm_intensity(data * mask)

    mean = []
    std = []
    center_pos = []
    for i in range(args.x_min, args.x_max):
        for j in range(args.y_min, args.y_max):
            center_pos.append([i, j])

    histogram_log = []

    for i in center_pos:
        alligned, shift = bring_center_to_point(norm_data * mask, i)
        after = diff_from_ref(alligned)
        score = calc_score(after)
        mean.append(score)
        histogram, bin_edges = np.histogram(after, bins=100, range=(-1, 1))
        # plt.plot(bin_edges[0:-1], histogram, label=f'center: {i[0]} {i[1]}')
        histogram_log.append(histogram)

    index = np.argmin(mean)
    # print(f'center find at {center_pos[index]}, index {index}')

    fh, ax = plt.subplots(1, 1, figsize=(8, 8))
    pos = np.arange(0, len(mean))
    plt.scatter(pos, mean, color="b", marker=".")

    plt.scatter(pos[index], mean[index], color="r", marker="o")
    # plt.errorbar(pos[index],mean[index],yerr=std[index], ecolor='r')
    plt.savefig(
        f"{args.label}_score_center_{center_pos[index][0]}_{center_pos[index][1]}_index_{index}.png"
    )

    alligned, shift = bring_center_to_point(norm_data * mask, center_pos[index])
    after = diff_from_ref(alligned)

    fh, ax = plt.subplots(1, 1, figsize=(8, 8))
    plt.imshow(data * mask, vmax=10)
    plt.scatter(center_pos[index][0], center_pos[index][1], color="r", marker="o")
    plt.savefig(
        f"{args.label}_image_center_{center_pos[index][0]}_{center_pos[index][1]}_index_{index}.png"
    )
    min_center = [center_pos[index][0], center_pos[index][1], index]

    f = h5py.File(f"{args.output}.h5", "w")
    f.create_dataset("center_positions", data=center_pos)
    f.create_dataset("mean", data=mean)
    f.create_dataset("px_dist", data=histogram_log)
    f.create_dataset("bin_edges", data=bin_edges)
    f.create_dataset("alligned_data", data=alligned)
    f.create_dataset("center_position", data=min_center)
    f.create_dataset("difference_map_allligned_data", data=after)
    f.close()


if __name__ == "__main__":
    main()
