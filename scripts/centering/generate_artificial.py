import numpy as np
import argparse
import matplotlib.pyplot as plt
import h5py
from typing import List, Optional, Callable, Tuple, Any, Dict


def generate_simple(low: int, high: int, h: int, w: int) -> np.ndarray:
    """
    Function that creates a rectangular image with dimensios of h and w and values randomly chosen between low and high.

    Parameters
    ----------
    low: int
        Lower intensity value.
    high: int
        Higher intensity value.
    h: int
        Image heigth in pixels.
    w: int 
        Image width in pixels.

    Returns
    ----------
    image: np.ndarray
        Rectangular image with dimensions h and w and values between high and low.
    """
    image = np.ndarray((h, w))
    for i in range(h):
        for j in range(w):
            image[i, j] = np.random.randint(low, high)
    return image


def generate_reflections(
    image: np.ndarray, n_points: int, h: int, w: int
) -> np.ndarray:
    """
    Function that creates n_points reflections in an input image between the rectangular region with dimensios of h and w.

    Parameters
    ----------
    image: np.ndarray
        Image in which reflections will be generated.
    n_points: int
        Number of reflections.
    h: int
        Heigth in pixels for rectangular region in which reflections will be generated.
    w: int 
        Width in pixels for rectangular region in which reflections will be generated.

    Returns
    ----------
    image: np.ndarray
        Image with reflections.
    """

    index_x = np.arange(0, w)
    index_y = np.arange(0, h)
    row = np.random.choice(index_y, (n_points, 1))
    column = np.random.choice(index_x, (n_points, 1))
    for i in range(n_points):
        image[
            int(row[i] - 1) : int(row[i] + 1), int(column[i] - 1) : int(column[i] + 1)
        ] = np.random.randint(100, 250)

    return image


def create_circular_mask(
    h: int, w: int, center: List[int] = None, radius: int = None
) -> np.ndarray:
    """
    Function that creates a circular mask for an image with dimensions w x h. The circular mask is centered in center and has a radius of radius in pixels.

    Parameters
    ----------
    h: int
        Heigth in pixels for rectangular region in which reflections will be generated.
    w: int 
        Width in pixels for rectangular region in which reflections will be generated.
    center: List[int]
        Circular mask center.
    radius: int
        Circular mask radius.

    Returns
    mask: np.ndarray
        Circular mask boolean array.
    """

    if center is None:  # use the middle of the image
        center = (int(w / 2), int(h / 2))
    if radius is None:  # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], w - center[0], h - center[1])

    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)

    mask = dist_from_center <= radius
    return mask


def generate_image(
    h: int, w: int, r_in: int, r_out: int, center: List[int]
) -> np.ndarray:
    """
    Function that creates an artificial diffraction pattern with dimensios of w x h and background signal defined by r_out, r_in and center.

    Parameters
    ----------
    h: int
        Image heigth in pixels.
    w: int 
        Image width in pixels.
    r_in: int
        Inner radius of lower background signal.
    r_out: int
        Outer radius of higher background signal.
    center: List[int]
        Center of the background signal.

    Returns
    ----------
    image: np.ndarray
        Artificial diffraction pattern.
    """

    image = generate_simple(0, 3, h, w)
    signal_background = generate_simple(0, 6, h=h, w=w)
    mask_min = create_circular_mask(h, w, center, radius=r_in)
    mask_max = create_circular_mask(h, w, center, radius=r_out)
    masked_signal = signal_background.copy()
    masked_signal[~mask_max] = 0
    masked_signal[mask_min] = 0
    second_background = generate_simple(1, 4, h=h, w=w)
    masked_second = second_background.copy()
    masked_second[~mask_max] = 0
    composed_img = image + masked_signal + masked_second
    n_reflections = np.random.randint(250, 1000)
    sim_pattern = generate_reflections(composed_img, n_reflections, h, w)
    return sim_pattern


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        description="Generate an artificial data collection for center finding using genetic.py."
    )
    parser.add_argument(
        "-n",
        "--n_images",
        type=int,
        action="store",
        help="Number of sequential images to create.",
    )
    parser.add_argument(
        "-h_px", "--height", type=int, action="store", help="Height of images in pixels."
    )
    parser.add_argument(
        "-w_px", "--width", type=int, action="store", help="Width of images in pixels."
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
    h = args.height
    w = args.width

    index_x = np.arange(args.r_out, w - args.r_out)
    index_y = np.arange(args.r_out, h - args.r_out)

    center_pos = np.hstack(
        (
            np.random.choice(index_x, (n_images, 1)),
            np.random.choice(index_y, (n_images, 1)),
        )
    )
    gen_images = []

    for i in center_pos:
        gen_images.append(
            generate_image(h=h, w=w, r_in=args.r_in, r_out=args.r_out, center=i)
        )

    f = h5py.File(f"{args.output}/gen_images.h5", "w")
    f.create_dataset("data", data=gen_images)
    f.create_dataset("center", data=center_pos)
    f.close()

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
