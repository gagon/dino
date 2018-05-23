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

""" SOLVER SETTINGS ====================================== """
unit_names={}
unit_names["sep"]=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
unit_names["label"]=["KPC","Unit-3","Unit-2"]
unit_names["simple"]=["kpc","u3","u2"]
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

    if mode==1: # mode 1 is just optimization, if mode=2, then higher level routing optimization is taking place, then no need to initialize, PE_server is initialized from routing opt function
        PE_server=ut.PE.Initialize()

    start=datetime.datetime.now()

    emit("progress",{"data":"Applying Target FWHPs.."})

    status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
    wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
    qgas_max_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQgas") # qgas_max is the main tool for GAP rule based optimizer

    # set all qgas max per well. This is to translate all target THPs to wells via qgasmax
    set_qgas_max(PE_server,wellname,status,session_json["well_data"],qgas_max_orig)

    emit("progress",{"data":"Solving Network..."})
    emit("progress",{"data":"------------------------------"})
    sleep(0.1)

    ut.solve_network_rb(PE_server) # solve network as a first pass

    unit_data=session_json["fb_data"]["unit_data"]
    unit_constraints_af={}
    for unit_idx,unit in enumerate(unit_names["simple"]): # calc AF constraints
        unit_constraints_af[unit]={}
        unit_constraints_af[unit]["qgas_max"]=unit_data[unit]["constraints"]["qgas_max"]/unit_data[unit]["af"]["af_gas"]
        unit_constraints_af[unit]["qoil_max"]=unit_data[unit]["constraints"]["qoil_max"]/unit_data[unit]["af"]["af_oil"]
        unit_constraints_af[unit]["qwat_max"]=unit_data[unit]["constraints"]["qwat_max"]/unit_data[unit]["af"]["af_wat"]


    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # OPTIMIZATION +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    tol=0.5
    conv=1000.0 # set initial high values to enter while loop
    iter_num=0

    while conv>tol and iter_num<10: # main loop, repeats until convergence is met or number of iteration exceed 10

        if iter_num>0: # don't report reiteration the first time
            emit("progress",{"data":"Repeat iteration to converge.. Iteration:%s ---------" % iter_num})
            sleep(0.1)

        well_prod={}
        well_prod["qgas"]=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].GasRate",status,"float")
        well_prod["qoil"]=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].OilRate",status,"float")
        well_prod["qwat"]=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].WatRate",status,"float")

        oil_constraint=[0,0,0] # this is used as array flag for each unit to say if unit is oil constrained qgas max for swing well will be set from oil difference rather than gas
        optimized=0 # this flag is used to decide if resolving network is needed or not
        for unit_idx,unit in enumerate(unit_names["simple"]): # solve every unit

            # this SI all unnesesary wells, finds swing well and chokes it back to set unit rates to unit constraints
            session_json,optimized,oil_constraint=solve_unit(PE_server,wellname,session_json,well_prod,unit_idx,oil_constraint,optimized,unit_data,unit_constraints_af)


        if optimized==1: #this flag is used to decide if resolving network is needed or not
            emit("progress",{"data":"Solving Network.."})
            sleep(0.1)
            ut.solve_network_rb(PE_server) # repeat solve networ if any well was SI during unit optimization


        # report results of optimization and calculate covergence
        conv,tot_qoil,tot_qgas,tot_qwat=report_results(PE_server,unit_names,unit_data,oil_constraint,unit_constraints_af)

        iter_num+=1
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    if iter_num>9:
        emit("progress",{"data":"Number of iterations exceeded!!!"})


    ut.set_chokes_calculated(PE_server) # after finishing calculations set back all well chokes to calculated state. This is required for the next calculations.

    res={
        "tot_qoil":round(tot_qoil,1),
        "tot_qgas":round(tot_qgas,1),
        "tot_qwat":round(tot_qwat,1)
    }


    dt=datetime.datetime.now()-start
    if mode==1:
        # ut.showinterface(PE_server,1)
        PE_server=ut.PE.Stop()
        emit("progress",{"data":"Calculations complete. Go to Results. <br> Time spent: %s" % dt,"finish":1})
    elif mode==2:
        emit("progress",{"data":"Calculations complete. Switching to next State... <br> Time spent: %s" % dt})
    sleep(0.1)

    return res




