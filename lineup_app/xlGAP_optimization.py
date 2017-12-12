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

""" Excel wells colunm mapping ============================"""

well_params={
    "Wellname":1,
    "Active pipe string":2,
    "Unit":3,
    "FWHP":4,
    "FL pres":5,
    "dPChoke":6,
    "GOR":7,
    "Qoil":8,
    "Qgas":9,
    "FBHP":10,
    "SBHP":11,
    "DD":12,
    "o3":13,
    "o2":14,
    "o1":15,
    "oC":16,
    "b3":17,
    "b2":18,
    "b1":19,
    "bC":20,
}

"""========================================================"""

import numpy as np
from lineup_app import utils as ut
from xlrd import open_workbook,xldate_as_tuple
import datetime
from flask_socketio import SocketIO, send, emit
import gevent
from gevent import monkey, sleep
import os
import xlwings as xw

def xlgap_conn():
    # get current directory using os library
    dirname, filename = os.path.split(os.path.abspath(__file__))
    # construct excel file full path
    xl_fullpath=os.path.join(dirname,r'static\xlgap.xlsx')
    # load excel file
    xlgap_wb = xw.Book(xl_fullpath)
    # load sheet
    xlwells=xlgap_wb.sheets['Wells']
    xlunits=xlgap_wb.sheets['Units']
    # get max row number. Needed for furture looping through sheet rows
    #row_cnt = conns.max_row
    return xlwells,xlunits,xlgap_wb

def wellname_type(wn):
    if type(wn) is not str: # to avoid decimal point coming from excel wellnames
        wn=int(wn)
    return str(wn)





def xl_optimization2(opt_vals,opt_counter,xlwells,xlunits,xlgap_wb):
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
        # emit("progress",{"data":"conv=%.3f,iter=%s,perts=%.3f,lasterror=%.3f,massdif=%.3f,presdiff=%.3f" % \
        #         (conv,iter_,perts,lasterror,maxmassbaldif,maxpresbaldif)})
        # sleep(0.1)



    if conv<=conv_tol or perts<pert_tol:
        return 1
    else:
        return 0




def xl_optimization1(unit,unit_constraints,opt_vals,xlwells,xlunits,xlgap_wb):
    opt_counter=0
    # optimization2(PE_server,opt_vals,opt_counter)
    xl_optimization2(opt_vals,opt_counter,xlwells,xlunits,xlgap_wb)
    # unit_qgas=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].GasRate"))
    unit_qgas=xl_get_unit_qgas(xlunits)

    opt_counter=1

    if unit_qgas>unit_constraints["qgas"]:

        gor_sorted=[\
                opt_vals["wellname"],\
                opt_vals["gor"],\
                opt_vals["fixed_thp"],\
                opt_vals["in_opt"]\
                ]

        gor_sorted=[list(i) for i in zip(*gor_sorted)]
        gor_sorted=sorted(gor_sorted, key=lambda item: item[1],reverse=True)


        well_cnt=0
        # unit_qgas=float(50000)

        while unit_qgas>unit_constraints["qgas"]:
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


            xl_optimization2(opt_vals,opt_counter,xlwells,xlunits,xlgap_wb)
            # unit_qgas=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].GasRate"))
            unit_qgas=xl_get_unit_qgas(xlunits)

            print("SI well:%s, wells shut:%s, Unit Qgas:%.3f, Qgas constraint:%.3f" % \
                    (gor_sorted[well_cnt][0],well_cnt+1,unit_qgas,unit_constraints["qgas"]))
            log_text="SI well:%s, wells shut:%s, Unit Qgas:%.3f, Qgas constraint:%.3f" % \
                    (gor_sorted[well_cnt][0],well_cnt+1,unit_qgas,unit_constraints["qgas"])
            emit("progress",{"data":log_text})
            sleep(1)

            well_cnt+=1


        if unit_qgas<unit_constraints["qgas"]:
            well_cnt-=1
            swing_iters=0
            target_thp_prev=0
            w=gor_sorted[well_cnt][0]

            well_idx_to_open=opt_vals["wellname"].index(gor_sorted[well_cnt][0])
            opt_vals["fixed_thp"][well_idx_to_open]=swing_well_thp

            # # get swing well PCs
            # welltype=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].TypeWell")
            # pc_thp=np.sort(np.array(ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].MANIPRES[0:19]"),dtype=float))[::-1]
            # if welltype=="CondensateProducer":
            #     pc_qgas=np.sort(np.array(ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].PCDATA[0][11][0:19]"),dtype=float))
            #     pc_qoil=pc_qgas/gor_sorted[well_cnt][1]*1000
            # else:
            #     pc_qoil=np.sort(np.array(ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].PCDATA[0][0][0:19]"),dtype=float))
            #     pc_qgas=pc_qoil*gor_sorted[well_cnt][1]/1000


            while abs(unit_qgas-unit_constraints["qgas"])>0.1 and swing_iters<20:


                qgas_diff=unit_qgas-unit_constraints["qgas"]

                # well_qgas=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].SolverResults[0].GasRate"))
                # well_qoil=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].WELL[{" + w + "}].SolverResults[0].OilRate"))

                # well_qgas,well_qoil=xl_get_well_rates(xlwells,w)
                well_qgas=xl_get_well_results(xlwells,w,"Qgas")
                well_qoil=xl_get_well_results(xlwells,w,"Qoil")

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

                xl_optimization2(opt_vals,opt_counter,xlwells,xlunits,xlgap_wb)
                # unit_qgas=float(ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].GasRate"))
                unit_qgas=xl_get_unit_qgas(xlunits)

                # print(w,target_thp,unit_qgas,"-=-=-=-=-")
                swing_iters+=1
                target_thp_prev=target_thp



    return {"unit_qgas":unit_qgas, "vals":opt_vals}


