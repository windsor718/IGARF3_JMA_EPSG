#!/usr/env/python
# script for decode grib2 file.
# designed for internal use @ tdjpn-DIAS
# wgrib2 module by NOAA is needed for the decoding and interpolation.

import argparse
import numpy as np
import datetime
import subprocess
import sys
import os
import ConfigParser

"""
Global variables
"""
wgrib2 = "/dias/users/ishitsuka.y.u-tokyo/bin/wgrib2"



### class definition


"""
SUPER CLASS: Core modules. You may have less chances to edit this class.
"""

class DecodeGrib(object):

    """
        DecodeGrib:
            Function:
                Python API to handle grib2 datasets. Conversion to plain binary and interpolation is supported.
    """

    def __init__(self,year,mon,day,hour,eNum):
        
        #internal setting
        self.gtRoot        = "/path/to/store/gtoolFiles"
        self.nRes          = float(0.05)
        self.cRes          = str(005)
        self.nlon          = int(440)
        self.nlat          = int(500)
        self.lon0          = float(123.)
        self.lat0          = float(24.)
        self.intpFlag      = True

        self.gPath         = "/path/To/The/grib2File.bin" # grib file name to decode.
        self.wgrib2        = wgrib2 #path to wgrib2
        self.oName         = "%s_%04d%02d%02d%02d_e%02d.%s"
        self.retrieveParam = "parameterToRetrieve" # this will be the output file name
        self.vectotParam   = "list to store vector element"
        self.paramKey      = "ParameterKey" # the arg for the -match option in wgrib2. a short name of the parameter is suggested. use "" if no short name is defined (e.g., grib file contains only 1 parameter.) in the grib file.
        self.vectorKey     = "list to store vector element's key"
        self.fieldKey      = "FieldKey" # the arg for the -match option in wgrib2 for the vector interpolation.
        self.intpKind      = "bilinear" #bilinear,nearest,budget

        #read from args
        self.year          = year
        self.mon           = mon
        self.day           = day
        self.hour          = hour
        self.eNum          = eNum


    def set_vals(self):

        self.dlon          = "{0:.3f}".format(self.nRes)
        self.dlat          = "{0:.3f}".format(self.nRes)
        self.newWest       = "{0:.5f}".format(self.lon0 + self.nRes/2.)
        self.newSouth      = "{0:.5f}".format(self.lat0 + self.nRes/2.)


    def main(self,field):

        gFile = self.gPath.split("/")[-1]
        if self.intpFlag:
            tmpFile = os.path.join(self.gtRoot,"%s.%s"%(gFile,self.cRes))
            if field == "scalar":
                flag = self.interpAndDecode_scl(tmpFile)
            elif field == "vector":
                flag = self.interpAndDecode_vct(tmpFile)
            else:
                sys.stderr.write("KeyError: %s is not defined name of field." % (field))
                sys.exit(1)
        else:
            f            = os.path.join(self.gtRoot,fName)
            flag = self.decode(f)

        return flag


    def interpAndDecode_scl(self,tmpFile):

        notification = "start interpolation...\n\t%s interpolation" % (self.intpKind)
        print notification

        if len(self.paramKey) == 0:
            intpOption = "-set_grib_type same -new_grid_winds earth -new_grid_interpolation %s -new_grid latlon %s:%s:%s %s:%s:%s" \
                     % (str(self.intpKind),str(self.newWest), str(self.nlon), str(self.dlon), str(self.newSouth), str(self.nlat), str(self.dlat))
        else:
            intpOption = "-match %s -set_grib_type same -new_grid_winds earth -new_grid_interpolation %s -new_grid latlon %s:%s:%s %s:%s:%s" \
                     % (str(self.paramKey),str(self.intpKind),str(self.newWest), str(self.nlon), str(self.dlon), str(self.newSouth), str(self.nlat), str(self.dlat))
        #interpolation
        subprocess.call("%s %s %s %s" % (self.wgrib2, self.gPath, intpOption, tmpFile),shell=True)
        #decoding
        self.decode(tmpFile)
        
        return 0


    def interpAndDecode_vct(self,tmpFile):

        notification = "start interpolation...\n\t%s interpolation" % (self.intpKind)
        print notification

        # interpolate from all data (u/v are both required for interpolation.)
        intpOption = "-match %s -set_grib_type same -new_grid_winds earth -new_grid_interpolation %s -new_grid latlon %s:%s:%s %s:%s:%s" \
                     % (str(self.fieldKey),str(self.intpKind),str(self.newWest), str(self.nlon), str(self.dlon), str(self.newSouth), str(self.nlat), str(self.dlat))
        #interpolation
        subprocess.check_call("%s %s %s %s" % (self.wgrib2, self.gPath, intpOption, tmpFile), shell=True)
        #extraction and decode
        for idx in [0,1]:
            self.retrieveParam = self.vectorParam[idx]
            self.paramKey      = self.vectorKey[idx]
            oTmp  = "%s-%d.bin" % (tmpFile,idx)
            subprocess.check_call("%s %s -match %s -grib %s" % (str(self.wgrib2), str(tmpFile), str(self.paramKey), str(oTmp)), shell=True)
            #show results
            subprocess.check_call("%s %s %s" % (self.wgrib2, "-V", oTmp),shell=True)
            #decode
            self.decode(oTmp)

        return 0


    def decode(self,f):

        oPath = os.path.join(self.gtRoot,self.oName % (self.retrieveParam,self.year,self.mon,self.day,self.hour,self.eNum,self.cRes))
        oTmp  = oPath + ".bin"
        decodeOption = "-no_header -bin %s" % (oTmp)
        subprocess.call("%s %s %s" %(self.wgrib2, f, decodeOption),shell=True)
        subprocess.call("cat %s >> %s" % (oTmp,oPath),shell=True)

        return 0


    def remove(self):

        for File in self.rmFiles:
            print "rm %s" % (File)
            os.system("rm %s" % (File))

        return 0


