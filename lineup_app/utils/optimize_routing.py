import array
import random

import numpy
from flask_socketio import SocketIO, send, emit
import gevent
from gevent import monkey, sleep
from lineup_app.NetSim_modules import NetSim_setup as nsst
from lineup_app.NetSim_modules import NetSim_optimization as nsopt
from lineup_app.GAP_modules import GAP_optimization as gob
from lineup_app.GAP_modules import GAP_setup as st
from lineup_app.GAP_modules import GAP_utils as ut
from lineup_app.utils import utils
import datetime



def generate_comb(session_json):
    r=[[]]
    for w,x in session_json["well_data"].items():
        if "ro" in x:
            if x["ro"]==1:
                t = []
                for y in x["connection"]["routes"]:
                    # print(y)
                    for i in r:
                        t.append(i+[{"well":w,"route_name":y["route_name"]}])
                r = t
    return r


def generate_comb2(ro_data):
    r=[[]]
    for w,x in ro_data.items():
        t = []
        for y in x:
            for i in r:
                t.append(i+[{"well":w,"route_name":y}])
        r = t
    return r


def filter_combs(combs,max_wells):

    filtered_combs=[]
    for comb in combs:
        print("hi")
        # routes=[]
        unique_routes=[]
        flag=0
        comb_=[]
        for c in comb: # generate unique route list
            c=c["route_name"].split("--")[:-1]
            c='--'.join([str(x) for x in c])
            comb_.append(c)

            if not c in unique_routes:
                unique_routes.append(c)

        for ur in unique_routes: # count same routes in combination
            cnt=0
            for c in comb_:
                if c == ur:
                    cnt+=1

            if cnt>max_wells:
                flag=1
                break

        if flag==0:
            filtered_combs.append(comb)

    return filtered_combs



def count_combs(ro_data):
    comb_num=1
    for w,r in ro_data.items():
        if r:
            comb_num=comb_num*len(r)
    return comb_num


def get_well_routes(session_json):
    ro_data={}
    for w,x in session_json["well_data"].items():
        if "ro" in x:
            if x["ro"]==1:
                ro_data[w]=x["connection"]["routes"]
    return ro_data



def prep_route_opt(session_json):

    ro_data=get_well_routes(session_json)

    # ro_msg=make_msg(ro_data)

    emit("prep_ro_data",{"data":ro_data})


    # for w,val in ro_data.items():
    #     print(w,val)

    # combinations=generate_comb(session_json)
    # # print(combinations)
    # for cnt,comb in enumerate(combinations):
    #     print(comb)
    return None

def route_optimization(session_json,ro_data,mockup):

    # combinations=generate_comb(session_json)
    combinations=generate_comb2(ro_data)
    combinations=filter_combs(combinations,3)
    print(len(combinations))
    # for cnt,comb in enumerate(combinations):
    #     print(comb)
    # return None
    utils.save_orig_session_json(session_json)

    # session_json_copy=session_json
    # return None
    if not mockup:
        PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)
    start=datetime.datetime.now()

    best_res={
        "tot_qoil":0.0,
        "tot_qgas":0.0,
        "tot_qwat":0.0
    }

    for cnt,comb in enumerate(combinations):

        iter_start=datetime.datetime.now()
        best=0
        print(comb)
        # session_json_copy=session_json
        emit("progress",{"data":"-----> Performing routing combination: %s out of %s" % (cnt+1,len(combinations))})
        sleep(0.1)

        session_json=utils.calc_target_fwhps(session_json)
        for c in comb:
            session_json["well_data"][c["well"]]["selected_route"]=c["route_name"]

        if mockup:
            nsst.set_unit_routes(session_json["well_data"]) # set well routes as per state
            session_json["well_data"]=nsst.get_all_well_data(session_json["well_data"])
            res=nsopt.run_optimization(session_json,2)
        else:
            st.set_unit_routes(session_json["well_data"]) # set well routes as per state
            session_json["well_data"]=st.get_all_well_data(session_json["well_data"])
            res=gob.run_optimization(session_json,PE_server,2)

        iter_dt=datetime.datetime.now()-iter_start
        print(res)

        if res["tot_qoil"]>best_res["tot_qoil"]:
            best=1
            best_res=res
            utils.save_best_session_json(session_json)

        emit("progress",{
                "data":"Calculations complete. Switching to next State... <br> Time spent: %s" % iter_dt,
                "finish":2,
                "res":res,
                "state_id":cnt+1,
                "time":str(iter_dt).split('.')[0],
                "best":best
            })

    if not mockup:
        PE_server=ut.PE.Stop()


    # emit("progress",{"data":"Applying best routing..."})
    session_json=utils.get_best_session_json()
    utils.save_session_json(session_json)
    emit("progress",{"data":"Applied best routing to current state"})


    dt=datetime.datetime.now()-start
    emit("progress",{"data":"Route optimization complete. <br>Time spent: %s" % dt,"finish":1})
    sleep(1)

    return "None"


if __name__ == "__main__":
    main()
