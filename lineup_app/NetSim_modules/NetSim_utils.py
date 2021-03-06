# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""


import numpy as np
from lineup_app.NetSim_modules import NetSimRoutines as NS
# import NetSimRoutines as NS



def list2gapstr(l):
    l=list(map(str, l))
    return "|".join(l)+"|"
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


def updatepar(par_orig,par,status):
    cnt=0
    for idx,s in enumerate(status):
        if s=="0":
           par_orig[idx]=par[cnt]
           cnt+=1
    return par_orig
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
    data=NS.DoSetAll("seps","masked","1|1|1|","int")
    data=NS.DoSet("seps/"+unit+"/masked",0)
    data=NS.DoCmd("build_network")

    return None


def unmask_all_units():
    data=NS.DoSetAll("seps","masked","0|0|0|","int")
    data=NS.DoCmd("build_network")
    return None
#
#
def solve_network():
    NS.DoCmd("solve_network")
    return None
#
def solve_network_rb():
    NS.DoCmd("optimize_network")
    return None
#
# def showinterface(PE_server,s):
#     PE.DoCmd(PE_server,"GAP.SHOWINTERFACE("+str(s)+")")
#     return None
#
#
def get_unit_qgas(unit):
    return float(NS.DoGet("seps/"+unit+"/results/qgas"))

def get_unit_qoil(unit):
    return float(NS.DoGet("seps/"+unit+"/results/qoil"))

def get_unit_qwat(unit):
    return float(NS.DoGet("seps/"+unit+"/results/qwat"))
#
# def set_unit_pres(PE_server,unit,pres):
#     PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{"+unit+"}].SolverPres[0]",pres)
#     return None
#
#
def shut_well(well):
    NS.DoSet("wells/"+well+"/results/dp",10000)
    NS.DoSet("wells/"+well+"/dp_calc",0)
    return None
#
def open_well(well):
    NS.DoSet("wells/"+well+"/results/dp",0.0)
    NS.DoSet("wells/"+well+"/dp_calc",1)
    return None
#
def set_chokes_calculated():
    dp_calc=get_all("wells","dp_calc")
    dp_calc=list2gapstr([1 for i in range(len(dp_calc))])
    NS.DoSetAll("wells","dp_calc",dp_calc,"int")
    return None
#
def get_filtermasked(item,param,status,t):
    par_orig=get_all(item,param)
    par=filtermasked(par_orig,status,t)
    return par


if __name__=="__main__":
    # data=choose_unit("kpc")
    # unmask_all_units()
    # status=get_all("wells","maskflag")
    # wells=get_filtermasked("wells","label",status,"string")
    # gor=get_filtermasked("wells","gor",status,"float")
    # wct=get_filtermasked("wells","wct",status,"float")
    # pipe_status=get_all("pipes","maskflag")
    # pipes=get_filtermasked("pipes","label",pipe_status,"string")
    d=set_chokes_calculated()
    # print(wells)
    # print(gor)
    # print(wct)
    # print(pipes)
