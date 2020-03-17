#!~/bin/Python-2.7.14/python
# -*- coding: utf-8 -*-

import numpy as np
from gtool import gtopen
import sys
import os
import ConfigParser
import argparse

class Gt2Bin(object):

    def __init__(self,kind):

        self.config    = "./config.ini"
        self.year      = 2000
        self.mon       = 1
        self.day       = 1
        self.hour      = 0
        self.eNum      = 0
        self.kind      = kind
    

    def setVars(self):
        ### Parse config
        self.initFile  = ConfigParser.SafeConfigParser()
        self.initFile.read(self.config)

        ### general settings
        self.srcRoot   = str(self.initFile.get("Model","outRoot"))
        self.outRoot   = str(self.initFile.get("Model","outRoot"))
        self.runName   = str(self.initFile.get("Model","runName"))

        self.prefix    = "Roff_"
        self.suffix    = "."+str(self.initFile.get("Forcing","cRes"))

        self.var       = "runoff"
        self.VAR       = "RUNOFF"

        self.gtPath    = self.srcRoot+"/"+self.runName+"/%s/%04d/%02d/%02d/%02d/e%02d/matsiro/main/" % (self.kind,self.year, self.mon, self.day, self.hour, self.eNum) +self.var
        self.outDir    = self.outRoot+"/"+self.runName+"/%s/%04d/%02d/%02d/%02d/e%02d/matsiro/main/bin/" % (self.kind,self.year, self.mon, self.day, self.hour, self.eNum)
        self.outFile   = "%s%04d%02d%02d%02d%s" % (self.prefix,self.year,self.mon,self.day,self.hour,self.suffix)
        self.outPath   = os.path.join(self.outDir,self.outFile)

        self.nx        = int(self.initFile.get("Forcing","nlon"))
        self.ny        = int(self.initFile.get("Forcing","nlat"))
        self.z         = 0
        self.Coef      = int(self.initFile.get("Forcing","tRes"))

        self.EWConvert = self.initFile.getboolean("Model","EWConvert")
        self.NSConvert = self.initFile.getboolean("Model","NSConvert")


###
    def main(self):

        print "Gt2Bin: Conversion started."
        self.setVars()

        binData = self.readGtool(self.gtPath,self.VAR,self.z,self.Coef)

        if self.NSConvert:
            binData = self.nsConvert(binData)
        if self.EWConvert:
            binData = self.ewConvert(binData)

        if os.path.exists(self.outDir) == False:
            os.makedirs(self.outDir)

        print "save the file at...\n"+self.outPath
        binData.flatten().astype(np.float32).tofile(self.outPath)
        print "Gt2Bin: Conversion end."


    def readGtool(self,gtPath,VAR,z,Coef):

        gt = gtopen(gtPath).vars[VAR][:][:,z,:,:]
        product = gt*Coef
        product[np.where(product>1e+5)] = 0 #tmp
        print "output shape: ",product.shape
        return product


    def ewConvert(self,binData):
        east = binData[:,:,0:self.nx/2]
        west = binData[:,:,self.nx/2:self.nx]
        product = np.concatenate((west,east),axis=2)
        print "EW origin converted."
        return product


    def nsConvert(self,binData):
        product = binData[:,::-1,:]
        print "NS order converted."
        return product


if __name__ == "__main__":

    config = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/FF/ECMWF/config.ini"

    parser = argparse.ArgumentParser(description="The script to convert raw binary into gtool format.")
    parser.add_argument("--config",type=str,default=config,help="path to the configuration file. Default path is set in this script.")
    parser.add_argument("year",type=int,help="simulation start year")
    parser.add_argument("month",type=int,help="simulation start month")
    parser.add_argument("day",type=int,help="simulation start day")
    parser.add_argument("hour",type=int,help="simulation start hour")
    parser.add_argument("eNum",type=int,help="ensemble member")
    args = parser.parse_args()

    chunk = Gt2Bin("Forecast")

    chunk.config = args.config
    chunk.year = args.year
    chunk.mon  = args.month
    chunk.day  = args.day
    chunk.hour = args.hour
    chunk.eNum = args.eNum

    chunk.main()
