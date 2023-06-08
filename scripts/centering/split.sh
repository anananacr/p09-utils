#!/bin/bash

# Split a large indexing job into many small tasks and submit using SLURM

# ./turbo-index-uni-v3 my-files.lst 

# Copyright © 2016-2017 Deutsches Elektronen-Synchrotron DESY,
#                       a research centre of the Helmholtz Association.
#
# Authors:
#   2016      Steve Aplin <steve.aplin@desy.de>
#   2016-2017 Thomas White <taw@physics.org>

#SPLIT=600
SPLIT=100
LABEL=$1
FOLDER=$2

ROOT=/gpfs/cfel/user/rodria/proc/p09_test/mov_sim
INPUT=${ROOT}/lists/${LABEL}.lst
ERRORDIR=${ROOT}/error

### fixed param
#moving_beam_1
#THR=0.35
#R=0.3
#GEN=15
#LIM=0.2

#moving_beam_2
THR=0.35
R=0.3
GEN=15
LIM=0.2

#moving_beam_3
#THR=0.35
#R=0.3
#GEN=15
#LIM=0.2

#mov_sim
THR=1
R=0.98
GEN=100
LIM=0

## parameter in range r_ext
PARAM='t'
START=0.05
STEP=0.05
END=1.01
RUN=0

## split list of cbf files in short lists
split -a 3 -d -l $SPLIT $INPUT split-events-${LABEL}.lst

for i in $(seq $START $STEP $END); do

    NEXT=$((RUN+1))
    mkdir ${ROOT}/${LABEL}_${FOLDER}/run_${NEXT}
    for FILE in split-events-${LABEL}.lst*; do

        # Stream file is the output of crystfel
        OUTPUT=`echo $FILE | sed -e "s/split-events-${LABEL}.lst/gen_images_/"`
        # Job name
        NAME=`echo $FILE | sed -e "s/split-events-${LABEL}.lst/${LABEL}-/"`

        # Job number
        NUMBER=${NAME##$LABEL-}
        POS=`expr $NUMBER \* $SPLIT + 1`

        echo "$NAME (serial start $POS): $FILE  --->  $OUTPUT.h5"

        SLURMFILE="${NAME}.sh"

        echo "#!/bin/sh" > $SLURMFILE
        echo >> $SLURMFILE

        echo "#SBATCH --partition=allcpu,cfel" >> $SLURMFILE  # Set your partition here
        echo "#SBATCH --time=20:00:00" >> $SLURMFILE

        echo "#SBATCH --nodes=1" >> $SLURMFILE
        echo "#SBATCH --nice=128" >> $SLURMFILE
        echo "#SBATCH --mincpus=102" >> $SLURMFILE
        echo "#SBATCH --mem=8G" >> $SLURMFILE

    #	echo "#SBATCH  --cpu-freq=2600000" >> $SLURMFILE
        echo >> $SLURMFILE

#       echo "#SBATCH --workdir   $PWD" >> $SLURMFILE
        echo "#SBATCH --job-name  $NAME" >> $SLURMFILE
        echo "#SBATCH --output    $ERRORDIR/$NAME-%N-%j.out" >> $SLURMFILE
        echo "#SBATCH --error     $ERRORDIR/$NAME-%N-%j.err" >> $SLURMFILE
        echo >> $SLURMFILE

        echo "source /etc/profile.d/modules.sh" >> $SLURMFILE
        echo "source /home/rodria/scripts/p09/env-p09/bin/activate" >> $SLURMFILE

        echo >> $SLURMFILE

        command="python3 genetic.py -i ${FILE} -a ${ROOT}/${LABEL}_${FOLDER}/gen_images_refs.h5 -p ${PARAM} -o ${ROOT}/${LABEL}_${FOLDER}/run_${RUN}/${OUTPUT}.h5"
    
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
        sbatch $SLURMFILE
        mv $SLURMFILE ../shell
    done
    RUN=$((RUN+1))
done
