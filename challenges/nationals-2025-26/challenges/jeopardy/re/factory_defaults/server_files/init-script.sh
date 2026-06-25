#!/bin/bash

./consumer &

./server &

python3 -m http.server 80  --directory ./site & 

wait -n

# Exit with the status of the process that exited first
exit $?