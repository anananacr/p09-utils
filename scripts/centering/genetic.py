from typing import List, Optional, Callable, Tuple, Any, Dict
import numpy as np
import argparse
import h5py
import os
from multiprocessing import Pool
import matplotlib.pyplot as plt
import fabio
import math
import pandas as pd
from force_center import bring_center_to_point
from datetime import datetime

Genome = Dict[np.ndarray, int]
Population = List[Genome]
FitnessFunc = Callable[[Genome], int]
PopulateFunc = Callable[[], Population]
CrossoverFunc = Callable[[Genome, Genome], Tuple[Genome, Genome]]


def fitness_func(genome: Genome) -> float:
    """
    Function that evaluates the fitness of a Genome, in this case an artificial image with its known center dislocated, with the observed data.

    Parameters
    ----------
    genome: Genome
        An individual of a population, an artificial image with its known center dislocated to up, down, left and right by steps.

    Returns
    ----------
    score: float
        Score of the individual.
    """
    a = genome["data"]
    b = raw_data[genome["obs_data_index"]]
    score = calc_distance(a, b)

    return -1 * score


def generate_genome(
    data: np.ndarray, obs_data_index: int, direction: int, step: int, offset: List[int]
) -> Genome:
    """
    Function that generates a Genome, in this case an artificial image with its known center dislocated to a direction (up, down, left and right) by steps.

    Parameters
    ----------
    data: np.ndarray
        An artificial image with a known center.
    obs_data_index: int
        Observed data index on H5 file for multiprocessing purpose.
    direction: int
        Direction in which data will be dislocated (0: no movement, 1: right 2: up 3: left, 4: down).
    step: int
        Number of pixels to shift the image.
    offset: List[int]
        Center value best aproximation obtained from last generation.
    Returns
    ----------
    genome: Genome
        An individual of a population, an artificial image with its known center dislocated to a direction by step.
    """
    h = data.shape[0]
    w = data.shape[1]
    center = [int(w / 2), int(h / 2)]
    movement = [[0, 0], [step, 0], [0, step], [-1 * step, 0], [0, -1 * step]]
    transformation = movement[direction]

    new_center = np.add.reduce([center, transformation, offset])
    # print('new_center',new_center)
    moved_data, shift = bring_center_to_point(data, point=new_center)
    return {
        "data": moved_data,
        "direction": direction,
        "center": new_center,
        "step": step,
        "offset": offset,
        "obs_data_index": obs_data_index,
    }


def generate_population(
    data: np.ndarray, obs_data_index: int, step: int = None, offset: List[int] = [0, 0]
) -> Population:
    """
    Function that generates a population, in this case collection of an artificial image with its known center dislocated to all directions (no movement, up, down, left and right) by steps.

    Parameters
    ----------
    data: np.ndarray
        An artificial image with a known center.
    obs_data_index: int
        Observed data index on H5 file for multiprocessing purpose.
    step: int
        Number of pixels to shift the image.
    offset: List[int]
        Center value best aproximation obtained from last generation.
    Returns
    ----------
    population: Population
        Collection of individuals, an artificial image with its known center dislocated to all directions by step.
    """
    if step == None:
        h = data.shape[0]
        w = data.shape[1]
        step = min(int(w / 4), int(h / 4))
    return [
        generate_genome(data, obs_data_index, direction, step, offset)
        for direction in range(5)
    ]


def combined_movement(a: Genome, b: Genome) -> Genome:
    data = a["data"]
    obs_data_index = a["obs_data_index"]
    offset = a["offset"]
    step = b["step"]
    movement = [[0, 0], [step, 0], [0, step], [-1 * step, 0], [0, -1 * step]]
    direction = 5
    transformation = movement[b["direction"]]
    h = data.shape[0]
    w = data.shape[1]
    center = [int(w / 2), int(h / 2)]

    new_center = np.add.reduce([center, transformation, offset])
    # print('combined new_center', new_center)
    moved_data, shift = bring_center_to_point(data, point=new_center)

    return {
        "data": moved_data,
        "direction": direction,
        "center": new_center,
        "step": step,
        "offset": offset,
        "obs_data_index": obs_data_index,
    }


# def population_fitness(population: Population, fitness_func: FitnessFunc) -> int:


