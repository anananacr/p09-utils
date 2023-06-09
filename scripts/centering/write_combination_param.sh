#!/bin/bash

# Split a large indexing job into many small tasks and submit using SLURM

# ./turbo-index-uni-v3 my-files.lst 

# Copyright © 2016-2017 Deutsches Elektronen-Synchrotron DESY,
#                       a research centre of the Helmholtz Association.
#
# Authors:
#   

LABEL=$1
FOLDER=$2

ROOT=/gpfs/cfel/user/rodria/proc/p09_test/mov_sim
INPUT=${ROOT}/lists/${LABEL}.lst
ERRORDIR=${ROOT}/error_all_re

### range param
t_min=0.1
t_max=1.00
t_step=0.1

r_min=0.2
r_max=1.00
r_step=0.1

g_min=2
g_max=102
g_step=10

l_min=0
l_max=1.00
l_step=0.1

COUNT_JOB=0
ID=0

IDFILE=${LABEL}.log

echo "g,r,t,l,id" > $IDFILE

for g in $(seq $g_min $g_step $g_max); do
    for r in $(seq $r_min $r_step $r_max); do
        for t in $(seq $t_min $t_step $t_max); do
            for l in $(seq $l_min $l_step $l_max); do
                param="${g},${r},${t},${l},${ID}"        
                if [ ${ID} -ge 0 ] && [ ${ID} -lt 8800 ]
                then
                    echo $param >> $IDFILE
                fi
                ID=$((ID+1))
            done
        done
    done
done