def solve_unit(PE_server,wellname,session_json,well_prod,unit_idx,oil_constraint,optimized,unit_data,unit_constraints_af):


    # from GAP extracted data, calculate total unit rates and combine all wells in unit_data array
    unit_prod,well_dataset=calculate_wells(unit_idx,wellname,session_json,well_prod)

    # sort array according to GOR ranking (column 1)
    well_dataset_gor_ranked=sorted(well_dataset,key=lambda x:x[1],reverse=True)
    # sort array according to WCT ranking (column 2)
    well_dataset_wct_ranked=sorted(well_dataset,key=lambda x:x[2],reverse=True)

    unit=unit_names["simple"][unit_idx] # what unit we are looking at


    # solve water Unit constraints first
    if unit_prod["qwat"]>unit_constraints_af[unit]["qwat_max"]: # enter optimization if constraints are violated

        last_well_idx,optimized,unit_prod=kill_wells_by_wct(PE_server,
                                                            unit_idx,unit,
                                                            unit_prod,
                                                            unit_constraints_af,
                                                            well_dataset_wct_ranked,
                                                            unit_names,session_json)

        session_json,unit_prod=adjust_wct_swing(PE_server,
                                                    last_well_idx,
                                                    well_dataset_wct_ranked,
                                                    session_json,
                                                    unit_constraints_af,
                                                    unit,unit_prod,
                                                    oil_constraint,unit_idx,unit_names)





    # solve gas and oil Unit constraints
    if unit_prod["qgas"]>unit_constraints_af[unit]["qgas_max"] or \
        unit_prod["qoil"]>unit_constraints_af[unit]["qoil_max"]: # enter optimization if any of the constraints are violated

        last_well_idx,optimized,unit_prod=kill_wells_by_gor(PE_server,
                                                            unit_idx,unit,
                                                            unit_prod,
                                                            unit_constraints_af,
                                                            well_dataset_gor_ranked,
                                                            unit_names,session_json)

        session_json,oil_constraint=adjust_gor_swing(PE_server,
                                                    last_well_idx,
                                                    well_dataset_gor_ranked,
                                                    session_json,
                                                    unit_constraints_af,
                                                    unit,unit_prod,
                                                    oil_constraint,unit_idx,unit_names)



    return session_json,optimized,oil_constraint




def calculate_wells(unit_idx,wellname,session_json,well_prod):

    well_dataset=[]
    unit_prod={}
    unit_prod["qgas"]=0.0
    unit_prod["qoil"]=0.0
    unit_prod["qwat"]=0.0

    for i,well in enumerate(wellname):

        if well_prod["qgas"][i]>0:
            if session_json["well_data"][well]["unit_id"]==unit_idx:

                well_dataset.append(
                    [
                        well,
                        session_json["well_data"][well]["gor"],
                        session_json["well_data"][well]["wct"],
                        # (session_json["well_data"][well]["wct"]/100)/(1-session_json["well_data"][well]["wct"]/100), # Water Oil Ratio (WOR)
                        well_prod["qgas"][i],
                        well_prod["qoil"][i],
                        well_prod["qwat"][i]
                    ]
                )
                unit_prod["qgas"]+=well_prod["qgas"][i]
                unit_prod["qoil"]+=well_prod["qoil"][i]
                unit_prod["qwat"]+=well_prod["qwat"][i]

    return unit_prod,well_dataset


def kill_wells_by_gor(PE_server,unit_idx,unit,unit_prod,unit_constraints_af,well_dataset_gor_ranked,unit_names,session_json):


    optimized=1 #this flag is used to decide if resolving network is needed or not
    i=0
    while unit_prod["qgas"]-well_dataset_gor_ranked[i][3]>unit_constraints_af[unit]["qgas_max"] or \
            unit_prod["qoil"]-well_dataset_gor_ranked[i][4]>unit_constraints_af[unit]["qoil_max"]: # SI wells one by one with GOR ranking logic

        well=well_dataset_gor_ranked[i][0]
        if session_json["well_data"][well]["fixed"]==0:

            unit_prod["qgas"]-=well_dataset_gor_ranked[i][3]
            unit_prod["qoil"]-=well_dataset_gor_ranked[i][4]
            unit_prod["qwat"]-=well_dataset_gor_ranked[i][5]

            ut.shut_well(PE_server,well)
            emit("progress",{
                "data":"%s: SI well %s - GOR=%.1f" % (
                                            unit_names["label"][unit_idx],
                                            well, # wellname from data_unit
                                            well_dataset_gor_ranked[i][1] # gor from data_unit
                                            )
                })

        else:
            emit("progress",{
                "data":"%s: Skipped fixed well %s - GOR=%.1f ^^" % (
                                            unit_names["label"][unit_idx],
                                            well,
                                            well_dataset_gor_ranked[i][1]
                                            )
                })
        sleep(0.1)
        i+=1

    return i,optimized,unit_prod



