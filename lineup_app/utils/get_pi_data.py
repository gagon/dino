
from lineup_app.utils import PI
import datetime


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

    data, pointType = PI.ExtractData(PI_server, data2get["pi_tag"])
    ts, values = PI.InterpolatedValues(data, data2get["start"], data2get["end"], interval=data2get["interval"])

    ts_str=[]
    for t in ts:
        ts_str.append(datetime.datetime.strftime(t,"%d/%m/%Y %H:%M:%S"))

    pidata={
        "ts":ts_str,
        "values":values
    }

    PI_server=PI.StopServer(PI_server)

    return pidata
