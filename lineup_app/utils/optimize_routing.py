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
from collections import Counter



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




def filter_combs(combs,filters,session_json):

    wells_in_combs=[w["well"] for w in combs[0]]
    # print(wells_in_combs)

    state_routes=[]
    for w,v in session_json["well_data"].items():
        if not w in wells_in_combs:
            r=v["selected_route"].split("--")[:-1] # remove last part (slot infor) from route
            r='--'.join([str(x) for x in r]) # make string again
            state_routes.append(r)

    # print(state_routes)

    filtered_combs=[]
    for comb in combs:

        # unique_routes=[]
        flag=0
        comb_=[]
        for c in comb: # generate unique route list
            c=c["route_name"].split("--")[:-1]
            c='--'.join([str(x) for x in c])
            comb_.append(c)

            # if not c in unique_routes:
            #     unique_routes.append(c)

        state_comb=state_routes+comb_

        counts=Counter(state_comb)
        # print(counts.keys())
        # print(counts.values())
        # print(counts)
        # print(state_comb)
        for i,r in enumerate(counts.keys()):
            # if r=="U3--DIRECT--EOPS_U3":
            #     print(r,i,list(counts.values())[i])
            cnt=list(counts.values())[i]



            if r in comb_:
                # print(r,comb_)
                if filters["tl_max_num"]:
                    if cnt>int(filters["tl_max_num"]):
                        flag=1
                        # print("tl_max:  ", r, cnt)
                        break

                if filters["test_max_num"]:
                    if "TEST" in r and cnt>int(filters["test_max_num"]):
                        flag=1
                        # print("test_max:  ", r, cnt)
                        break


        #
        #
        # for ur in unique_routes: # count same routes in combination
        #     cnt=0
        #     for c in comb_:
        #         if c == ur:
        #             cnt+=1
        #
        #     if filters["tl_max_num"]:
        #         if cnt>int(filters["tl_max_num"]):
        #             flag=1
        #             break
        #
        #     if filters["test_max_num"]:
        #         # print(cnt,filters["test_max_num"])
        #         if "TEST" in ur and cnt>int(filters["test_max_num"]):
        #             flag=1
        #             break


        if flag==0:
            filtered_combs.append(comb)

    # for f in filtered_combs:
    #     print(f)

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

def route_optimization(session_json,ro_data,filters,mockup):

    # combinations=generate_comb(session_json)
    combinations=generate_comb2(ro_data)
    combinations=filter_combs(combinations,filters,session_json)
    # print(len(combinations))
    # for cnt,comb in enumerate(combinations):
    #     print(comb)
    # return None
    utils.save_orig_session_json(session_json)

    # session_json_copy=session_json
    # return None
    if not mockup:
        PE_server=ut.PE.Initialize()
    else:
        PE_server="None"

    # ut.showinterface(PE_server,0)
    start=datetime.datetime.now()

    best_res={
        "tot_qoil":0.0,
        "tot_qgas":0.0,
        "tot_qwat":0.0
    }
    best_comb=[]

    for cnt,comb in enumerate(combinations):

        iter_start=datetime.datetime.now()

        best=0
        print("iter:",cnt)
        emit("route_table",{"comb":comb,"comb_cnt":cnt+1,"comb_tot":len(combinations)}) # update table highlights according to routes applied
        sleep(0.1)

        res=solve_comb(session_json,comb,mockup,PE_server)

        iter_dt=datetime.datetime.now()-iter_start


        if res["tot_qoil"]>best_res["tot_qoil"]:
            best=1
            best_res=res
            best_comb=comb
            utils.save_best_session_json(session_json)

        comb_str='|'.join([c["well"]+":"+c["route_name"] for c in comb])
        # print([c["well"]+":"+c["route_name"] for c in comb])

        emit("progress",{
                "data":"Calculations complete. Switching to next State... <br> Time spent: %s" % iter_dt,
                "finish":2,
                "res":res,
                "state_id":cnt+1,
                "time":str(iter_dt).split('.')[0],
                "best":best,
                "comb":comb_str
            })





    session_json=utils.get_best_session_json()
    utils.save_session_json(session_json)
    emit("progress",{"data":"Applied best routing to current state"})

    if not best_comb==comb: # resolve combination if best is not equal to current combination
        emit("progress",{"data":"Resolving best combination.."})
        emit("route_table",{"comb":best_comb,"comb_cnt":-1,"comb_tot":len(combinations)}) # update table highlights according to routes applied
        res=solve_comb(session_json,best_comb,mockup,PE_server)

    if not mockup:
        PE_server=ut.PE.Stop()

    dt=datetime.datetime.now()-start
    dt=str(dt).split('.')[0]
    emit("progress",{"data":"Route optimization complete. <br>Time spent: %s" % dt,"finish":1,"best_comb":best_comb})
    sleep(0.1)

    return "None"


def solve_comb(session_json,comb,mockup,PE_server):

    session_json=utils.calc_target_fwhps(session_json)
    for c in comb:
        session_json["well_data"][c["well"]]["selected_route"]=c["route_name"]

    if mockup:
        nsst.set_unit_routes(session_json["well_data"],PE_server,2) # set well routes as per state
        session_json["well_data"]=nsst.get_all_well_data(session_json["well_data"],PE_server,2)
        res=nsopt.run_optimization(session_json,PE_server,2)
    else:
        st.set_unit_routes(session_json["well_data"],PE_server,2) # set well routes as per state
        session_json["well_data"]=st.get_all_well_data(session_json["well_data"],PE_server,2)
        res=gob.run_optimization(session_json,PE_server,2)

    return res



if __name__ == "__main__":
    main()
