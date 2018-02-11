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
from lineup_app.GAP_modules import GAP_utils as ut
from xlrd import open_workbook,xldate_as_tuple
import datetime
from flask_socketio import SocketIO, send, emit
import gevent
from gevent import monkey, sleep
import json
from lineup_app.GAP_modules import GAP_setup as st



def run_optimization(session_json,PE_server,mode):

    units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
    units_label=["KPC","Unit-3","Unit-2"]
    units_simple=["kpc","u3","u2"]

    #
    if mode==1:
        PE_server=ut.PE.Initialize()
        # ut.showinterface(PE_server,0)

    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)

    #
    start=datetime.datetime.now()

    emit("progress",{"data":"Applying Target FWHPs.."})

    status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
    wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
    qgas_max_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQgas") # qgas_max is the main tool for GAP rule based optimizer

    # set all qgas max per well
    set_qgas_max(wellname,status,session_json["well_data"],qgas_max_orig)

    emit("progress",{"data":"Solving Network..."})
    emit("progress",{"data":"------------------------------"})
    sleep(0.1)
    ut.solve_network_rb(PE_server)

    unit_data=session_json["unit_data"]


    repeat=1
    tol=0.5
    while repeat==1:

        qgas=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].GasRate",status,"float")
        qoil=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].OilRate",status,"float")
        qwat=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].WatRate",status,"float")

        oil_constraint=[0,0,0]
        optimized=0
        for unit_idx,unit in enumerate(units_simple):

            data_unit=[]
            unit_qgas=0.0
            unit_qoil=0.0
            unit_qwat=0.0

            for i,well in enumerate(wellname):

                if qgas[i]>0:
                    if session_json["well_data"][well]["unit_id"]==unit_idx:
                        data_unit.append([well,session_json["well_data"][well]["gor"],qgas[i],qoil[i],qwat[i]])
                        unit_qgas+=qgas[i]
                        unit_qoil+=qoil[i]
                        unit_qwat+=qwat[i]

            data_unit=sorted(data_unit,key=lambda x:x[1],reverse=True)

            unit_qgas_max=unit_data[unit]["constraints"]["qgas_max"]
            unit_qoil_max=unit_data[unit]["constraints"]["qoil_max"]
            unit_qwat_max=unit_data[unit]["constraints"]["qwat_max"]

            if unit_qgas>unit_qgas_max or unit_qoil>unit_qoil_max:
                optimized=1
                i=0
                while unit_qgas-data_unit[i][2]>unit_qgas_max or unit_qoil-data_unit[i][3]>unit_qoil_max:
                    if session_json["well_data"][data_unit[i][0]]["fixed"]==0:
                        unit_qgas-=data_unit[i][2]
                        unit_qoil-=data_unit[i][3]
                        wells_to_shut.append(data_unit[i][0])
                        ut.shut_well(PE_server,data_unit[i][0])
                        emit("progress",{
                            "data":"%s: SI well %s - GOR=%.1f" % (
                                                        units_label[unit_idx],
                                                        data_unit[i][0], # wellname from data_unit
                                                        data_unit[i][1] # gor from data_unit
                                                        )
                            })

                    else:
                        emit("progress",{
                            "data":"%s: Skipped fixed well %s - GOR=%.1f ^^" % (
                                                        units_label[unit_idx],
                                                        data_unit[i][0],
                                                        data_unit[i][1]
                                                        )
                            })
                    sleep(0.1)
                    i+=1


                while session_json["well_data"][data_unit[i][0]]["fixed"]==1: # find well that is not fixed
                    i+=1
                swing_well=data_unit[i][0]

                delta_qgas_max=unit_qgas_max-unit_qgas

                # see if qoil_max is closer, if yes, then convert to qgas_max using swing well gor and apply as well constraint
                oil_constraint[unit_idx]=0

                delta_qoil_max=unit_qoil_max-unit_qoil

                delta_qgas_max_from_qoil=delta_qoil_max*session_json["well_data"][swing_well]["gor"]/1000.0
                if delta_qgas_max_from_qoil<delta_qgas_max:
                    delta_qgas_max=delta_qgas_max_from_qoil
                    oil_constraint[u]=1

                qgas_max=session_json["well_data"][swing_well]["qgas_max"]
                qgas_max2gap=qgas_max+delta_qgas_max

                if qgas_max2gap>10.0:
                    ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+swing_well+"}].MaxQgas",qgas_max2gap)
                    session_json["well_data"][swing_well]["qgas_max"]=qgas_max2gap
                    emit("progress",{"data":"%s: Swing well %s**" % (units_label[unit_idx],swing_well)})
                else:
                    wells_to_shut.append(swing_well)
                    ut.shut_well(PE_server,swing_well)
                    emit("progress",{"data":"%s: Unstable swing well %s shut" % (units_label[unit_idx],swing_well)})
                sleep(0.1)

        if optimized==1:
            emit("progress",{"data":"Solving Network.."})
            sleep(0.1)
            ut.solve_network_rb(PE_server)

        conv=0.0
        for unit_idx,unit in enumerate(units_simple):

            unit_qgas=ut.get_unit_qgas(PE_server,units[unit_idx])
            unit_qoil=ut.get_unit_qoil(PE_server,units[unit_idx])
            unit_qwat=ut.get_unit_qwat(PE_server,units[unit_idx])
            unit_qgas_max=unit_data[unit]["constraints"]["qgas_max"]
            unit_qoil_max=unit_data[unit]["constraints"]["qoil_max"]
            unit_qwat_max=unit_data[unit]["constraints"]["qwat_max"]
            # # save to session
            # unit_data[unit]["results"]["qgas"]=unit_qgas
            # unit_data[unit]["results"]["qoil"]=unit_qoil
            # unit_data[unit]["results"]["qwat"]=unit_qwat

            # reporting
            if unit_qgas>unit_qgas_max:
                emit("progress",{"data":"<mark>Qgas=%.1f, Qgas max=%.1f </mark>" % (unit_qgas,unit_qgas_max)})
            else:
                emit("progress",{"data":"Qgas=%.1f, Qgas max=%.1f" % (unit_qgas,unit_qgas_max)})

            if unit_qoil>unit_qoil_max:
                emit("progress",{"data":"<mark>Qoil=%.1f, Qoil max=%.1f </mark>" % (unit_qoil,unit_qoil_max)})
            else:
                emit("progress",{"data":"Qoil=%.1f, Qoil max=%.1f" % (unit_qoil,unit_qoil_max)})

            if unit_qwat>unit_qwat_max:
                emit("progress",{"data":"<mark>Qwater=%.1f, Qwater max=%.1f </mark>" % (unit_qwat,unit_qwat_max)})
            else:
                emit("progress",{"data":"Qwater=%.1f, Qwater max=%.1f" % (unit_qwat,unit_qwat_max)})

            emit("progress",{"data":"%s -----------------------------------------" % units_label[unit_idx]})
            sleep(0.5)

            if oil_constraint[unit_idx]==1:
                if unit_qoil>unit_qoil_max*1.0001:
                    conv+=abs(unit_qoil_max-unit_qoil)
            else:
                if unit_qgas>unit_qgas_max*1.0001:
                    conv+=abs(unit_qgas_max-unit_qgas)



        if conv>tol:
            repeat=1
            emit("progress",{"data":"Repeat iteration to converge.. ---------"})
            sleep(0.1)
        else:
            repeat=0


    ut.set_chokes_calculated(PE_server)

    dt=datetime.datetime.now()-start
    if mode==1:
        # ut.showinterface(PE_server,1)
        PE_server=ut.PE.Stop()
        emit("progress",{"data":"Calculations complete. Go to Results. <br> Time spent: %s" % dt,"finish":1})
    elif mode==2:
        emit("progress",{"data":"Calculations complete. Switching to next State... <br> Time spent: %s" % dt})
    sleep(0.1)

    return None


def route_optimization(session_json):

    combinations=generate_comb(session_json)
    session_json_copy=session_json

    PE_server=ut.PE.Initialize()
    ut.showinterface(PE_server,0)
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


def set_qgas_max(wellname,status,well_data,qgas_max_orig):
    qgas_max=[] # qgas_max values per well to set
    for well in wellname:
        if "target_fwhp" in well_data[well]:
            if well_data[well]["target_fwhp"]>0.0:
                qgas_max.append(well_data[well]["qgas_max"])
            else:
                ut.shut_well(PE_server,well)
                qgas_max.append("")
        else:
            ut.shut_well(PE_server,well)
            qgas_max.append("")

    qgas_max2gap=ut.updatepar(qgas_max_orig,qgas_max,status)
    qgas_max2gap=ut.list2gapstr(qgas_max2gap)
    ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQgas",qgas_max2gap)

    return None


def generate_comb(session_json):
    r=[[]]
    for w,x in session_json["well_data"].items():
        if "ro" in x:
            if x["ro"]==1:
                t = []
                for y in x["connection"]["routes"]:
                    print(y)
                    for i in r:
                        t.append(i+[{"well":w,"route_name":y["route_name"]}])
                r = t
    return r
