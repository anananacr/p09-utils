#!/bin/bash
LABEL=$1
ROOT=/gpfs/cfel/user/rodria/proc/p09_test/mov_lyso_0
START=$2
END=$3
RUN_FILE="run_jobs_lyso_auto_${START}_${END}.sh"

NAME=$LABEL-009

echo "#!/bin/sh" > $RUN_FILE

for i in $(seq $START 1 $END); do
    SLURMFILE="${NAME}_${i}.sh"
    echo  "sbatch $ROOT/shell/$SLURMFILE;">> $RUN_FILE
done

mv $RUN_FILE $ROOT/jobs
