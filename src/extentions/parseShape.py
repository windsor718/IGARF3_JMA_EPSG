from gtool import gtopen
import numpy as np
import ConfigParser
import sys
import os
import subprocess


def main(config,year,mon,day,hour):
    #Configuration
    initFile = ConfigParser.SafeConfigParser()
    initFile.read(config)

    ###
    gtRoot   =  initFile.get("Forcing","gtRoot") #gtool data root
    cRes     =  initFile.get("Forcing","cRes")

    year     =  int(year)
    mon      =  int(mon)
    day      =  int(day)
    hour     =  int(hour)

    gtPath   = os.path.join(gtRoot,cRes,"%04d/%02d/%02d/%02d"%(year,mon,day,hour),"PRCP_%04d%02d%02d%02d.gt"%(year,mon,day,hour))
    gt       = gtopen(gtPath).vars["PRCP"][:]
    tShape   = gt.shape[0]

    subprocess.call("echo tShape=%s >> ./Modelinfo.txt"%tShape,shell=True)

    return tShape
