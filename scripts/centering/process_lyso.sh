#!/bin/sh

python3 process_jobs_partial.py -i /gpfs/cfel/user/rodria/proc/p09_test/mov_lyso_0/lyso_opt_0/run_0 -l /gpfs/cfel/user/rodria/proc/p09_test/mov_lyso_0/lists/lyso_opt.lst -o ../../../proc/lyso_opt_000/lyso_opt_000 -c center_list_p09.txt >output &

