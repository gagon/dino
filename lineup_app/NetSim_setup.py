# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""

import numpy as np
# from lineup_app import PetexRoutines as PE
from lineup_app import NetSim_utils as nsut


def get_well_data(unit,unit_id,well_data):

    nsut.choose_unit(unit)

    status=nsut.get_all("wells","maskflag")
    wellname=nsut.get_filtermasked("wells","label",status,"string")
    gor=nsut.get_filtermasked("wells","gor",status,"float")
    wct=nsut.get_filtermasked("wells","wct",status,"float")

    # dd_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxDrawdown",status,"float")
    # qliq_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQliq",status,"float")
    pipe_status=nsut.get_all("pipes","maskflag")
    pipes=nsut.get_filtermasked("pipes","label",pipe_status,"string")

    for d,w in enumerate(wellname):

        this_route=-1
        route_cnt=0
        for ri,r in enumerate(well_data[w]["connection"]["routes"]):
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

        well_data[w]["gor"]=gor[d]
        well_data[w]["wct"]=wct[d]
        well_data[w]["unit_id"]=unit_id
        well_data[w]["curr_route"]=this_route
        well_data[w]["route_cnt"]=route_cnt
        well_data[w]["masked"]=0 # set masked 0 to well unmasked(active) in GAP


    return well_data



def get_all_well_data(well_data):

    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)

    """ SEQUENCE OF UNITS ====================================== """
    units=["KPC","Unit-3","Unit-2"]
    units_simple=["kpc","u3","u2"]


    # well_data=[]
    for idx,unit in enumerate(units):

        well_data=get_well_data(units_simple[idx],idx,well_data)

    # set masked 1 to well masked in GAP
    for well,val in well_data.items():
        if not "masked" in val:
            well_data[well]["masked"]=1

    """ UNMASK ALL UNITS ====================================== """
    nsut.unmask_all_units()

    # ut.showinterface(PE_server,1)
    # PE_server=ut.PE.Stop()
    return well_data



def set_unit_routes(well_data):

    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)

    # pipe_status=ut.get_all(PE_server,"GAP.MOD[{PROD}].PIPE[$].MASKFLAG")
    # pipes=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].PIPE[$].Label",pipe_status,"string")

    pipe_status=nsut.get_all("pipes","maskflag")
    pipes=nsut.get_filtermasked("pipes","label",pipe_status,"string")

    for well,val in well_data.items():
        # if well is not masked then check and set routing
        print(well)
        if val["masked"]==0:

            # map selected_route to OS string
            route_open=""
            for i,r in enumerate(val["connection"]["routes"]):
                route=r["route_name"]
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
                for i,r in enumerate(val["connection"]["routes"]):
                    if r["os"]!=route_open:
                        # only first pipe closest to the well can be closed to stop it from the route
                        # above is required so that does not interfere with (close) pipes of comingled wells to that route
                        # temporary logic, more suitable steps to be done
                        if len(r["os"].split(","))>1:
                            if r["os"].split(",")[0]==route_open_arr[0]:
                                nsut.close_pipes(r["os"].split(","))
                            else:
                                nsut.close_pipes([r["os"].split(",")[0]])
                        else:
                            nsut.close_pipes([r["os"].split(",")[0]])


                # then open required route pipes
                for i,r in enumerate(val["connection"]["routes"]):
                    if r["os"]==route_open:
                        nsut.open_pipes(r["os"].split(","))





    # ut.showinterface(PE_server,1)
    # PE_server=ut.PE.Stop()
    return None


def set_sep_pres(sep):

    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)

    # units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
    # if sep["kpc_sep_pres"]:
    #     ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[0] + "}].SolverPres[0]",sep["kpc_sep_pres"])
    # if sep["u3_train1_sep_pres"]:
    #     ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[1] + "}].SolverPres[0]",sep["u3_train1_sep_pres"])
    # if sep["u2_sep_pres"]:
    #     ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].SEP[{" + units[2] + "}].SolverPres[0]",sep["u2_sep_pres"])


    if sep["kpc_sep_pres"]:
        nsut.NS.DoSet("seps/kpc/pres",sep["kpc_sep_pres"])
    if sep["u3_train1_sep_pres"]:
        nsut.NS.DoSet("seps/u3/pres",sep["u3_train1_sep_pres"])
    if sep["u2_sep_pres"]:
        nsut.NS.DoSet("seps/u2/pres",sep["u2_sep_pres"])

    # ut.showinterface(PE_server,1)
    # PE_server=ut.PE.Stop()

    return None


def get_sep_pres():

    # PE_server=ut.PE.Initialize()
    # ut.showinterface(PE_server,0)

    # units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
    units_simple=["kpc","u3","u2"]

    sep={}
    sep["kpc_sep_pres"]=float(nsut.NS.DoGet("seps/" + units_simple[0] +"/pres"))
    sep["u3_train1_sep_pres"]=float(nsut.NS.DoGet("seps/" + units_simple[1] +"/pres"))
    sep["u2_sep_pres"]=float(nsut.NS.DoGet("seps/" + units_simple[2] +"/pres"))

    # temporarily all 4 trains at U3 set equal
    sep["u3_train2_sep_pres"]=sep["u3_train1_sep_pres"]
    sep["u3_train3_sep_pres"]=sep["u3_train1_sep_pres"]
    sep["u3_train4_sep_pres"]=sep["u3_train1_sep_pres"]

    # ut.showinterface(PE_server,1)
    # PE_server=ut.PE.Stop()

    return sep



def get_gap_wells():
    status=nsut.get_all("wells","maskflag")
    wellname=nsut.get_filtermasked("wells","label",status,"string")
    well_data={}
    for well in wellname:
        well_data[well]={}
    return well_data
