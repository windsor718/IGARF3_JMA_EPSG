import datetime
import subprocess

sDate = datetime.datetime(2019,5,14,12)
eDate = datetime.datetime(2019,5,20,12)

date  = sDate
while date <= eDate:
    print date
    subprocess.call(["python","batch_f.py",str(date.year),str(date.month),str(date.day),str(date.hour),"0"])
    subprocess.call(["python","batch_m.py",str(date.year),str(date.month),str(date.day),str(date.hour),"0"])
    date = date + datetime.timedelta(hours=12)
