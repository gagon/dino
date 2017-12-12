# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""

import numpy as np
# from lineup_app import PetexRoutines as PE
from lineup_app import utils as ut
from flask_socketio import SocketIO, send, emit
import gevent
from gevent import monkey, sleep



def load_pcs2gap(well_pcs):

    PE_server=ut.PE.Initialize()
    ut.showinterface(PE_server,0)

    wells=sorted(well_pcs.keys())
    print(wells)
    for well in wells:
        print(well)
        emit("load_progress",{"data":"Loading PCs for well %s" % well})
        sleep(0.1)

        welltype=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].TypeWell")

        zero_arr=np.zeros(20)+1.1
        zero_arr=ut.list2gapstr(zero_arr)
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].MANIPRES[0:19]",zero_arr)
        if welltype=="CondensateProducer":
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][11][0:19]",zero_arr) #gasrate
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][12][0:19]",zero_arr) #wgr
        else:
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][0][0:19]",zero_arr) #liqrate
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][1][0:19]",zero_arr) #wc
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][2][0:19]",zero_arr)
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][3][0:19]",zero_arr)
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][7][0:19]",zero_arr)


        thps=ut.list2gapstr(well_pcs[well]["pc"]["thps"])
        qliqs=ut.list2gapstr(well_pcs[well]["pc"]["qliqs"])
        qgas=ut.list2gapstr(well_pcs[well]["pc"]["qgas"])
        wcs=ut.list2gapstr(np.zeros(20)+well_pcs[well]["wc"]*100.0)
        wgrs=ut.list2gapstr(np.zeros(20)+well_pcs[well]["wgr"])
        gors=ut.list2gapstr(np.zeros(20)+well_pcs[well]["gor"])
        fbhps=ut.list2gapstr(well_pcs[well]["pc"]["fbhps"])
        temps=ut.list2gapstr(well_pcs[well]["pc"]["temps"])

        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].MANIPRES[0:19]",thps)
        if welltype=="CondensateProducer":
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][11][0:19]",qgas)
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][12][0:19]",wgrs)
        else:
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][0][0:19]",qliqs)
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][1][0:19]",wcs)
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][2][0:19]",gors)
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][3][0:19]",fbhps)
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].PCDATA[0][7][0:19]",temps)


        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].IPR[0].ResPres",well_pcs[well]["sbhp"])
        ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].IPR[0].GOR",well_pcs[well]["gor"])
        if welltype=="CondensateProducer":
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].IPR[0].WGR",well_pcs[well]["wgr"])
        else:
            ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].IPR[0].WCT",well_pcs[well]["wc"]*100.0)




    ut.showinterface(PE_server,1)
    PE_server=ut.PE.Stop()



    # ut.choose_unit(PE_server,unit)
    # status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
    # wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
    # gor=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].IPR[0].GOR",status,"float")
    # dd_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxDrawdown",status,"float")
    # qliq_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQliq",status,"float")
    #
    # results=[wellname,\
    #         gor.tolist(),\
    #         dd_lim.tolist(),
    #         qliq_lim.tolist()]
    # results=[list(i) for i in zip(*results)]
    # results=sorted(results, key=lambda item: item[1])
    #
    # data={}
    # for d,w in enumerate(results):
    #
    #     data[d]={
    #         "wellname":w[0],
    #         "gor":round(w[1],1),
    #         "dd_lim":round(w[2],1),
    #         "qliq_lim":round(w[3],1),
    #         "rank":d,
    #         "unit_id":unit_id,
    #     }

    return None



# def get_all_well_data():
#     print("kello")
#     PE_server=ut.PE.Initialize()
#
#     ut.showinterface(PE_server,0)
#
#     """ SEQUENCE OF UNITS ====================================== """
#     units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
#     units_simple=["kpc","u3","u2"]
#
#
#     well_data=[]
#     for idx,unit in enumerate(units):
#
#         data=get_well_data(PE_server,unit,idx)
#         well_data.append(data)
#
#     """ UNMASK ALL UNITS ====================================== """
#     ut.unmask_all_units(PE_server)
#
#     ut.showinterface(PE_server,1)
#
#     PE_server=ut.PE.Stop()
#     return well_data
#
#
#
# def set_unit_routes(well_details,unit_routes):
#
#     PE_server=ut.PE.Initialize()
#     ut.showinterface(PE_server,0)
#
#
#     pipe_status=ut.get_all(PE_server,"GAP.MOD[{PROD}].PIPE[$].MASKFLAG")
#     pipes=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].PIPE[$].Label",pipe_status,"string")
#
#     # print(pipes)
#
#     # print(unit_routes)
#
#     for well,val in unit_routes.items():
#
#         if unit_routes[well]["selected_unit"] and well_details[well]["os2"]:
#             # print(unit_routes[well]["selected_unit"],well_details[well]["unit1"])
#             if well_details[well]["unit1"]==unit_routes[well]["selected_unit"]:
#                 pipe_close=well_details[well]["os2"]
#                 pipe_open=well_details[well]["os1"]
#             else:
#                 pipe_close=well_details[well]["os1"]
#                 pipe_open=well_details[well]["os2"]
#             #
#             # pipe_close="dummy_pipe1"
#             # pipe_open="dummy_pipe2"
#             print(well,pipe_open,pipe_close)
#             if pipe_close in pipes and pipe_open not in pipes:
#                 print(pipe_open,pipe_close)
#                 ut.set_pipes(PE_server,pipe_close,pipe_open)
#
#
#     ut.showinterface(PE_server,1)
#     PE_server=ut.PE.Stop()
