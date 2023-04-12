#!/bin/sh

# Split genetic algorithm test into many jobs and submit using SLURM

# ./turbo_gen.sh folder name in root /gpfs/cfel/user/rodria/proc/p09_test/folder_name
# Make sure parameters for tests are correct in this file.

# Copyright � 2016-2017 Deutsches Elektronen-Synchrotron DESY,
#                       a research centre of the Helmholtz Association.
#
# Authors:
#      

#MAIL=ana.rodrigues@desy.de
### It will look for a ROOT/run_0/gen_images.h5 ROOT/gen_images_ref.h5
INPUT=$1
ROOT=/gpfs/cfel/user/rodria/proc/p09_test/moving_beam/${INPUT}

### fixed param
THR=1
R=0.95
GEN=60
LIM=0.616

## parameter in range r_ext
PARAM='r'
START=0.95
STEP=0.05
END=0.95
RUN=0

for i in $(seq $START $STEP $END); do

    NEXT=$((RUN+1))
    LABEL=art_run_${RUN}
    JNAME="center-p09_run_${RUN}"
    NAME="center-p09_run_${RUN}"
    SLURMFILE="${NAME}_${INPUT}.sh"

    #mkdir ${ROOT}/run_${NEXT}
    #cp ${ROOT}/run_${RUN}/gen_images.h5 ${ROOT}/run_${NEXT}/

    echo "#!/bin/sh" > $SLURMFILE
    echo >> $SLURMFILE
    echo "#SBATCH --partition=upex,cfel,cfel-cdi" >> $SLURMFILE  # Set your partition here
    echo "#SBATCH --time=14:00:00" >> $SLURMFILE
    echo "#SBATCH --nodes=1" >> $SLURMFILE
    echo >> $SLURMFILE
    echo "#SBATCH --chdir   $PWD" >> $SLURMFILE
    echo "#SBATCH --job-name  $JNAME" >> $SLURMFILE
    echo "#SBATCH --output    ${NAME}-%N-%j.out" >> $SLURMFILE
    echo "#SBATCH --error     ${NAME}-%N-%j.err" >> $SLURMFILE
    echo "#SBATCH --nice=0" >> $SLURMFILE
    #echo "#SBATCH --mail-type ALL" >> $SLURMFILE
    #echo "#SBATCH --mail-user $MAIL" >> $SLURMFILE
    echo >> $SLURMFILE

    command="python3 genetic.py -i ${ROOT}_100/../lists/${INPUT}.lst -a ${ROOT}_100/gen_images_refs.h5 -p ${PARAM} -o ${ROOT}_200/run_${RUN}/gen_images.h5"

    if [ $PARAM = 'r' ]
    then
        command="$command  -g ${GEN} -r ${i} -t ${THR} -l ${LIM}"
    elif [ $PARAM = 'l' ]
    then
        command="$command  -g ${GEN} -r ${R} -t ${THR} -l ${i}"
    elif [ $PARAM = 'g' ]
    then
        command="$command  -g ${i} -r ${R} -t ${THR} -l ${LIM}"
    elif [ $PARAM = 't' ]
    then
        command="$command  -g ${GEN} -r ${R} -t ${i} -l ${LIM}"
    fi
    
    echo $command >> $SLURMFILE

    echo "chmod a+rw $PWD" >> $SLURMFILE
    RUN=$((RUN+1))
    sbatch $SLURMFILE
    mv $SLURMFILE ../shell;

done

