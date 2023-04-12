#!/bin/sh

#SBATCH --partition=upex
#SBATCH --time=16:00:00
#SBATCH --nodes=1

#SBATCH --chdir   /home/rodria/scripts/p09/p09-utils/scripts/centering
#SBATCH --job-name  center-p09_run_2
#SBATCH --output    center-p09_run_2-%N-%j.out
#SBATCH --error     center-p09_run_2-%N-%j.err
#SBATCH --nice=0

python3 genetic.py -i /gpfs/cfel/user/rodria/proc/p09_test/moving_beam/lyso_01_001_1/run_2/gen_images.h5 -a /gpfs/cfel/user/rodria/proc/p09_test/moving_beam/lyso_01_001_1/gen_images_refs.h5 -p g -g 15 -r 0.65 -t 1 -l 0
chmod a+rw /home/rodria/scripts/p09/p09-utils/scripts/centering