def xl_run_optimization(state):

    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)
    xlwells,xlunits,xlgap_wb=xlgap_conn()

    start=datetime.datetime.now()

    fixed_thp_wells={}
    for w,v in state["wells"].items():
        if v["fwhp"]:
            fixed_thp_wells[w]=float(v["fwhp"])



    """ SEQUENCE OF UNITS ====================================== """
    units=["KPC","U3","U2"]
    units_simple=["kpc","u3","u2"]


    """ GET WELLNAMES AND LIMITS FROM GAP ====================================== """
    # wellname_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].Label")
    # dd_lim_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxDrawdown")
    # qliq_lim_orig=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQliq")


    # ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[0] + "}].SolverPres[0]",state["sep"]["kpc_sep"])
    # ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[1] + "}].SolverPres[0]",state["sep"]["u3_sep"])
    # ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[2] + "}].SolverPres[0]",state["sep"]["u2_sep"])



    xlunits.range((2,4)).value=state["sep"]["kpc_sep"]
    xlunits.range((3,4)).value=state["sep"]["u2_sep"]
    xlunits.range((4,4)).value=state["sep"]["u3_sep"]



    post_opt_state={}

    """ ITERATE THROUGH UNITS AND SOLVE POTENTIAL ====================================== """
    for idx,unit in enumerate(units):

        print("Solving: %s" % unit)
        emit("progress",{"data":"Solving: %s ================" % unit})
        sleep(1)

        unit_constraints=state["constraints"][units_simple[idx]]

        # ut.choose_unit(PE_server,unit)
