
from lineup_app.utils import PI
import datetime
import numpy as np


def get_iwit_thp(wellnames,start,end):
    PI_server=PI.Initialize()

    iwit_thps=[]
    for well,well_gap in wellnames.items():
        tag="KA:WP"+well+"_WHP"
        data, pointType = PI.ExtractData(PI_server, tag)
        ts, values = PI.InterpolatedValues(data, start, end, interval="1h")

        if values: # check if pi returned any values
            if check_if_nums(values): # check if all are numbers
                avg_thp=round(np.mean(values)+1.0,1) # BarG to BarA
                if avg_thp>50.0: # include reading that are more than 50bar
                    iwit_thps.append([well_gap,start,avg_thp,"-"])

    PI_server=PI.StopServer(PI_server)

    return iwit_thps


def check_if_nums(vals):
    nums=True
    for v in vals:
        if not is_number(v):
            nums=False
            break
    return nums


def is_number(s):
    try:
        float(s)
        return True
    except:
        return False


def get_calibration_pi_data(wellnames,pi_tags,start,end):
    PI_server=PI.Initialize()

    calibration_pi_data=[]

    for well,well_gap in wellnames.items():

        if well in pi_tags:

            well_row=[well_gap] # initialize array

            # IWIT THP
            tag="KA:WP"+well+"_WHP"
            try:
                data, pointType = PI.ExtractData(PI_server, tag)
                ts, values = PI.InterpolatedValues(data, start, end, interval="1h")
                well_row.append(validate_nums_avg(values))
            except:
                well_row.append("-")

            # Flowline pressure
            tag=pi_tags[well]["flp_pi_tag"]
            try:
                data, pointType = PI.ExtractData(PI_server, tag)
                ts, values = PI.InterpolatedValues(data, start, end, interval="1h")
                well_row.append(validate_nums_avg(values))
            except:
                well_row.append("-")

            # Slot pressure
            tag=pi_tags[well]["slp_pi_tag"]
            try:
                data, pointType = PI.ExtractData(PI_server, tag)
                ts, values = PI.InterpolatedValues(data, start, end, interval="1h")
                well_row.append(validate_nums_avg(values))
            except:
                well_row.append("-")

            calibration_pi_data.append(well_row)


    PI_server=PI.StopServer(PI_server)

    return calibration_pi_data




def validate_nums_avg(values):

    avg_val=""
    if values: # check if pi returned any values
        if check_if_nums(values): # check if all are numbers
            avg_val=round(np.mean(values)+1.0,1) # BarG to BarA
            if avg_val<50.0: # include reading that are more than 50bar
                avg_val="-"

    return avg_val

def get_online_status(wellnames,start,end):
    PI_server=PI.Initialize()

    online_status=[]
    for well,well_gap in wellnames.items():
        tag="KA:WP"+well+"_STATUS"
        data, pointType = PI.ExtractData(PI_server, tag)
        ts, values = PI.InterpolatedValues_other(data, start, end, interval="1h")
        if values: # check if pi returned any values
            online_status.append([well_gap,ts[0],values[0]]) # get the first data point

    PI_server=PI.StopServer(PI_server)

    return online_status


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
