#!/bin/sh

#SBATCH --partition=upex,cfel,cfel-cdi
#SBATCH --time=14:00:00
#SBATCH --nodes=1

#SBATCH --chdir   /home/rodria/scripts/p09/p09-utils/scripts/centering
#SBATCH --job-name  center-p09_run_0
#SBATCH --output    center-p09_run_0-%N-%j.out
#SBATCH --error     center-p09_run_0-%N-%j.err
#SBATCH --nice=0

python3 genetic.py -i /gpfs/cfel/user/rodria/proc/p09_test/moving_beam/lyso_03_004_100/../lists/lyso_03_004.lst -a /gpfs/cfel/user/rodria/proc/p09_test/moving_beam/lyso_03_004_100/gen_images_refs.h5 -p r -o /gpfs/cfel/user/rodria/proc/p09_test/moving_beam/lyso_03_004_200/run_0/gen_images.h5 -g 60 -r 0.95 -t 1 -l 0.616
chmod a+rw /home/rodria/scripts/p09/p09-utils/scripts/centering
