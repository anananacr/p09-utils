#!/bin/bash

# Copyright © 2016-2017 Deutsches Elektronen-Synchrotron DESY,
#                       a research centre of the Helmholtz Association.
#
# Authors:
# Ana Carolina Rodrigues

LABEL=$1


### range param
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
COUNT_JOB=0
ID=0

IDFILE=${LABEL}.log

echo "s,v,c,n,t,l,id" > $IDFILE

for s in $(seq $s_min $s_step $s_max); do
    for v in $(seq $v_min $v_step $v_max); do
        for c in $(seq $c_min $c_step $c_max); do
            for n in $(seq $n_min $n_step $n_max); do
                for t in $(seq $t_min $t_step $t_max); do
                    for l in $(seq $l_min $l_step $l_max); do
                        param="${s},${v},${c},${n},${t},${l},${ID}"        
                        if [ ${ID} -ge 0 ] && [ ${ID} -lt 2401 ]
                        then
                            echo $param >> $IDFILE
                        fi
                        ID=$((ID+1))
                    done
                done
            done
        done
    done
done