def calc_distance(a, b):

    distance_map = a.copy()
    for i in range(distance_map.shape[0]):
        for j in range(distance_map.shape[1]):

            val = 2 * (a[i, j] - b[i, j]) / (a[i, j] + b[i, j])
            # val=(a[i,j]-b[i,j])/(a[i,j])
            distance_map[i, j] = val

    distance_map = np.nan_to_num(distance_map)
    distance_map[np.where(distance_map >= threshold)] = 0
    distance_map[np.where(distance_map <= -1 * threshold)] = 0
    mean = 0
    count = 0
    for i in range(distance_map.shape[0]):
        for j in range(distance_map.shape[1]):
            if distance_map[i, j] != 0:
                mean += (distance_map[i, j]) ** 2
                count += 1
    mean /= count
    mean = math.sqrt(mean)

    return mean


def selection_pair(population: Population, fitness_func: FitnessFunc) -> Population:
    return choices(
        population=population, weights=[fitness_func(gene) for gene in population], k=2
    )


def sort_population(population: Population, fitness_func: FitnessFunc) -> Population:

    return sorted(population, key=fitness_func, reverse=True)


def run_evolution(
    data: np.ndarray,
    obs_data_index: int,
    populate_func: PopulateFunc,
    fitness_func: FitnessFunc,
    fitness_limit: float,
    generation_limit: int = 100,
    r_ext: float = 0.5,
    crossover_func: CrossoverFunc = combined_movement,
) -> Tuple[Population, int]:

    population = populate_func(data, obs_data_index)

    h = data.shape[0]
    w = data.shape[1]
    center_track = [int(w / 2), int(h / 2)]
    # print(center_track)
    movement = [[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1]]
    acc_transf = [0, 0]
    for i in range(generation_limit):
        print(i, center_track)
        population = sort_population(population, fitness_func)

        if fitness_func(population[0]) >= fitness_limit:
            center = center_track
            break

        parents = population[0:2]

        offspring = crossover_func(parents[0], parents[1])

        transformation = []
        if fitness_func(offspring) > fitness_func(population[0]):
            actual_step = offspring["step"]
            next_step = round(actual_step * r_ext)

            transformation_1 = [
                i * actual_step for i in movement[parents[0]["direction"]]
            ]
            transformation_2 = [
                i * actual_step for i in movement[parents[1]["direction"]]
            ]
            transformation = np.add.reduce([transformation_1, transformation_2])
            center_track = np.add.reduce([center_track, transformation])
            acc_transf = np.add.reduce([acc_transf, transformation])
            next_generation = populate_func(
                data, obs_data_index, step=next_step, offset=acc_transf
            )
            # print('transformation', transformation, 'gen', i)
            # print(f"Best for next: {offspring['center']}, {offspring['direction']},{offspring['step']}")
            print("fit_val", fitness_func(population[0]))
        else:
            actual_step = parents[0]["step"]
            next_step = round(actual_step * r_ext)
            transformation = [
                i * actual_step for i in movement[parents[0]["direction"]]
            ]
            center_track = np.add.reduce([center_track, transformation])
            acc_transf = np.add.reduce([acc_transf, transformation])
            next_generation = populate_func(
                data, obs_data_index, step=next_step, offset=acc_transf
            )

            # print('transformation', transformation, 'gen', i)
            # print(f"Best for next: {parents[0]['center']}, {parents[0]['direction']},{parents[0]['step']}")
            print("fit_val", fitness_func(population[0]))

        # print(f"Best center approx: {center_track}")

        population = next_generation
        center = center_track
    return i, center


