#!/bin/bash
for i in `seq 1 20`;
do
    #wget http://10.244.0.1:32580/
    wget http://$1:$2/
    sleep 1
done
