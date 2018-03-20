
from lineup_app.utils import PI
import datetime
import numpy as np


def get_iwit_thp(wellnames,start,end):
    PI_server=PI.Initialize()

    iwit_thps=[]
    for well,well_gap in wellnames.items():
        tag="KA:WP"+well+"_WHP"
        data, pointType = PI.ExtractData(PI_server, tag)
        ts, values = PI.InterpolatedValues(data, start, end, interval="1d")
        # ts, values = PI.RecordedValues(data, start, end)
        if values:
            if values[-1]>50.0:
                iwit_thps.append([well_gap,start,values[-1]+1,"-"])

    PI_server=PI.StopServer(PI_server)

    return iwit_thps



def get_pi_data(data2get):
    PI_server=PI.Initialize()
    pidata=fetch_pi(PI_server,data2get["pi_tag"],data2get["start"],data2get["end"],data2get["interval"])
    PI_server=PI.StopServer(PI_server)

    return pidata



def get_pi_arr(data2get_list):
    PI_server=PI.Initialize()
    for i,data2get in enumerate(data2get_list["tags"]):
        pidata=fetch_pi(PI_server,data2get["pi_tag"],data2get_list["time"]["start"],data2get_list["time"]["end"],data2get_list["time"]["interval"])
        pidata["values"]=round(np.mean(pidata["values"]),data2get["precision"])
        pidata["ts"]="avg"
        data2get_list["tags"][i]["pidata"]=pidata
    PI_server=PI.StopServer(PI_server)

    return data2get_list


def fetch_pi(PI_server,pi_tag,start,end,interval):

    data, pointType = PI.ExtractData(PI_server, pi_tag)
    ts, values = PI.InterpolatedValues(data, start, end, interval=interval)

    ts_str=[]
    for t in ts:
        ts_str.append(datetime.datetime.strftime(t,"%d/%m/%Y %H:%M:%S"))

    pidata={
        "ts":ts_str,
        "values":values
    }
    return pidata