def adjust_gor_swing(PE_server,last_well_idx,well_dataset_gor_ranked,session_json,unit_constraints_af,unit,unit_prod,oil_constraint,unit_idx,unit_names):

    # SOLVE SWING ############################################################################################

    swing_well=well_dataset_gor_ranked[last_well_idx][0]
    while session_json["well_data"][swing_well]["fixed"]==1: # find next well that is not fixed
        swing_well=well_dataset_gor_ranked[last_well_idx][0]
        last_well_idx+=1

    delta_qgas_max=unit_constraints_af[unit]["qgas_max"]-unit_prod["qgas"] # calculate by how much Qgas should be reduced
    delta_qoil_max=unit_constraints_af[unit]["qoil_max"]-unit_prod["qoil"] # calculate by how much Qoil should be reduced



    # see if qoil_max is closer, if yes, then convert to qgas_max using swing well gor and apply as well constraint
    oil_constraint[unit_idx]=0
    delta_qgas_max_from_qoil=delta_qoil_max*session_json["well_data"][swing_well]["gor"]/1000.0
    if delta_qgas_max_from_qoil<delta_qgas_max:
        delta_qgas_max=delta_qgas_max_from_qoil
        oil_constraint[u]=1

    #take current swing well qgasmax from GAP
    swing_qgas_max=session_json["well_data"][swing_well]["qgas_max"]

    #then apply delta to it so that unit constraint is met
    swing_qgas_max2gap=swing_qgas_max+delta_qgas_max

    if swing_qgas_max2gap>10.0: #check if well can sustain this flow
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+swing_well+"}].MaxQgas",swing_qgas_max2gap)
        session_json["well_data"][swing_well]["qgas_max"]=swing_qgas_max2gap
        emit("progress",{"data":"%s: Swing well %s**" % (unit_names["label"][unit_idx],swing_well)})
    else: # if not, SI the well so that GAP solves faster
        ut.shut_well(PE_server,swing_well)
        emit("progress",{"data":"%s: Unstable swing well %s shut" % (unit_names["label"][unit_idx],swing_well)})
    sleep(0.1)

    return session_json,oil_constraint






def kill_wells_by_wct(PE_server,unit_idx,unit,unit_prod,unit_constraints_af,well_dataset_wct_ranked,unit_names,session_json):


    optimized=1 #this flag is used to decide if resolving network is needed or not
    i=0
    while unit_prod["qwat"]-well_dataset_wct_ranked[i][5]>unit_constraints_af[unit]["qwat_max"]:# SI wells one by one with GOR ranking logic

        well=well_dataset_wct_ranked[i][0]
        if session_json["well_data"][well]["fixed"]==0:

            unit_prod["qgas"]-=well_dataset_wct_ranked[i][3]
            unit_prod["qoil"]-=well_dataset_wct_ranked[i][4]
            unit_prod["qwat"]-=well_dataset_wct_ranked[i][5]

            ut.shut_well(PE_server,well)
            emit("progress",{
                "data":"%s: SI well %s - Watercut=%.1f" % (
                                            unit_names["label"][unit_idx],
                                            well, # wellname from data_unit
                                            well_dataset_wct_ranked[i][2] # gor from data_unit
                                            )
                })

        else:
            emit("progress",{
                "data":"%s: Skipped fixed well %s - Watercut=%.1f ^^" % (
                                            unit_names["label"][unit_idx],
                                            well,
                                            well_dataset_wct_ranked[i][2]
                                            )
                })
        sleep(0.1)
        i+=1

    return i,optimized,unit_prod




def adjust_wct_swing(PE_server,last_well_idx,well_dataset_wct_ranked,session_json,unit_constraints_af,unit,unit_prod,oil_constraint,unit_idx,unit_names):

    # SOLVE SWING ############################################################################################

    swing_well=well_dataset_wct_ranked[last_well_idx][0]
    while session_json["well_data"][swing_well]["fixed"]==1: # find next well that is not fixed
        swing_well=well_dataset_wct_ranked[last_well_idx][0]
        last_well_idx+=1

    delta_qwat_max=unit_constraints_af[unit]["qwat_max"]-unit_prod["qwat"] # calculate by how much Qgas should be reduced

    # qwat_max -> wct -> qoil_max -> gor -> qgas_max -> THP (in GAP)
    delta_qoil_max_from_qwat=delta_qwat_max*(1-session_json["well_data"][swing_well]["wct"]/100)/(session_json["well_data"][swing_well]["wct"]/100)
    delta_qgas_max_from_qoil=delta_qoil_max_from_qwat*session_json["well_data"][swing_well]["gor"]/1000.0
    delta_qgas_max=delta_qgas_max_from_qoil

    # using + because of negative values from delta (constr-unit prod)
    unit_prod["qwat"]+=delta_qwat_max
    unit_prod["qoil"]+=delta_qoil_max_from_qwat
    unit_prod["qgas"]+=delta_qgas_max_from_qoil

    #take current swing well qgasmax from GAP
    swing_qgas_max=session_json["well_data"][swing_well]["qgas_max"]

    #then apply delta to it so that unit constraint is met
    swing_qgas_max2gap=swing_qgas_max+delta_qgas_max

    if swing_qgas_max2gap>10.0: #check if well can sustain this flow
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+swing_well+"}].MaxQgas",swing_qgas_max2gap)
        session_json["well_data"][swing_well]["qgas_max"]=swing_qgas_max2gap
        emit("progress",{"data":"%s: Water Swing well %s**" % (unit_names["label"][unit_idx],swing_well)})
    else: # if not, SI the well so that GAP solves faster
        ut.shut_well(PE_server,swing_well)
        emit("progress",{"data":"%s: Unstable water swing well %s shut" % (unit_names["label"][unit_idx],swing_well)})
    sleep(0.1)

    return session_json,unit_prod



