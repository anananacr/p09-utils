
#python3 center.py -i /asap3/petra3/gpfs/p09/2022/data/11016566/raw/Ana/lyso01/rotational_001/lyso01_001_00002.cbf -m mask_2.h5 -x1 830 -x2 850 -y1 980 -y2 1000 -o results/lyso_01_01 
#!/bin/sh

# Split a large centering job into many small tasks and submit using SLURM

# ./turbo-center lyso_01 rotational_001 x1 x2 y1 y2
# Copyright � 2016-2017 Deutsches Elektronen-Synchrotron DESY,
#                       a research centre of the Helmholtz Association.
#
# Authors:
#      

MAIL=ana.rodrigues@desy.de
CRYSTAL=$1
ROT=$2
INPUT=lyso${CRYSTAL}/rotational_0${ROT}/lyso${CRYSTAL}_0${ROT}_01800.cbf
MASK=../mask_sym_stop/mask_${CRYSTAL}_${ROT}.h5
ROOT=/asap3/petra3/gpfs/p09/2022/data/11016566/raw/Ana

START_X=$3
END_X=$4
START_Y=$5
END_Y=$6
OUTPUT=/gpfs/cfel/user/rodria/proc/p09_test/lyso_${CRYSTAL}_${ROT}_sym
LABEL=lyso_${CRYSTAL}_${ROT}_sym
JNAME='center-p09'
NAME='center-p09'
SLURMFILE="${NAME}_${LABEL}.sh"

echo "#!/bin/sh" > $SLURMFILE
echo >> $SLURMFILE
echo "#SBATCH --partition=cfel" >> $SLURMFILE  # Set your partition here
echo "#SBATCH --time=10:00:00" >> $SLURMFILE
echo "#SBATCH --nodes=1" >> $SLURMFILE
echo >> $SLURMFILE
echo "#SBATCH --chdir   $PWD" >> $SLURMFILE
echo "#SBATCH --job-name  $JNAME" >> $SLURMFILE
echo "#SBATCH --output    ${NAME}-${LABEL}-%N-%j.out" >> $SLURMFILE
echo "#SBATCH --error     ${NAME}-${LABEL}-%N-%j.err" >> $SLURMFILE
echo "#SBATCH --nice=0" >> $SLURMFILE
echo "#SBATCH --mail-type ALL" >> $SLURMFILE
echo "#SBATCH --mail-user $MAIL" >> $SLURMFILE
echo >> $SLURMFILE

command="python3 center.py -i ${ROOT}/${INPUT} -m ${MASK} -x1 ${START_X} -x2 ${END_X} -y1 ${START_Y} -y2 ${END_Y} -o ${OUTPUT} -l ${LABEL}"

echo $command >> $SLURMFILE

echo "chmod a+rw $PWD" >> $SLURMFILE

sbatch $SLURMFILE
mv $SLURMFILE ../shell;
