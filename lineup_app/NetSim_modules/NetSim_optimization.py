# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""

""" SOLVER SETTINGS ====================================== """
conv_tol=0.01 # Qgas tolerance (Qgas unit total - Qgas unit constraint)
max_iters=20 # maximum iterations during simultaneous DP choke solving (optimization2)
pert_tol=0.001 # perturbations limit below which changing variable has no significant impact
""" ====================================================== """



import numpy as np
# from lineup_app import utils as ut
from xlrd import open_workbook,xldate_as_tuple
import datetime
from flask_socketio import SocketIO, send, emit
import gevent
from gevent import monkey, sleep
import json
# from lineup_app import GAP_setup as st
from lineup_app.NetSim_modules import NetSim_setup as nsst
from lineup_app.NetSim_modules import NetSim_utils as nsut



def run_optimization(session_json):

    # units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
    # units_simple=["kpc","u3","u2"]
    units=["kpc","u3","u2"]
    #
    #
    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)
    #
    start=datetime.datetime.now()

    emit("progress",{"data":"Applying Target FWHPs.."})
    sleep(0.1)


    status=nsut.get_all("wells","maskflag")
    wellname=nsut.get_filtermasked("wells","label",status,"string")
    # fwhp_min_orig=nsut.get_all("wells","constraints/fwhp_min")
    qgas_max_orig=nsut.get_all("wells","constraints/qgas_max")
    # print(wellname,status)

    # qgas_max_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQgas") # qgas_max is the main tool for GAP rule based optimizer

    qgas_max=[] # qgas_max values per well to set
    # fwhp_min=[]

    for well in wellname:
        # print(well)
        if "target_fwhp" in session_json["well_data"][well]:
            # print("target_fwhp exists")

            if session_json["well_data"][well]["target_fwhp"]>0.0:
                qgas_max.append(session_json["well_data"][well]["qgas_max"])
                # fwhp_min.append(session_json["well_data"][well]["fwhp_min"])
                # print("set fwhp_min to ", session_json["well_data"][well]["fwhp_min"])
            else:
                nsut.shut_well(well)
                qgas_max.append(-1)
                # fwhp_min.append("0")
                # print("shut the well")
        else:
            nsut.shut_well(well)
            qgas_max.append(-1)
            # print("not target_fwhp, shut the well")

    # print(fwhp_min)
    # return None
    # qgas_max2gap=ut.updatepar(qgas_max_orig,qgas_max,status)
    # qgas_max2gap=ut.list2gapstr(qgas_max2gap)
    # ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQgas",qgas_max2gap)

    # print(fwhp_min_orig,fwhp_min,status)
    # fwhp_min2gap=nsut.updatepar(fwhp_min_orig,fwhp_min,status)
    # fwhp_min2gap=nsut.list2gapstr(fwhp_min2gap)
    # nsut.NS.DoSetAll("wells","constraints/fwhp_min",fwhp_min2gap,"float")

    qgas_max2gap=nsut.updatepar(qgas_max_orig,qgas_max,status)
    qgas_max2gap=nsut.list2gapstr(qgas_max2gap)

    nsut.NS.DoSetAll("wells","constraints/qgas_max",qgas_max2gap,"float") # 5 secs
    # print(datetime.datetime.now())
    emit("progress",{"data":"Solving Network.."})
    sleep(0.1)

    nsut.solve_network_rb()  # 4-5 secs
    # ut.set_chokes_calculated(PE_server)
    # print(datetime.datetime.now())

    kpc_qgas_max=session_json["unit_data"]["constraints"]["kpc_qgas_max"]
    u3_qgas_max=session_json["unit_data"]["constraints"]["u3_qgas_max"]
    u2_qgas_max=session_json["unit_data"]["constraints"]["u2_qgas_max"]

    kpc_qoil_max=session_json["unit_data"]["constraints"]["kpc_qoil_max"]
    u3_qoil_max=session_json["unit_data"]["constraints"]["u3_qoil_max"]
    u2_qoil_max=session_json["unit_data"]["constraints"]["u2_qoil_max"]

    kpc_qwat_max=session_json["unit_data"]["constraints"]["kpc_qwat_max"]
    u3_qwat_max=session_json["unit_data"]["constraints"]["u3_qwat_max"]
    u2_qwat_max=session_json["unit_data"]["constraints"]["u2_qwat_max"]

    # return None

    repeat=1
    tol=0.5
    while repeat==1:

        # qgas=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].GasRate",status,"float")
        # qoil=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].OilRate",status,"float")
        # qwat=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].WatRate",status,"float")

        qoil=nsut.get_filtermasked("wells","results/qoil",status,"float")
        qgas=nsut.get_filtermasked("wells","results/qgas",status,"float")
        qwat=nsut.get_filtermasked("wells","results/qwat",status,"float")

        data_kpc=[]
        data_u3=[]
        data_u2=[]
        kpc_qgas=0.0
        u3_qgas=0.0
        u2_qgas=0.0
        kpc_qoil=0.0
        u3_qoil=0.0
        u2_qoil=0.0

        for i,well in enumerate(wellname):

            if qgas[i]>0:
                # print(qgas[i],well)
                if session_json["well_data"][well]["unit_id"]==0:
                    # print(well,session_json["well_data"][well]["gor"],qgas[i],qoil[i],qwat[i])
                    data_kpc.append([well,session_json["well_data"][well]["gor"],qgas[i],qoil[i],qwat[i]])
                    kpc_qgas+=qgas[i]
                    kpc_qoil+=qoil[i]
                elif session_json["well_data"][well]["unit_id"]==1:
                    data_u3.append([well,session_json["well_data"][well]["gor"],qgas[i],qoil[i],qwat[i]])
                    u3_qgas+=qgas[i]
                    u3_qoil+=qoil[i]
                elif session_json["well_data"][well]["unit_id"]==2:
                    data_u2.append([well,session_json["well_data"][well]["gor"],qgas[i],qoil[i],qwat[i]])
                    u2_qgas+=qgas[i]
                    u2_qoil+=qoil[i]

        data_kpc=sorted(data_kpc,key=lambda x:x[1],reverse=True)
        data_u2=sorted(data_u2,key=lambda x:x[1],reverse=True)
        data_u3=sorted(data_u3,key=lambda x:x[1],reverse=True)

        wells_to_shut=[]

        setup=[
            [kpc_qgas_max,kpc_qgas,kpc_qoil_max,kpc_qoil,data_kpc,"KPC"],
            [u3_qgas_max,u3_qgas,u3_qoil_max,u3_qoil,data_u3,"Unit-3"],
            [u2_qgas_max,u2_qgas,u2_qoil_max,u2_qoil,data_u2,"Unit-2"]
        ]
        # print(setup[0][1],setup[1][1],setup[2][1])


        oil_constraint=[0,0,0]
        optimized=0
        for u in range(3):

            unit_qgas_max=setup[u][0]
            unit_qgas=setup[u][1]
            unit_qoil_max=setup[u][2]
            unit_qoil=setup[u][3]
            data_unit=setup[u][4]
            unit=setup[u][5]

            # print(unit_qgas,unit_qgas_max, unit_qoil,unit_qoil_max)
            if unit_qgas>unit_qgas_max or unit_qoil>unit_qoil_max:
                optimized=1
                i=0
                while unit_qgas-data_unit[i][2]>unit_qgas_max or unit_qoil-data_unit[i][3]>unit_qoil_max:
                    if session_json["well_data"][data_unit[i][0]]["fixed"]==0:
                        unit_qgas-=data_unit[i][2]
                        unit_qoil-=data_unit[i][3]
                        wells_to_shut.append(data_unit[i][0])
                        nsut.shut_well(data_unit[i][0])
                        # session_json["well_data"][data_unit[i][0]]["target_fwhp"]=-1
                        emit("progress",{"data":"%s: SI well %s - GOR=%s" % (unit,data_unit[i][0],session_json["well_data"][data_unit[i][0]]["gor"])})
                        sleep(0.01)
                    else:
                        emit("progress",{"data":"%s: Skipped fixed well %s - GOR=%s ^^" % (unit,data_unit[i][0],session_json["well_data"][data_unit[i][0]]["gor"])})
                        sleep(0.01)
                    i+=1

                while session_json["well_data"][data_unit[i][0]]["fixed"]==1: # find well that is not fixed
                    i+=1
                swing_well=data_unit[i][0]


                delta_qgas_max=unit_qgas_max-unit_qgas

                # see if qoil_max is closer, if yes, then convert to qgas_max using swing well gor and apply as well constraint
                oil_constraint[u]=0

                delta_qoil_max=unit_qoil_max-unit_qoil


                delta_qgas_max_from_qoil=delta_qoil_max*session_json["well_data"][swing_well]["gor"]/1000.0
                if delta_qgas_max_from_qoil<delta_qgas_max:
                    delta_qgas_max=delta_qgas_max_from_qoil
                    oil_constraint[u]=1
                # print(delta_qoil_max,unit_qoil_max,unit_qoil,delta_qgas_max_from_qoil,delta_qgas_max,oil_constraint[u])

                qgas_max=session_json["well_data"][swing_well]["qgas_max"]
                qgas_max2gap=qgas_max+delta_qgas_max
                # print(swing_well,qgas_max,qgas_max2gap)
                if qgas_max2gap>10.0:
                    # ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+swing_well+"}].MaxQgas",qgas_max2gap)
                    nsut.NS.DoSet("wells/"+swing_well+"/constraints/qgas_max",qgas_max2gap)
                    session_json["well_data"][swing_well]["qgas_max"]=qgas_max2gap
                    emit("progress",{"data":"%s: Swing well %s**" % (unit,swing_well)})
                    sleep(0.01)
                    # sleep(1)
                else:
                    wells_to_shut.append(swing_well)
                    nsut.shut_well(swing_well)
                    emit("progress",{"data":"%s: Unstable swing well %s shut" % (unit,swing_well)})
                    sleep(0.01)
                    # sleep(1)



        if optimized==1:
            emit("progress",{"data":"Solving Network.."})
            sleep(0.01)
            nsut.solve_network_rb()

        # get sep results
        kpc_qgas=nsut.get_unit_qgas(units[0])
        u3_qgas=nsut.get_unit_qgas(units[1])
        u2_qgas=nsut.get_unit_qgas(units[2])
        kpc_qoil=nsut.get_unit_qoil(units[0])
        u3_qoil=nsut.get_unit_qoil(units[1])
        u2_qoil=nsut.get_unit_qoil(units[2])
        kpc_qwat=nsut.get_unit_qwat(units[0])
        u3_qwat=nsut.get_unit_qwat(units[1])
        u2_qwat=nsut.get_unit_qwat(units[2])

        # calculate covergence
        conv=0.0
        # kpc convergence
        if oil_constraint[0]==1:
            if kpc_qoil>kpc_qoil_max*1.0001:
                conv+=abs(kpc_qoil_max-kpc_qoil)
        else:
            if kpc_qgas>kpc_qgas_max*1.0001:
                conv+=abs(kpc_qgas_max-kpc_qgas)
        # u3 convergence
        if oil_constraint[1]==1:
            if u3_qoil>u3_qoil_max*1.0001:
                conv+=abs(u3_qoil_max-u3_qoil)
        else:
            if u3_qgas>u3_qgas_max*1.0001:
                conv+=abs(u3_qgas_max-u3_qgas)
        # u2 convergence
        if oil_constraint[2]==1:
            if u2_qoil>u2_qoil_max*1.0001:
                conv+=abs(u2_qoil_max-u2_qoil)
        else:
            if u2_qgas>u2_qgas_max*1.0001:
                conv+=abs(u2_qgas_max-u2_qgas)

        # print(conv,tol,oil_constraint)
        # print(kpc_qgas_max,kpc_qgas,u3_qgas_max,u3_qgas,u2_qgas_max,u2_qgas)
        emit("progress",{"data":"==============================="})
        emit("progress",{"data":"Qgas=%.1f, Qgas max=%.1f" % (kpc_qgas,kpc_qgas_max)})
        emit("progress",{"data":"Qoil=%.1f, Qoil max=%.1f" % (kpc_qoil,kpc_qoil_max)})
        emit("progress",{"data":"Qwater=%.1f, Qwater max=%.1f" % (kpc_qwat,kpc_qwat_max)})
        # sleep(0.01)
        emit("progress",{"data":"KPC =========================="})
        emit("progress",{"data":"Qgas=%.1f, Qgas max=%.1f" % (u3_qgas,u3_qgas_max)})
        emit("progress",{"data":"Qoil=%.1f, Qoil max=%.1f" % (u3_qoil,u3_qoil_max)})
        emit("progress",{"data":"Qwater=%.1f, Qwater max=%.1f" % (u3_qwat,u3_qwat_max)})
        # sleep(0.01)
        emit("progress",{"data":"Unit-3 =========================="})
        emit("progress",{"data":"Qgas=%.1f, Qgas max=%.1f" % (u2_qgas,u2_qgas_max)})
        emit("progress",{"data":"Qoil=%.1f, Qoil max=%.1f" % (u2_qoil,u2_qoil_max)})
        emit("progress",{"data":"Qwater=%.1f, Qwater max=%.1f" % (u2_qwat,u2_qwat_max)})
        emit("progress",{"data":"Unit-2 =========================="})
        sleep(0.01)

        if conv>tol:
            repeat=1
            emit("progress",{"data":"Repeat iteration to converge.. +++++++++++++++++++++++++++++++++++++++++++++++"})
            sleep(0.01)
        else:
            repeat=0

    print(datetime.datetime.now())
    # make well dp chokes calculated for the next calculations
    nsut.set_chokes_calculated()
    print(datetime.datetime.now())

    # ut.showinterface(PE_server,1)


    dt=datetime.datetime.now()-start
    emit("progress",{"data":"Calculations complete. Go to Results. <br> Time spent: %s" % dt,"finish":1})
    sleep(0.01)

    return None


