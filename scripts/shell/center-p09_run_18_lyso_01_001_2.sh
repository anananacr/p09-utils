#!/bin/sh

#SBATCH --partition=upex
#SBATCH --time=16:00:00
#SBATCH --nodes=1

#SBATCH --chdir   /home/rodria/scripts/p09/p09-utils/scripts/centering
#SBATCH --job-name  center-p09_run_18
#SBATCH --output    center-p09_run_18-%N-%j.out
#SBATCH --error     center-p09_run_18-%N-%j.err
#SBATCH --nice=0

python3 genetic.py -i /gpfs/cfel/user/rodria/proc/p09_test/moving_beam/lyso_01_001_2/run_18/gen_images.h5 -a /gpfs/cfel/user/rodria/proc/p09_test/moving_beam/lyso_01_001_2/gen_images_refs.h5 -p g -g 95 -r 0.95 -t 1 -l 0
chmod a+rw /home/rodria/scripts/p09/p09-utils/scripts/centering
