# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""

import numpy as np
from lineup_app import utils as ut


def generate_unit_pc(PE_server,unit,unit_id,well_details,state):

    ut.choose_unit(PE_server,unit)

    status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
    wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
    qoil=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].OilRate",status,"float")
    qgas=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].GasRate",status,"float")
    fwhp=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].FWHP",status,"float")
    dp=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].PControlResult",status,"float")
    gor=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].IPR[0].GOR",status,"float")

    dd=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].Drawdown",status,"float")
    dd_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxDrawdown",status,"float")
    qliq=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].LiqRate",status,"float")
    qliq_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQliq",status,"float")

    results=[wellname,\
            gor.tolist(),\
            fwhp.tolist(),\
            dp.tolist(),\
            qoil.tolist(),\
            qgas.tolist(),\
            dd.tolist(),
            dd_lim.tolist(),
            qliq.tolist(),
            qliq_lim.tolist()]
    results=[list(i) for i in zip(*results)]
    results=sorted(results, key=lambda item: item[1])

    pc={}
    rank={}
    for d,w in enumerate(results):
        this_route=""
        if state[w[0]]["selected_route"]:
            arr=state[w[0]]["selected_route"].split("--")
            this_route={
                "unit":arr[0],
                "rms":arr[1],
                "tl":arr[2],
                "slot":arr[3][5:], # [5:] is to take out "slot " string added in setup
                "comingled":well_details[w[0]]["routes"][0]["comingled"] # borrow from well_details
            }
        else:
            this_route=well_details[w[0]]["routes"][0]



        ###################### FLOWLINE PRESSURE #############################
        if state[w[0]]["selected_route"]:
            for i,r in enumerate(well_details[w[0]]["routes"]):
                wd_route=str(r["unit"])+"--"+str(r["rms"])+"--"+str(r["tl"])+"--slot "+str(r["slot"])
                if wd_route==state[w[0]]["selected_route"]:
                    fl_pipe_os=r["fl_pipe_os"]
        else:
            fl_pipe_os=well_details[w[0]]["routes"][0]["fl_pipe_os"] # take first row for well, no other option

        if fl_pipe_os:
            slotpres=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].PIPE[{"+fl_pipe_os+"}].SolverResults[0].PresOut")
            slotpres=float(slotpres)
        else:
            slotpres=0
        ######################################################################


        pc[d]={
            "wellname":w[0],
            "gor":w[1],
            "fwhp":w[2],
            "fwhp_raw":w[2],
            "dp":w[3],
            "qoil":w[4],
            "qgas":w[5],
            "dd":w[6],
            "dd_lim":round(w[7],1),
            "qliq":w[8],
            "qliq_lim":round(w[9],1),
            "choked":0,
            "rank":d,
            "unit_id":unit_id,
            "route":this_route,
            "connected":well_details[w[0]]["connected"],
            "slotpres":slotpres

        }

    pc_data=pc

    return pc_data



def get_all_unit_pc(well_details,state):

    PE_server=ut.PE.Initialize()

    ut.showinterface(PE_server,0)

    """ SEQUENCE OF UNITS ====================================== """
    units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
    units_simple=["kpc","u3","u2"]
    units_qgas=[]

    pc_data=[]
    for idx,unit in enumerate(units):
        units_qgas.append(ut.get_unit_qgas(PE_server,unit))
        pc=generate_unit_pc(PE_server,unit,idx,well_details,state)
        pc_data.append(pc)

    """ UNMASK ALL UNITS ====================================== """
    ut.unmask_all_units(PE_server)
    ut.solve_network(PE_server)
    ut.showinterface(PE_server,1)

    PE_server=ut.PE.Stop()
    return pc_data
