#!/bin/bash
#PBS -j oe
#PBS -o /data21/yuta/FP/src/MSM/batch/moveLogs.log

cd $PBS_O_WORKDIR
. ./Modelinfo.txt
. $config

if [ ! -e ./simErr.txt ];then
    sleep 1m
fi

sleep 30s

if [ $mon -lt 10 ]; then
    m=0$mon
else
    m=$mon
fi
if [ $day -lt 10 ]; then
    d=0$day
else
    d=$day
fi
if [ $hour -lt 10 ]; then
    h=0$hour
else
    h=$hour
fi

chmod 644 ./dataPrcLog.txt
chmod 644 ./dataPrcErr.txt
chmod 644 ./simLog.txt
chmod 644 ./simErr.txt

dir=${outRoot}${runName}/${year}/${m}/${d}/${h}/

mv ./Modelinfo.txt ${dir}Modelinfo.txt
mv ./dataPrcLog.txt ${dir}dataPrcLog.txt
mv ./dataPrcErr.txt ${dir}dataPrcErr.txt
mv ./simLog.txt ${dir}simLog.txt
mv ./simErr.txt ${dir}simErr.txt