#        break

        """ GET WELLNAMES, LIMITS AND STATUS FROM GAP ====================================== """
        # status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
        # wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
        # dd_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxDrawdown",status,"float")
        # qliq_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQliq",status,"float")
        #
        #
        #
        # # qoil=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].OilRate",status,"float")
        # # qgas=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].GasRate",status,"float")
        #
        # dp=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].PControlResult",status,"float")
        # gor=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].IPR[0].GOR",status,"float")



        wellname=xl_get_allwell_results(xlwells,unit,"Wellname")
        dp=xl_get_allwell_results(xlwells,unit,"dPChoke")
        gor=xl_get_allwell_results(xlwells,unit,"GOR")
        dd_lim=[100 for i in range(len(gor))]
        qliq_lim=[2500 for i in range(len(gor))]
        #
        # r=2
        # while xlwells.range((r,1)).value!=None:
        #     if xlwells.range((r,3)).value==unit:
        #         wellname.append(wellname_type(xlwells.range((r,1)).value)) # to avoid decimal point coming from excel
        #         dp.append(xlwells.range((r,6)).value)
        #         gor.append(xlwells.range((r,7)).value)
        #         dd_lim.append(100)
        #         qliq_lim.append(2500)
        #     r+=1



        # define fixed thp, match order in table and order in GAP
        fixed_thp=np.zeros(len(wellname))
        in_opt=np.zeros(len(wellname))

        for d,w in enumerate(wellname):
            fixed_thp[d]=state["wells"][w]["fwhp"]
            in_opt[d]=state["wells"][w]["in_opt"]

        # for w,t in state["wells"].items():
        #     for d,d_ in enumerate(wellname):
        #         if w==d_:
        #             fixed_thp[d]=t["fwhp"]
        #             in_opt[d]=t["in_opt"]

        # fixed_thp=np.zeros(len(wellname))
        # in_opt=np.zeros(len(wellname))
        # for w,t in fixed_thp_wells.items():
        #     for d,d_ in enumerate(wellname):
        #         if w==d_:
        #             fixed_thp[d]=t


        opt_vals={
        "status":status,
        "wellname":wellname,
        "dd_lim":dd_lim,
        "qliq_lim":qliq_lim,
        "fixed_thp":fixed_thp,
        "dp":dp,
        "gor":gor,
        "in_opt":in_opt
        }

        # this was added to avoid inconsistency in solving only 1 sep versus all seps. slightly different results even with exactly same dPs.
        # ut.unmask_all_units(PE_server)

        """ POTENTIAL SOLVE ====================================== """
        # opt=optimization1(PE_server,unit,unit_constraints,opt_vals)
        opt=xl_optimization1(unit,unit_constraints,opt_vals,xlwells,xlunits,xlgap_wb)
        emit("progress",{"data":"Unit Qgas: %.3f, Constraint: %s" % (opt["unit_qgas"],unit_constraints["qgas"])})
        sleep(1)
        # break

        for i,w in enumerate(opt["vals"]["wellname"]):
            post_opt_state[w]={"fwhp":opt["vals"]["fixed_thp"][i]}

    """ UNMASK ALL UNITS ====================================== """
    # ut.unmask_all_units(PE_server)

    """ GAP SOLVE NETWORK ====================================== """
    # ut.solve_network(PE_server)
    # ut.showinterface(PE_server,1)


    dt=datetime.datetime.now()-start
    emit("progress",{"data":"Calculations complete. Go to Results. <br> Time spent: %s" % dt})
    sleep(1)

    # print(post_opt_state)
    xlgap_wb.save()
    # PE_server=ut.PE.Stop()
    return post_opt_state


def xl_get_unit_qgas(xlunits):
    r=2
    while xlunits.range((r,1)).value!=None:
        if xlunits.range((r,1)).value==unit:
            unit_qgas=float(xlunits.range((r,3)).value)
            break
        r+=1
    return float(unit_qgas)


def xl_get_well_rates(xlwells,well):
    r=2
    while xlwells.range((r,1)).value!=None:
        if wellname_type(xlwells.range((r,1)).value)==well:
            well_qgas=float(xlwells.range((r,9)).value)
            well_qoil=float(xlwells.range((r,8)).value)
            break
        r+=1
    return well_qgas,well_qoil


def xl_get_well_results(xlwells,well,param):
    param_idx=well_params[param]
    r=2
    while xlwells.range((r,1)).value!=None:
        if wellname_type(xlwells.range((r,1)).value)==well:
            well_result=float(xlwells.range((r,param_idx)).value)
            break
        r+=1
    return well_result


def xl_get_allwell_results(xlwells,unit,param):
    param_idx=well_params[param]
    unit_idx=well_params["Unit"]
    allwell_result=[]
    r=2
    while xlwells.range((r,1)).value!=None:
        if xlwells.range((r,unit_idx)).value==unit:
            if param=="Wellname":
                allwell_result.append(wellname_type(xlwells.range((r,param_idx)).value))
            else:
                allwell_result.append(float(xlwells.range((r,param_idx)).value))
        r+=1
    return allwell_result
