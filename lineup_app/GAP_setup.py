# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""

import numpy as np
# from lineup_app import PetexRoutines as PE
from lineup_app import utils as ut


def get_well_data(PE_server,unit,unit_id,well_details):

    ut.choose_unit(PE_server,unit)
    status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
    wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
    gor=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].IPR[0].GOR",status,"float")
    dd_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxDrawdown",status,"float")
    qliq_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQliq",status,"float")
    pipe_status=ut.get_all(PE_server,"GAP.MOD[{PROD}].PIPE[$].MASKFLAG")
    pipes=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].PIPE[$].Label",pipe_status,"string")

    results=[wellname,\
            gor.tolist(),\
            dd_lim.tolist(),
            qliq_lim.tolist()]
    results=[list(i) for i in zip(*results)]
    results=sorted(results, key=lambda item: item[1])

    data={}
    for d,w in enumerate(results):

        this_route=-1
        route_cnt=0
        for ri,r in enumerate(well_details[w[0]]["routes"]):
            if r["os"]:
                route_os=r["os"].split(",")
                if len(route_os)>1:
                    if route_os[0] in pipes and route_os[1] in pipes:
                        this_route=ri
                        route_cnt+=1
                        # break
                else:
                    if route_os[0] in pipes:
                        this_route=ri
                        route_cnt+=1
                        # break


        data[d]={
            "wellname":w[0],
            "gor":round(w[1],1),
            "dd_lim":round(w[2],1),
            "qliq_lim":round(w[3],1),
            "rank":d,
            "unit_id":unit_id,
            "curr_route":this_route,
            "routes":well_details[w[0]]["routes"],
            "connected":well_details[w[0]]["connected"],
            "route_cnt":route_cnt
        }

    return data



def get_all_well_data(well_details):

    PE_server=ut.PE.Initialize()
    ut.showinterface(PE_server,0)

    """ SEQUENCE OF UNITS ====================================== """
    units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
    units_simple=["kpc","u3","u2"]


    well_data=[]
    for idx,unit in enumerate(units):

        data=get_well_data(PE_server,unit,idx,well_details)
        well_data.append(data)

    """ UNMASK ALL UNITS ====================================== """
    ut.unmask_all_units(PE_server)

    ut.showinterface(PE_server,1)

    PE_server=ut.PE.Stop()
    return well_data



def set_unit_routes(well_details,unit_routes):

    PE_server=ut.PE.Initialize()
    ut.showinterface(PE_server,0)

    pipe_status=ut.get_all(PE_server,"GAP.MOD[{PROD}].PIPE[$].MASKFLAG")
    pipes=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].PIPE[$].Label",pipe_status,"string")

    for well,val in unit_routes.items():
        # map selected_route to OS string
        route_open=""
        for i,r in enumerate(well_details[well]["routes"]):
            route=str(r["unit"])+"--"+str(r["rms"])+"--"+str(r["tl"])+"--slot "+str(r["slot"])
            if route==val["selected_route"]:
                route_open=r["os"]

        # check if setting mask/unmask is needed by looking at maskflag of the pipes
        toset=0
        if route_open:
            route_open_arr=route_open.split(",")
            if len(route_open_arr)>1:
                if not route_open_arr[0] in pipes or not route_open_arr[1] in pipes:
                    toset=1
            else:
                if not route_open_arr[0] in pipes:
                    toset=1

        # required to be mask/unmask pipes
        if toset==1:
            # first close all route pipes
            for i,r in enumerate(well_details[well]["routes"]):
                if r["os"]!=route_open:
                    # only first pipe closest to the well can be closed to stop it from the route
                    # above is required so that does not interfere with (close) pipes of comingled wells to that route
                    # temporary logic, more suitable steps to be done
                    if len(r["os"].split(","))>1:
                        if r["os"].split(",")[0]==route_open_arr[0]:
                            ut.close_pipes(PE_server,r["os"].split(","))
                        else:
                            ut.close_pipes(PE_server,[r["os"].split(",")[0]])
                    else:
                        ut.close_pipes(PE_server,[r["os"].split(",")[0]])


            # then open required route pipes
            for i,r in enumerate(well_details[well]["routes"]):
                if r["os"]==route_open:
                    ut.open_pipes(PE_server,r["os"].split(","))




    ut.showinterface(PE_server,1)
    PE_server=ut.PE.Stop()


def set_sep_pres(sep):

    PE_server=ut.PE.Initialize()
    ut.showinterface(PE_server,0)

    units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]

    ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[0] + "}].SolverPres[0]",sep["kpc_sep"])
    ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[1] + "}].SolverPres[0]",sep["u3_sep"])
    ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[2] + "}].SolverPres[0]",sep["u2_sep"])

    ut.showinterface(PE_server,1)
    PE_server=ut.PE.Stop()

    return None


def get_sep_pres():

    PE_server=ut.PE.Initialize()
    ut.showinterface(PE_server,0)

    units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]

    sep={}
    sep["kpc_sep"]=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[0] + "}].SolverPres[0]")
    sep["u3_sep"]=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[1] + "}].SolverPres[0]")
    sep["u2_sep"]=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[2] + "}].SolverPres[0]")

    ut.showinterface(PE_server,1)
    PE_server=ut.PE.Stop()

    return sep