def route_optimization(session_json):

    combinations=generate_comb(session_json)
    # print(combinations)
    for cnt,comb in enumerate(combinations):
        print(comb)

    session_json_copy=session_json
    return None
    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)
    start=datetime.datetime.now()

    for cnt,comb in enumerate(combinations):
        print(comb)
        session_json_copy=session_json
        emit("progress",{"data":"-----> Performing routing combination: %s out of %s" % (cnt,len(combinations))})
        sleep(0.1)

        for well,val in session_json_copy["well_data"].items(): # additional step to pre calculate required qgas_max equivalent to target FWHP
            if "target_fwhp" in val:
                if val["target_fwhp"]>0:
                    pc_fwhp=session_json_copy["well_data"][well]["pc"]["thps"]
                    pc_qgas=session_json_copy["well_data"][well]["pc"]["qgas"]
                    session_json_copy["well_data"][well]["qgas_max"]=np.interp(val["target_fwhp"],pc_fwhp,pc_qgas)

        for c in comb:
            session_json_copy["well_data"][c["well"]]["selected_route"]=c["route_name"]
        st.set_unit_routes(session_json_copy["well_data"]) # set well routes as per state








        run_optimization(session_json_copy,PE_server)


    ut.showinterface(PE_server,1)
    # PE_server=ut.PE.Initialize()
    PE_server=ut.PE.Stop()
    dt=datetime.datetime.now()-start
    emit("progress",{"data":"Calculations complete. Go to Results. <br> Time spent: %s" % dt,"finish":1})
    sleep(1)

    return "None"




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
