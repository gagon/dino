# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""


import numpy as np
from lineup_app import NetSimRoutines as NS
# import NetSimRoutines as NS



# def list2gapstr(l):
#     l=list(map(str, l))
#     return "|".join(l)+"|"
#
#
def filtermasked(par_orig,status,st):
    fpar=[]
    for idx,s in enumerate(status):
        if s=="0":
           fpar.append(par_orig[idx])
    if st=="float":
        return np.array(fpar,dtype=float)
    else:
        return fpar
#

# def updatepar(par_orig,par,status):
#     cnt=0
#     for idx,s in enumerate(status):
#         if s=="0":
#            par_orig[idx]=par[cnt]
#            cnt+=1
#     return par_orig
#
#
def get_all(item,param):
    return NS.DoGetAll(item,param).split("|")[:-1]
#
def close_pipes(pipe_close):
    for p in pipe_close:
        pipe="pipes/"+p+"/masked"
        NS.DoSet(pipe,1)
    NS.DoCmd("build_network")
    return None
#
def open_pipes(pipe_open):
    for p in pipe_open:
        pipe="pipes/"+p+"/masked"
        NS.DoSet(pipe,0)
    NS.DoCmd("build_network")
    return None

#
# def set_pipes(PE_server,pipe_close,pipe_open):
#     for p in pipe_close:
#         PE.DoCmd(PE_server,"GAP.MOD[{PROD}].PIPE[{"+p+"}].MASK()")
#     for p in pipe_open:
#         PE.DoCmd(PE_server,"GAP.MOD[{PROD}].PIPE[{"+p+"}].UNMASK()")
#     return None
#
#
#
def choose_unit(unit):
    data=NS.DoSetAll("seps","masked","1|1|1|")
    data=NS.DoSet("seps/"+unit+"/masked",0)
    data=NS.DoCmd("build_network")

    return None


def unmask_all_units():
    data=NS.DoSetAll("seps","masked","0|0|0|")
    data=NS.DoCmd("build_network")
    return None
#
#
# def solve_network(PE_server):
#     PE.DoCmd(PE_server,"GAP.SOLVENETWORK(0, MOD[0])")
#     return None
#
# def solve_network_rb(PE_server):
#     PE.DoCmd(PE_server,"GAP.SOLVENETWORK(3, MOD[0])")
#     return None
#
# def showinterface(PE_server,s):
#     PE.DoCmd(PE_server,"GAP.SHOWINTERFACE("+str(s)+")")
#     return None
#
#
# def get_unit_qgas(PE_server,unit):
#     return float(PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].GasRate"))
#
# def get_unit_qoil(PE_server,unit):
#     return float(PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].OilRate"))
#
# def get_unit_qwat(PE_server,unit):
#     return float(PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverResults[0].WatRate"))
#
# def set_unit_pres(PE_server,unit,pres):
#     PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverPres[0]",pres)
#     return None
#
#
# def shut_well(PE_server,well):
#     PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].DPControl","FIXEDVALUE")
#     PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].DPControlValue",10000)
#     return None
#
# def open_well(PE_server,well):
#     PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].DPControl","CALCULATED")
#     PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].DPControlValue",0)
#     return None
#
# def set_chokes_calculated(PE_server):
#     PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[$].DPControl","CALCULATED")
#     PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[$].DPControlValue",0)
#     return None
#
def get_filtermasked(item,param,status,t):
    par_orig=get_all(item,param)
    par=filtermasked(par_orig,status,t)
    return par


if __name__=="__main__":
    # data=choose_unit("kpc")
    unmask_all_units()
    status=get_all("wells","maskflag")
    wells=get_filtermasked("wells","label",status,"string")
    gor=get_filtermasked("wells","gor",status,"float")
    wct=get_filtermasked("wells","wct",status,"float")
    pipe_status=get_all("pipes","maskflag")
    pipes=get_filtermasked("pipes","label",pipe_status,"string")
    print(wells)
    print(gor)
    print(wct)
    print(pipes)