def calc_center_genetic(raw_data_index: int) -> List[Any]:
    obs_data = raw_data[raw_data_index]
    index = ref_index[0]

    start = datetime.now()
    max_gen, calc_center = run_evolution(
        art_data[index],
        raw_data_index,
        generate_population,
        fitness_func,
        generation_limit=args.generations,
        r_ext=args.r_ext,
        fitness_limit=-1 * args.lim,
    )
    end = datetime.now()

    time_delta = end - start
    proc_time = str(time_delta)
    center = calc_center
    return [raw_data_index, proc_time, max_gen, center[0], center[1]]


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        description="Find center of lysozyme patterns in CBF images from Pilatus 2M at P09-PETRA."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        action="store",
        help="path to the list file of input data.",
    )

    parser.add_argument(
        "-a",
        "--art",
        type=str,
        action="store",
        help="path to the artificial centered images file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        action="store",
        help="path to the output centered image file",
    )
    parser.add_argument(
        "-g",
        "--generations",
        type=int,
        action="store",
        help="max number of generations",
    )
    parser.add_argument(
        "-r",
        "--r_ext",
        type=float,
        action="store",
        help="extintion rate of steps in each generation.",
    )
    parser.add_argument(
        "-t",
        "--thr",
        type=float,
        action="store",
        help="threshold cut in difference map",
    )
    parser.add_argument(
        "-l",
        "--lim",
        type=float,
        default=0.0,
        action="store",
        help="path to the output H5 file",
    )
    parser.add_argument(
        "-id",
        "--id_param",
        type=int,
        default=0,
        action="store",
        help="path to the output HDF5 file",
    )
    parser.add_argument(
        "-p", "--param", type=str, action="store", help="adjusting parameter label"
    )
    global args
    args = parser.parse_args(raw_args)

    file_name = f"{args.input}"

    f = h5py.File(f"{args.art}", "r")
    global art_data
    art_data = np.array(f["data"])
    f.close()
    n_images = art_data.shape[0]

    global raw_data

    file_label, file_extension = os.path.splitext(args.input)

    if file_extension[:4] == ".lst":
        gen_images = []
        center_pos = []

        ## open list file
        f = open(args.input, "r")
        files = f.readlines()
        total_frames = len(files)
        f.close()
        ## choose an image from list
        image_index = np.random.choice(total_frames, n_images)
        image_id = []
        # for i in image_index:
        for i in range(total_frames):
            file_name = files[i][:-1]
            data = np.array(fabio.open(f"{file_name}").data)
            image_id.append(file_name)
            gen_images.append(data)
        raw_data = np.array(gen_images)

    elif file_extension == ".h5":
        f = h5py.File(f"{args.input}", "r")
        raw_data = np.array(f["data"])[:]
        f.close()

    global threshold
    threshold = args.thr

    center = []
    proc_time = []

    g = h5py.File(f"{args.art}", "r")
    global ref_index
    # ref_index = np.array(g["ref_index"])[:]
    ref_index = [0]
    g.close()

    raw_data_index = np.arange(0, raw_data.shape[0])
    dimensions = [raw_data.shape[2], raw_data.shape[1]]

    with Pool() as p:
        # with Pool(total_frames+2) as p:
        result = p.map(calc_center_genetic, raw_data_index)

    df = pd.DataFrame(
        result, columns=["image_number", "proc_time", "max_gen", "center_x", "center_y"]
    )
    df.sort_values(by="image_number")
    print(df.proc_time)

    param_summary = [
        ["r_ext", f"{args.r_ext}"],
        ["g", f"{args.generations}"],
        ["thr", f"{args.thr}"],
        ["fitness_limit", f"{args.lim}"],
        ["id_param", f"{args.id_param}"],
        ["opt_param", f"{args.param}"],
        ["max_generations", f"{df.max_gen.median()}"],
    ]

    if file_extension[:4] == ".lst":
        f = h5py.File(f"{args.output}", "w")
        f.create_dataset("id", data=image_id)
        if args.x_t is not None and args.y_t is not None:
            f.create_dataset("center", data=center_pos)
        f.create_dataset("center_calc", data=df[["center_x", "center_y"]])
        f.create_dataset("processing_time", data=list(df.proc_time))
        f.create_dataset("ref_index", data=ref_index)
        f.create_dataset("dimensions", data=dimensions)

    elif file_extension == ".h5":
        f = h5py.File(f"{args.output}", "a")
        f.create_dataset("center_calc", data=df[["center_x", "center_y"]])
        f.create_dataset("processing_time", data=list(df.proc_time))
        f.create_dataset("ref_index", data=ref_index)

    if args.param == "r":
        f.create_dataset("param_value_opt", data=args.r_ext)
    elif args.param == "t":
        f.create_dataset("param_value_opt", data=args.thr)
    elif args.param == "g":
        f.create_dataset("param_value_opt", data=args.generations)
    elif args.param == "l":
        f.create_dataset("param_value_opt", data=args.lim)
    elif args.param == "id":
        f.create_dataset("param_value_opt", data=args.id_param)

    f.create_dataset("genetic_param", data=param_summary)
    f.close()


if __name__ == "__main__":
    main()