"""
CHILD CLASS: Here you need to create your own classes in reference to your datasets.
"""
class JMA_EPSG(DecodeGrib):

    def __init__(self,config,year,mon,day,hour,eNum):
        # Initialization in reference to the super class
        DecodeGrib.__init__(self,year,mon,day,hour,eNum)

        # Read a config file
        initFile  = ConfigParser.SafeConfigParser()
        initFile.read(config)

        # Read from config
        self.gtRoot        = str(initFile.get("Forcing","gtRoot"))
        self.nRes          = float(initFile.get("Forcing","nRes"))
        self.cRes          = str(initFile.get("Forcing","cRes"))
        self.nlon          = int(initFile.get("Forcing","nlon"))
        self.nlat          = int(initFile.get("Forcing","nlat"))
        self.lon0          = float(initFile.get("Forcing","lon0"))
        self.lat0          = float(initFile.get("Forcing","lat0"))
        self.intpFlag      = initFile.getboolean("Forcing","interp")

        # parameters to retrieve [scalar]
        self.msmParaSets_scl = [("tp",":APCP"),("gpm",":HGT"),("t2",":TMP"),("rh",":RH"),("tcdc",":TCDC"),("prmsl",":PRMSL"),("vgrd",":VGRD:10"),("ugrd",":UGRD:10")]
        # parameters to retriebe [vector]
        self.msmParaSets_vct = [] # [[arg1,arg2,arg3],...,[arg1,arg2,arg3]]
        
        """
             arg1: string. keys to extract vector fields which is used as the args of -match option in wgrib2.
             arg2: tuple. the paramter your want. ("parameterName","parameterShortName (-match key)")
             arg3: tuple. the parameter you want. ("parameterName","parameterShortName (-match key)")
        """
        
        # set up diagnostic variables
        self.set_vals()


        # clean up fies.
        self.rmFiles = [os.path.join(self.gtRoot,"jma_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"tp_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"rh_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"t2_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"gpm_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"ugrd_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"vgrd_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"tcdc_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum))]
        self.remove()


    def decodeJMA_EPSG(self):
        print "*"*80
        print "jma_epsg grib2 Decoder:"
        ft_init = ["00"]
        ft_tail = ["08"]
        for ft0, ft1 in zip(ft_init, ft_tail):
            self.gPath = self.definePathToGrib(ft0, ft1)
            for para in self.msmParaSets_scl:
                self.retrieveParam = para[0]
                self.paramKey      = para[1]
                self.main("scalar")
            for field in self.msmParaSets_vct:
                self.vectorParam   = [field[1][0],field[2][0]]
                self.vectorKey     = [field[1][1],field[2][1]]
                self.fieldKey      = field[0]
                print self.vectorParam,self.paramKey,self.fieldKey
                self.main("vector")

            subprocess.check_call(["gzip",self.gPath])

        print "Finishing grib2 Decoder..."
        print "*"*80


    def definePathToGrib(self, ft0, ft1):
        """
        any required processes (e.g., downloading) to define the path to the grib file to decode.
        """
        gDir   = "/dias/data/gpv/%04d%02d/%04d%02d%02d/" % (self.year, self.mon, self.year, self.mon, seld.day)
        sPath  = os.path.join(gDir,"Z__C_RJTD_%04d%02d%02d%02d0000_EPSW_GPV_Rgl_FD%s_%s_grib2.bin") % (self.year,self.mon,self.day,self.hour,ft0,ft1)

        for e in range(eNum):
            # split a grib file to a grib file for one ensemble
            ePath = ""
            pass

            return ePath

