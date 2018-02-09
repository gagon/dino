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
from lineup_app.utils import utils as ut
from xlrd import open_workbook,xldate_as_tuple
import datetime
from flask_socketio import SocketIO, send, emit
import gevent
from gevent import monkey, sleep
import json
from lineup_app.GAP_modules import GAP_setup as st


# data = json.load(open(json_fullpath))


def optimization2(PE_server,opt_vals,opt_counter,gap_calc_json_fullpath):
    """

    """

    print("---- Fixed THP - simultaneous choke adjust")

    """ GET DP AND NO FLOW PRESSURE ====================================== """
    # initialize dp = 0, except for SI wells
    dp_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].PControlResult")

    if opt_counter==0:
        dp=np.zeros(len(opt_vals["fixed_thp"]))
    else:
        dp=ut.filtermasked(dp_orig,opt_vals["status"],"float")

    for d,d_ in enumerate(opt_vals["fixed_thp"]):
        if d_<0: # if fixed THP=-1 then keep welll SI
            dp[d]=10000.0
        elif dp[d]>9999.0: # to avoid thp>0 and dp=10000 inconsistency (open previously SI well)
            dp[d]=0
        # else:
        #     dp[d]=0.0
    # max thp at which well stops flowing, used to set thp_high
    # noflow_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MANIPRES[19]")
    # noflow=ut.filtermasked(noflow_orig,opt_vals["status"],"float")

    # print("hello!!!===================")

    """ INITIALIZE OPTIMIZATION PARAMETERS ====================================== """
    iter_=0
    conv=1000.0
    dp_prev=np.ones(len(dp))*1000.0 # dummy dp array
    pert=0
    # thp_low=np.zeros(len(opt_vals["wellname"]))
    # thp_high=noflow

    while conv>conv_tol and iter_<max_iters and pert==0:

        """ SET CHOKES ====================================== """
        dp2gap=ut.updatepar(dp_orig,dp,opt_vals["status"])
        dp2gap=ut.list2gapstr(dp2gap)
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[$].DPControlValue",dp2gap)


        """ GAP SOLVE NETWORK ====================================== """
        ut.solve_network(PE_server)


        """ GET RESULTS FROM GAP SOLVE NETWORK ====================================== """
        pres_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].Pres")
        pres=ut.filtermasked(pres_orig,opt_vals["status"],"float")

        dd_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].Drawdown")
        dd=ut.filtermasked(dd_orig,opt_vals["status"],"float")

        qliq_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].LiqRate")
        qliq=ut.filtermasked(qliq_orig,opt_vals["status"],"float")


        """ CALCULATE THP FROM RESULTS ====================================== """
        thp=pres+dp

        # print(dp)
        """ CALCULATE CONVERGENCE ====================================== """
        conv=0.01
        for j in range(len(dp)):
            thpopt=0.0
            # print(opt_vals["fixed_thp"][j],dp[j],pres[j])
            if opt_vals["fixed_thp"][j]>0.0 and dp[j]<10000.0 and opt_vals["fixed_thp"][j]>pres[j]:
                thpopt=abs(opt_vals["fixed_thp"][j]-thp[j])
            conv+=thpopt



        """ SIMULTANEOUS ADJUSTMENT OF DPS TO FIXED THP ====================================== """
        for d,dd_ in enumerate(dd):
            if dp[d]<10000.0 and opt_vals["fixed_thp"][d]>0.0:
                thp[d]=opt_vals["fixed_thp"][d]



        """ CALCULATE DP TO BE SET ====================================== """
        dp=thp-pres
        dp=dp.clip(min=0)


        """ CHECK IF CHOKES ARE PERTURBATING, IF NOT FINISH ====================================== """
        perts=np.sum(np.absolute(dp_prev-dp))
        if perts<pert_tol:
            pert=1
        else:
            dp_prev=dp

        """ GET OPTIMIZATION RESULTS ====================================== """
        lasterror=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SolverStatusList[0].LastError"))
        maxmassbaldif=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SolverStatusList[0].MaxMassBalanceDiff"))
        maxpresbaldif=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SolverStatusList[0].MaxPressureBalanceDiff"))


        """ INCREMENT ITERATION ====================================== """
        iter_+=1

        """ REPORT RESULTS ====================================== """
        print("conv=%.3f,iter=%s,perts=%.3f,lasterror=%.3f,massdif=%.3f,presdiff=%.3f" % \
                (conv,iter_,perts,lasterror,maxmassbaldif,maxpresbaldif))
        emit("progress",{"data":"conv=%.3f,iter=%s,perts=%.3f,lasterror=%.3f,massdif=%.3f,presdiff=%.3f" % \
                (conv,iter_,perts,lasterror,maxmassbaldif,maxpresbaldif)})
        sleep(0.1)


        # if not SWITCH:
        #     return -1



    if conv<=conv_tol or perts<pert_tol:
        return 1
    else:
        return 0




