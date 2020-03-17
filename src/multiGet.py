from multiprocessing import Pool
import numpy as np
import time
import argparse

parser = argparse.ArgumentParser(description="The API to decode grib2.")
parser.add_argument("year",type=int,help="simulation start year")
parser.add_argument("month",type=int,help="simulation start month")
parser.add_argument("day",type=int,help="simulation start day")
parser.add_argument("hour",type=int,help="simulation start hour")
args = parser.parse_args()

year = args.year
mon  = args.month
day  = args.day
hour = args.hour

def job(eNum):

    #subprocess.check_call(["python","batch_f.py",year,mon,day,hour,str(eNum)])
    print eNum


def multiGet():

    eNums = np.arange(0,52,1).tolist()
    print eNums
    p = Pool(3)
    p.map(job,eNums)
    p.terminate()

if __name__ == "__main__":

    multiGet()
