#!/bin/sh

python3 ../centering/process_jobs_partial.py -i /gpfs/cfel/user/rodria/proc/p09_test/mov_lyso_0/lyso_auto_0/run_0 -l /gpfs/cfel/user/rodria/proc/p09_test/mov_lyso_0/lists/lyso_auto.lst -o ../../../proc/lyso_auto_000/lyso_auto_000 -c center_list_p09.txt >output &

