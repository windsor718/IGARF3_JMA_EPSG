#!/usr/bin/env python
import sys
import os
from ecmwfapi import ECMWFDataServer
import ConfigParser


###
year  = sys.argv[1].zfill(4)
mon   = sys.argv[2].zfill(2)
day   = sys.argv[3].zfill(2)
hour  = sys.argv[4].zfill(2)
eNum  = sys.argv[5].zfill(2)

###
dir   = "/dias/groups/tdjpn-01/yuta/FF/ECMWF/data/grib/"
res   = 0.5
south = -90
west  = 0
nlon  = 720
nlat  = 360

###
north = float(south) + float(res)*float(nlat)
east  = float(west) + float(res)*float(nlon)
date  = "%s%s%s" % (year,mon,day)
print north, east
###
#modify if needed.
step  = '0/to/246/by/6'
grid  = '0.50/0.50'
param = 'TP/TCC/2T/2D/10U/10V/SP'


def ctlForecast():

    server = ECMWFDataServer()
        
    server.retrieve({
        'origin'    : "ecmf", #name of forecast center
        'levtype'   : "sfc", #atmos. level type
        'number'    : "all", #the number of enwemble members, all to download all.
        'expver'    : "prod", 
        'dataset'   : "tigge", #name of the dataset 
        'step'      : step, #time step and span */to/*/by/*
        'grid'      : grid, #grid size
        'param'     : param, #short name of the parameter, please refer http://apps.ecmwf.int/codes/grib/param-db?filter=grib2
        'time'      : hour, #initial time
        'date'      : date, #date,yyyymmdd or yyyymmdd/to/yyyymmdd
        'area'      : "%s/%s/%s/%s"%(north,west,south,east), #north/west/south/east automatically adjusted by the grid size.
        'type'      : "ctl", #forecast type
        'target'    : os.path.join(dir,"ecmwf_%s%s_%s.grib2"%(date,hour,eNum))
    })



def ptbForecast():

    server = ECMWFDataServer()

    server.retrieve({
        'origin'    : "ecmf", #name of forecast center
        'levtype'   : "sfc", #atmos. level type
        'number'    : str(eNum), #the number of enwemble members, all to download all.
        'expver'    : "prod",
        'dataset'   : "tigge", #name of the dataset
        'step'      : step, #time step and span */to/*/by/*
        'grid'      : grid, #grid size
        'param'     : param, #short name of the parameter, please refer http://apps.ecmwf.int/codes/grib/param-db?filter=grib2
        'time'      : hour, #initial time
        'date'      : date, #date,yyyymmdd or yyyymmdd/to/yyyymmdd
        'area'      : "%s/%s/%s/%s"%(north,west,south,east), #north/west/south/east automatically adjusted by the grid size.
        'type'      : "pf", #forecast type
        'target'    : os.path.join(dir,"ecmwf_%s%s_%s.grib2"%(date,hour,eNum))
    })


if __name__ == "__main__":
    if eNum == "00":
        print "="*80
        print "ctl forecast"
        print "="*80
        ctlForecast()
    else:
        print "="*80
        print "perturbed forecast: %s"%eNum
        print "="*80
        ptbForecast()

