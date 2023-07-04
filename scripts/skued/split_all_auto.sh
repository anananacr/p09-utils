#!/bin/bash

# Split a large indexing job into many small tasks and submit using SLURM

# ./turbo-index-uni-v3 my-files.lst 

# Copyright © 2016-2017 Deutsches Elektronen-Synchrotron DESY,
#                       a research centre of the Helmholtz Association.
#
# Authors:
#   

#SPLIT=600
SPLIT=100
LABEL=$1
FOLDER=$2

ROOT=/gpfs/cfel/user/rodria/proc/p09_test/mov_lyso_0
INPUT=${ROOT}/lists/${LABEL}.lst
ERRORDIR=${ROOT}/error

### range param
#bragg spots
b=0

##autocenter
a=0

## threshold
t_min=2
t_max=21
t_step=2

s_min=2
s_max=4
s_step=0.5

c_min=1
c_max=3
c_step=1

l_min=2
l_max=5
l_step=1

n_min=1
n_max=4
n_step=1

v_min=500
v_max=10000
v_step=1000

COUNT=0
COUNT_JOB=0
## split list of cbf files in short lists
split -a 3 -d -l $SPLIT $INPUT split-events-${LABEL}.lst
ID=0
FILE=split-events-${LABEL}.lst000
# Stream file is the output of crystfel
OUTPUT=`echo $FILE | sed -e "s/split-events-${LABEL}.lst/gen_images_/"`
# Job name
NAME=`echo $FILE | sed -e "s/split-events-${LABEL}.lst/${LABEL}-/"`

# Job number
NUMBER=${NAME##$LABEL-}
POS=`expr $NUMBER \* $SPLIT + 1`

echo "$NAME (serial start ${COUNT_JOB})"

SLURMFILE="${NAME}_${COUNT_JOB}.sh"

echo "#!/bin/sh" > $SLURMFILE
echo >> $SLURMFILE

echo "#SBATCH --partition=allcpu,upex" >> $SLURMFILE  # Set your partition here
echo "#SBATCH --time=1-23:00:00" >> $SLURMFILE
echo "#SBATCH --requeue" >> $SLURMFILE

echo "#SBATCH --nodes=1" >> $SLURMFILE
echo "#SBATCH --nice=128" >> $SLURMFILE
echo "#SBATCH --mincpus=102" >> $SLURMFILE
echo "#SBATCH --mem=8G" >> $SLURMFILE
#	echo "#SBATCH  --cpu-freq=2600000" >> $SLURMFILE
echo >> $SLURMFILE

#echo "#SBATCH --workdir   $PWD" >> $SLURMFILE
echo "#SBATCH --job-name  $NAME-%N-%j" >> $SLURMFILE
echo "#SBATCH --output    $ERRORDIR/${NAME}_${COUNT_JOB}-%N-%j.out" >> $SLURMFILE
echo "#SBATCH --error     $ERRORDIR/${NAME}_${COUNT_JOB}-%N-%j.err" >> $SLURMFILE
echo >> $SLURMFILE

echo "source /etc/profile.d/modules.sh" >> $SLURMFILE
echo "module load maxwell python/3.10" >> $SLURMFILE
echo "source /home/rodria/software/env-skiued/bin/activate" >> $SLURMFILE
echo >> $SLURMFILE

RUN_FILE="run_jobs_lyso_auto.sh"
echo "#!/bin/sh" > $RUN_FILE
for s in $(seq $s_min $s_step $s_max); do
    for v in $(seq $v_min $v_step $v_max); do
        for c in $(seq $c_min $c_step $c_max); do
            for n in $(seq $n_min $n_step $n_max); do
                for t in $(seq $t_min $t_step $t_max); do
                    for l in $(seq $l_min $l_step $l_max); do
                        for FILE in split-events-${LABEL}.lst*; do

                            # Stream file is the output of crystfel
                            OUTPUT=`echo $FILE | sed -e "s/split-events-${LABEL}.lst/gen_images_/"`

                            command="./calculate_center.py -i ${FILE} -m ${ROOT}/lists/mask_${LABEL}.lst -o ${ROOT}/${LABEL}_${FOLDER}/run_0/${OUTPUT}_${ID}.h5"            
                            command="$command  -b ${b} -t ${t} -s ${s} -c ${c} -l ${l} -n ${n} -v ${v} -a ${a} -center center_list_p09.txt -id ${ID}"
                            echo $command >> $SLURMFILE
                            COUNT=$((COUNT+1))
                            if [ $COUNT -eq 100 ]
                            then
                                
                                echo "chmod a+rw $PWD" >> $SLURMFILE
                                if [ ${COUNT_JOB} -ge 0 ] && [ ${COUNT_JOB} -lt 200 ]
                                then
                                    
                                    echo  "sbatch $ROOT/shell/$SLURMFILE;">> $RUN_FILE
                                    sbatch --test-only $SLURMFILE
                                    #sbatch $SLURMFILE
                                    mv $SLURMFILE $ROOT/shell
                                else
                                    rm $SLURMFILE
                                fi
                                
                                
                                COUNT=0
                                COUNT_JOB=$((COUNT_JOB+1))
                                ### init next slurm file
                                # Stream file is the output of crystfel
                                OUTPUT=`echo $FILE | sed -e "s/split-events-${LABEL}.lst/gen_images_/"`
                                # Job name
                                NAME=`echo $FILE | sed -e "s/split-events-${LABEL}.lst/${LABEL}-/"`

                                # Job number
                                NUMBER=${NAME##$LABEL-}
                                POS=`expr $NUMBER \* $SPLIT + 1`

                                echo "$NAME (serial start ${COUNT_JOB})"

                                SLURMFILE="${NAME}_${COUNT_JOB}.sh"

                                echo "#!/bin/sh" > $SLURMFILE
                                echo >> $SLURMFILE

                                echo "#SBATCH --partition=allcpu,upex" >> $SLURMFILE  # Set your partition here
                                echo "#SBATCH --time=1-23:00:00" >> $SLURMFILE
                                echo "#SBATCH --requeue" >> $SLURMFILE

                                echo "#SBATCH --nodes=1" >> $SLURMFILE
                                echo "#SBATCH --nice=128" >> $SLURMFILE
                                echo "#SBATCH --mincpus=102" >> $SLURMFILE
                                echo "#SBATCH --mem=8G" >> $SLURMFILE

                                #	echo "#SBATCH  --cpu-freq=2600000" >> $SLURMFILE
                                echo >> $SLURMFILE

                                #echo "#SBATCH --workdir   $PWD" >> $SLURMFILE
                                echo "#SBATCH --job-name  $NAME" >> $SLURMFILE
                                echo "#SBATCH --output    $ERRORDIR/${NAME}_${COUNT_JOB}-%N-%j.out" >> $SLURMFILE
                                echo "#SBATCH --error     $ERRORDIR/${NAME}_${COUNT_JOB}-%N-%j.err" >> $SLURMFILE
                                
                                echo >> $SLURMFILE

                                echo "source /etc/profile.d/modules.sh" >> $SLURMFILE
                                echo "module load maxwell python/3.10" >> $SLURMFILE
                                echo "source /home/rodria/software/env-skiued/bin/activate" >> $SLURMFILE
                                echo >> $SLURMFILE

                            fi
                        done
                        ID=$((ID+1))
                    done
                done
            done
        done
    done
done
echo "chmod a+rw $PWD" >> $SLURMFILE
#sbatch --test-only $SLURMFILE
#sbatch $SLURMFILE
mv $SLURMFILE $ROOT/shell/