class ECMWF(DecodeGrib):

    def __init__(self,config,year,mon,day,hour,eNum):
        # Initialization in reference to the super class
        DecodeGrib.__init__(self,year,mon,day,hour,eNum)

        # Read a config file
        initFile  = ConfigParser.SafeConfigParser()
        initFile.read(config)

        # Read from config
        self.gtRoot        = str(initFile.get("Forcing","gtRoot"))
        self.nRes          = float(initFile.get("Forcing","nRes"))
        self.cRes          = str(initFile.get("Forcing","cRes"))
        self.nlon          = int(initFile.get("Forcing","nlon"))
        self.nlat          = int(initFile.get("Forcing","nlat"))
        self.lon0          = float(initFile.get("Forcing","lon0"))
        self.lat0          = float(initFile.get("Forcing","lat0"))
        self.intpFlag      = initFile.getboolean("Forcing","interp")

        # parameters to retrieve [scalar]
        self.msmParaSets_scl = [("tp","TPRATE"),("sp","PRES"),("t2","TMP"),("d2","DPT"),("tcdc","TCDC")]
        # parameters to retriebe [vector]
        self.msmParaSets_vct = [["\":(UGRD|VGRD):10\"",("vgrd",":VGRD:10"),("ugrd",":UGRD:10")]] # [[arg1,arg2,arg3],...,[arg1,arg2,arg3]]
        
        """
             arg1: string. keys to extract vector fields which is used as the args of -match option in wgrib2.
             arg2: tuple. the paramter your want. ("parameterName","parameterShortName (-match key)")
             arg3: tuple. the parameter you want. ("parameterName","parameterShortName (-match key)")
        """
        
        # set up diagnostic variables
        self.set_vals()


        # clean up fies.
        self.rmFiles = [os.path.join(self.gtRoot,"ecmwf_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"tp_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"sp_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"t2_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"d2_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"ugrd_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"vgrd_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum)),\
        os.path.join(self.gtRoot,"tcdc_%04d%02d%02d%02d_e%02d*"%(self.year,self.mon,self.day,self.hour,self.eNum))]
        self.remove()


    def decodeECMWF(self):
        print "*"*80
        print "ecmwf grib2 Decoder:"

        self.gPath = self.definePathToGrib()
        for para in self.msmParaSets_scl:
            self.retrieveParam = para[0]
            self.paramKey      = para[1]
            self.main("scalar")
        for field in self.msmParaSets_vct:
            self.vectorParam   = [field[1][0],field[2][0]]
            self.vectorKey     = [field[1][1],field[2][1]]
            self.fieldKey      = field[0]
            print self.vectorParam,self.paramKey,self.fieldKey
            self.main("vector")

        subprocess.check_call(["gzip",self.gPath])

        print "Finishing grib2 Decoder..."
        print "*"*80


    def definePathToGrib(self):
        """
        any required processes (e.g., downloading) to define the path to the grib file to decode.
        """

        gDir   = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/FF/ECMWF/data/grib/"
        oPath  = os.path.join(gDir,"ecmwf_%04d%02d%02d%02d_%02d.grib2") % (self.year,self.mon,self.day,self.hour,self.eNum)

        if os.path.exists(oPath+".gz"):
            print "File Found."
            subprocess.check_call(["gzip","-d",oPath+".gz"])

            return oPath

        else:
            subprocess.check_call(["python","./IO/getEcmwfData.py",str(self.year),str(self.mon),str(self.day),str(self.hour),str(self.eNum)])

            return oPath


if __name__ == "__main__":

    config = "/dias/users/ishitsuka.y.u-tokyo/tdjpn/FF/ECMWF/config.ini"
    
    parser = argparse.ArgumentParser(description="The API to decode grib2.")
    parser.add_argument("--config",type=str,default=config,help="path to the configuration file. Default path is set in this script.")
    parser.add_argument("year",type=int,help="simulation start year")
    parser.add_argument("month",type=int,help="simulation start month")
    parser.add_argument("day",type=int,help="simulation start day")
    parser.add_argument("hour",type=int,help="simulation start hour")
    parser.add_argument("eNum",type=int,default=None,help="Ensemble number")
    args = parser.parse_args()

    conf = args.config
    year = args.year
    mon  = args.month
    day  = args.day
    hour = args.hour
    eNum = args.eNum

    chunk = ECMWF(conf,year,mon,day,hour,eNum)
    chunk.decodeECMWF()