def optimization1(PE_server,unit,session_json):
    opt_counter=0

    optimization2(PE_server,opt_vals,opt_counter,gap_calc_json_fullpath) # core base of GAP optimization


    unit_qgas=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].GasRate"))
    opt_counter=1

    if unit_qgas>unit_constraints["qgas_max"]:

        gor_sorted=[\
                opt_vals["wellname"],\
                opt_vals["gor"].tolist(),\
                opt_vals["fixed_thp"].tolist(),\
                opt_vals["in_opt"].tolist()
                ]

        gor_sorted=[list(i) for i in zip(*gor_sorted)]
        gor_sorted=sorted(gor_sorted, key=lambda item: item[1],reverse=True)


        well_cnt=0
        # unit_qgas=float(50000)

        while unit_qgas>unit_constraints["qgas_max"]:
            # print(well_cnt,unit_qgas,unit_constraints[unit]["qgas"],"-----")

            # skip already SI wells, loop till you meet open well
            while gor_sorted[well_cnt][2]<0 or gor_sorted[well_cnt][3]==0:
                # print(well_cnt,len(gor_sorted)-1)
                if well_cnt>len(gor_sorted)-2:
                    break
                else:
                    well_cnt+=1

            if well_cnt>len(gor_sorted)-2:
                break


            well_idx_to_si=opt_vals["wellname"].index(gor_sorted[well_cnt][0])
            swing_well_thp=opt_vals["fixed_thp"][well_idx_to_si]
            opt_vals["fixed_thp"][well_idx_to_si]=-1


            optimization2(PE_server,opt_vals,opt_counter,gap_calc_json_fullpath)
            unit_qgas=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].GasRate"))
            print("SI well:%s, wells shut:%s, Unit Qgas:%.3f, Qgas constraint:%.3f" % \
                    (gor_sorted[well_cnt][0],well_cnt+1,unit_qgas,unit_constraints["qgas_max"]))
            log_text="SI well:%s, wells shut:%s, Unit Qgas:%.3f, Qgas constraint:%.3f" % \
                    (gor_sorted[well_cnt][0],well_cnt+1,unit_qgas,unit_constraints["qgas_max"])
            emit("progress",{"data":log_text})
            sleep(1)

            well_cnt+=1


        if unit_qgas<unit_constraints["qgas_max"]:
            well_cnt-=1
            swing_iters=0
            target_thp_prev=0
            w=gor_sorted[well_cnt][0]

            well_idx_to_open=opt_vals["wellname"].index(gor_sorted[well_cnt][0])
            opt_vals["fixed_thp"][well_idx_to_open]=swing_well_thp

            # get swing well PCs
            welltype=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].TypeWell")
            pc_thp=np.sort(np.array(ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].MANIPRES[0:19]"),dtype=float))[::-1]
            if welltype=="CondensateProducer":
                pc_qgas=np.sort(np.array(ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].PCDATA[0][11][0:19]"),dtype=float))
                pc_qoil=pc_qgas/gor_sorted[well_cnt][1]*1000
            else:
                pc_qoil=np.sort(np.array(ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].PCDATA[0][0][0:19]"),dtype=float))
                pc_qgas=pc_qoil*gor_sorted[well_cnt][1]/1000


            while abs(unit_qgas-unit_constraints["qgas_max"])>0.1 and swing_iters<20:


                qgas_diff=unit_qgas-unit_constraints["qgas_max"]

                well_qgas=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].SolverResults[0].GasRate"))
                well_qoil=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].SolverResults[0].OilRate"))

                well_qgas_target=float(well_qgas-qgas_diff)
                target_thp=np.interp(well_qgas_target,pc_qgas,pc_thp)
                # print(target_thp_prev,target_thp,well_qgas_target,pc_qgas,pc_thp)

                if abs(target_thp-target_thp_prev)<0.001:
                    break

                print("Well:%s, well qgas: %s, Qgasdiff: %s, well Qgas target: %s, Target THP: %s" \
                        % (w,well_qgas,qgas_diff,well_qgas_target,target_thp))
                log_text="Well:%s, well qgas: %.3f, Qgasdiff: %.3f, well Qgas target: %.3f, Target THP: %.3f" \
                        % (w,well_qgas,qgas_diff,well_qgas_target,target_thp)
                emit("progress",{"data":log_text})
                sleep(1)

                # print(w,qgas_diff,target_thp,well_qgas_target,pc_qgas,pc_thp)

                swing_well=opt_vals["wellname"].index(w)
                opt_vals["fixed_thp"][swing_well]=target_thp

                optimization2(PE_server,opt_vals,opt_counter,gap_calc_json_fullpath)
                unit_qgas=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].GasRate"))

                # print(w,target_thp,unit_qgas,"-=-=-=-=-")
                swing_iters+=1
                target_thp_prev=target_thp



    return {"unit_qgas":unit_qgas, "vals":opt_vals}