def report_results(PE_server,unit_names,unit_data,oil_constraint,unit_constraints_af):

    conv=0.0 # convergence value
    tot_qoil=0.0
    tot_qgas=0.0
    tot_qwat=0.0
    for unit_idx,unit in enumerate(unit_names["simple"]):
        unit_qgas=ut.get_unit_qgas(PE_server,unit_names["sep"][unit_idx]) # get directly from GAP separators
        unit_qoil=ut.get_unit_qoil(PE_server,unit_names["sep"][unit_idx]) # get directly from GAP separators
        unit_qwat=ut.get_unit_qwat(PE_server,unit_names["sep"][unit_idx]) # get directly from GAP separators
        tot_qoil+=unit_qoil
        tot_qgas+=unit_qgas
        tot_qwat+=unit_qwat

        # reporting
        if unit_qgas>unit_constraints_af[unit]["qgas_max"]:
            emit("progress",{"data":"<mark>Qgas=%.1f, Qgas max=%.1f </mark>" % (\
                unit_qgas*unit_data[unit]["af"]["af_gas"],\
                unit_constraints_af[unit]["qgas_max"]*unit_data[unit]["af"]["af_gas"])})
        else:
            emit("progress",{"data":"Qgas=%.1f, Qgas max=%.1f" % (\
                unit_qgas*unit_data[unit]["af"]["af_gas"],\
                unit_constraints_af[unit]["qgas_max"]*unit_data[unit]["af"]["af_gas"])})

        if unit_qoil>unit_constraints_af[unit]["qoil_max"]:
            emit("progress",{"data":"<mark>Qoil=%.1f, Qoil max=%.1f </mark>" % (\
                unit_qoil*unit_data[unit]["af"]["af_oil"],\
                unit_constraints_af[unit]["qoil_max"]*unit_data[unit]["af"]["af_oil"])})
        else:
            emit("progress",{"data":"Qoil=%.1f, Qoil max=%.1f" % (\
                unit_qoil*unit_data[unit]["af"]["af_oil"],\
                unit_constraints_af[unit]["qoil_max"]*unit_data[unit]["af"]["af_oil"])})

        if unit_qwat>unit_constraints_af[unit]["qwat_max"]:
            emit("progress",{"data":"<mark style='background-color:#cce6ff;'>Qwater=%.1f, Qwater max=%.1f </mark>" % (\
                unit_qwat*unit_data[unit]["af"]["af_wat"],\
                unit_constraints_af[unit]["qwat_max"]*unit_data[unit]["af"]["af_wat"])})
        else:
            emit("progress",{"data":"Qwater=%.1f, Qwater max=%.1f" % (\
                unit_qwat*unit_data[unit]["af"]["af_wat"],\
                unit_constraints_af[unit]["qwat_max"]*unit_data[unit]["af"]["af_wat"])})


        emit("progress",{"data":"%s -----------------------------------------" % unit_names["label"][unit_idx]})
        sleep(0.1)

        if oil_constraint[unit_idx]==1:
            if unit_qoil>unit_constraints_af[unit]["qoil_max"]*1.0001:
                conv+=abs(unit_constraints_af[unit]["qoil_max"]-unit_qoil)
        else:
            if unit_qgas>unit_constraints_af[unit]["qgas_max"]*1.0001:
                conv+=abs(unit_constraints_af[unit]["qgas_max"]-unit_qgas)

    return conv,tot_qoil,tot_qgas,tot_qwat





def route_optimization(session_json):

    combinations=generate_comb(session_json)
    session_json_copy=session_json

    PE_server=ut.PE.Initialize()
    ut.showinterface(PE_server,0) # don't update GAP interface, this is used to speed up GAP calculations
    start=datetime.datetime.now()

    for cnt,comb in enumerate(combinations):

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

    ut.showinterface(PE_server,1) # update GAP calculations after solving all combinations
    PE_server=ut.PE.Stop()

    dt=datetime.datetime.now()-start
    emit("progress",{"data":"Calculations complete. Go to Results. <br> Time spent: %s" % dt,"finish":1})
    sleep(1)

    return "None"


def set_qgas_max(PE_server,wellname,status,well_data,qgas_max_orig):
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
