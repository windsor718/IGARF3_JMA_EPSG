import datetime
import subprocess

sDate = datetime.datetime(2018,6,29,12)
eDate = datetime.datetime(2018,6,29,12)

date  = sDate
while date <= eDate:
    print date
    for eNum in range(0,51):
        print eNum
        subprocess.call(["python","batch_f.py",str(date.year),str(date.month),str(date.day),str(date.hour),str(eNum)])
        subprocess.call(["python","batch_m.py",str(date.year),str(date.month),str(date.day),str(date.hour),str(eNum)])
    date = date + datetime.timedelta(hours=12)