def run_optimization(session_json,PE_server):

    # units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
    # units_simple=["kpc","u3","u2"]
    #
    #
    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)
    #
    # start=datetime.datetime.now()

    emit("progress",{"data":"Applying Target FWHPs.."})

    status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
    wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
    qgas_max_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQgas") # qgas_max is the main tool for GAP rule based optimizer

    qgas_max=[] # qgas_max values per well to set
    for well in wellname:
        if "target_fwhp" in session_json["well_data"][well]:
            if session_json["well_data"][well]["target_fwhp"]>0.0:
                qgas_max.append(session_json["well_data"][well]["qgas_max"])
            else:
                ut.shut_well(PE_server,well)
                qgas_max.append("")
        else:
            ut.shut_well(PE_server,well)
            qgas_max.append("")

    qgas_max2gap=ut.updatepar(qgas_max_orig,qgas_max,status)
    qgas_max2gap=ut.list2gapstr(qgas_max2gap)
    ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQgas",qgas_max2gap)

    emit("progress",{"data":"Solving Network.."})
    sleep(0.1)

    ut.solve_network_rb(PE_server)
    # ut.set_chokes_calculated(PE_server)


    kpc_qgas_max=session_json["unit_data"]["constraints"]["kpc_qgas_max"]
    u3_qgas_max=session_json["unit_data"]["constraints"]["u3_qgas_max"]
    u2_qgas_max=session_json["unit_data"]["constraints"]["u2_qgas_max"]

    kpc_qoil_max=session_json["unit_data"]["constraints"]["kpc_qoil_max"]
    u3_qoil_max=session_json["unit_data"]["constraints"]["u3_qoil_max"]
    u2_qoil_max=session_json["unit_data"]["constraints"]["u2_qoil_max"]

    kpc_qwat_max=session_json["unit_data"]["constraints"]["kpc_qwat_max"]
    u3_qwat_max=session_json["unit_data"]["constraints"]["u3_qwat_max"]
    u2_qwat_max=session_json["unit_data"]["constraints"]["u2_qwat_max"]


    repeat=1
    tol=0.5
    while repeat==1:

        qgas=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].GasRate",status,"float")
        qoil=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].OilRate",status,"float")
        qwat=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].WatRate",status,"float")

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


        oil_constraint=[0,0,0]
        optimized=0
        for u in range(3):

            unit_qgas_max=setup[u][0]
            unit_qgas=setup[u][1]
            unit_qoil_max=setup[u][2]
            unit_qoil=setup[u][3]
            data_unit=setup[u][4]
            unit=setup[u][5]

            if unit_qgas>unit_qgas_max or unit_qoil>unit_qoil_max:
                optimized=1
                i=0
                while unit_qgas-data_unit[i][2]>unit_qgas_max or unit_qoil-data_unit[i][3]>unit_qoil_max:
                    if session_json["well_data"][data_unit[i][0]]["fixed"]==0:
                        unit_qgas-=data_unit[i][2]
                        unit_qoil-=data_unit[i][3]
                        wells_to_shut.append(data_unit[i][0])
                        ut.shut_well(PE_server,data_unit[i][0])
                        # session_json["well_data"][data_unit[i][0]]["target_fwhp"]=-1
                        emit("progress",{"data":"%s: SI well %s - GOR=%s" % (unit,data_unit[i][0],session_json["well_data"][data_unit[i][0]]["gor"])})
                    else:
                        emit("progress",{"data":"%s: Skipped fixed well %s - GOR=%s ^^" % (unit,data_unit[i][0],session_json["well_data"][data_unit[i][0]]["gor"])})
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
                print(delta_qoil_max,unit_qoil_max,unit_qoil,delta_qgas_max_from_qoil,delta_qgas_max,oil_constraint[u])

                qgas_max=session_json["well_data"][swing_well]["qgas_max"]
                qgas_max2gap=qgas_max+delta_qgas_max
                print(swing_well,qgas_max,qgas_max2gap)
                if qgas_max2gap>10.0:
                    ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+swing_well+"}].MaxQgas",qgas_max2gap)
                    session_json["well_data"][swing_well]["qgas_max"]=qgas_max2gap
                    emit("progress",{"data":"%s: Swing well %s**" % (unit,swing_well)})
                    # sleep(1)
                else:
                    wells_to_shut.append(swing_well)
                    ut.shut_well(PE_server,swing_well)
                    emit("progress",{"data":"%s: Unstable swing well %s shut" % (unit,swing_well)})
                    # sleep(1)



        if optimized==1:
            emit("progress",{"data":"Solving Network.."})
            sleep(0.01)
            ut.solve_network_rb(PE_server)

        # get sep results
        kpc_qgas=ut.get_unit_qgas(PE_server,units[0])
        u3_qgas=ut.get_unit_qgas(PE_server,units[1])
        u2_qgas=ut.get_unit_qgas(PE_server,units[2])
        kpc_qoil=ut.get_unit_qoil(PE_server,units[0])
        u3_qoil=ut.get_unit_qoil(PE_server,units[1])
        u2_qoil=ut.get_unit_qoil(PE_server,units[2])
        kpc_qwat=ut.get_unit_qwat(PE_server,units[0])
        u3_qwat=ut.get_unit_qwat(PE_server,units[1])
        u2_qwat=ut.get_unit_qwat(PE_server,units[2])

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

        emit("progress",{"data":"==============================="})
        emit("progress",{"data":"Qgas=%.1f, Qgas max=%.1f" % (kpc_qgas,kpc_qgas_max)})
        emit("progress",{"data":"Qoil=%.1f, Qoil max=%.1f" % (kpc_qoil,kpc_qoil_max)})
        emit("progress",{"data":"Qwater=%.1f, Qwater max=%.1f" % (kpc_qwat,kpc_qwat_max)})
        emit("progress",{"data":"KPC =========================="})
        emit("progress",{"data":"Qgas=%.1f, Qgas max=%.1f" % (u3_qgas,u3_qgas_max)})
        emit("progress",{"data":"Qoil=%.1f, Qoil max=%.1f" % (u3_qoil,u3_qoil_max)})
        emit("progress",{"data":"Qwater=%.1f, Qwater max=%.1f" % (u3_qwat,u3_qwat_max)})
        emit("progress",{"data":"Unit-3 =========================="})
        emit("progress",{"data":"Qgas=%.1f, Qgas max=%.1f" % (u2_qgas,u2_qgas_max)})
        emit("progress",{"data":"Qoil=%.1f, Qoil max=%.1f" % (u2_qoil,u2_qoil_max)})
        emit("progress",{"data":"Qwater=%.1f, Qwater max=%.1f" % (u2_qwat,u2_qwat_max)})
        emit("progress",{"data":"Unit-2 =========================="})
        sleep(0.01)

        if conv>tol:
            repeat=1
            emit("progress",{"data":"Repeat iteration to converge.. +++++++++++++++++++++++++++++++++++++++++++++++"})
            sleep(0.1)
        else:
            repeat=0


    ut.set_chokes_calculated(PE_server)


    ut.showinterface(PE_server,1)


    dt=datetime.datetime.now()-start
    # emit("progress",{"data":"Calculations complete. Go to Results. <br> Time spent: %s" % dt,"finish":1})
    # sleep(1)

    # PE_server=ut.PE.Stop()
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
