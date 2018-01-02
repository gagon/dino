# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""

import numpy as np
from lineup_app import utils as ut
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

#
#
# def xl_generate_unit_pc(unit,unit_id,well_details,state,xlwells,xlunits,xlgap_wb):
#
#     # ut.choose_unit(PE_server,unit)
#
#     # status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
#     # wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
#     # qoil=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].OilRate",status,"float")
#     # qgas=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].GasRate",status,"float")
#     # fwhp=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].FWHP",status,"float")
#     # dp=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].PControlResult",status,"float")
#     # gor=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].IPR[0].GOR",status,"float")
#     #
#     # dd=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].Drawdown",status,"float")
#     # dd_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxDrawdown",status,"float")
#     # qliq=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].LiqRate",status,"float")
#     # qliq_lim=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].MaxQliq",status,"float")
#
#     wellname=[]
#     qoil=[]
#     qgas=[]
#     fwhp=[]
#     dp=[]
#     gor=[]
#     dd=[]
#     dd_lim=[]
#     qliq=[]
#     qliq_lim=[]
#
#     r=2
#     while xlwells.range((r,1)).value!=None:
#         if xlwells.range((r,3)).value==unit:
#             wellname.append(wellname_type(xlwells.range((r,1)).value)) # to avoid decimal point coming from excel
#             qoil.append(xlwells.range((r,8)).value)
#             qgas.append(xlwells.range((r,9)).value)
#             fwhp.append(xlwells.range((r,4)).value)
#             dp.append(xlwells.range((r,6)).value)
#             gor.append(xlwells.range((r,7)).value)
#             dd.append(xlwells.range((r,12)).value)
#             dd_lim.append(100)
#             qliq.append(xlwells.range((r,8)).value)
#             qliq_lim.append(2500)
#         r+=1
#
#
#
#     results=[wellname,\
#             gor,\
#             fwhp,\
#             dp,\
#             qoil,\
#             qgas,\
#             dd,
#             dd_lim,
#             qliq,
#             qliq_lim]
#     results=[list(i) for i in zip(*results)]
#     results=sorted(results, key=lambda item: item[1])
#
#     pc={}
#     rank={}
#     for d,w in enumerate(results):
#         this_route=""
#         if state[w[0]]["selected_route"]:
#             arr=state[w[0]]["selected_route"].split("--")
#             this_route={
#                 "unit":arr[0],
#                 "rms":arr[1],
#                 "tl":arr[2],
#                 "slot":arr[3][5:], # [5:] is to take out "slot " string added in setup
#                 "comingled":well_details[w[0]]["routes"][0]["comingled"] # borrow from well_details
#             }
#         else:
#             this_route=well_details[w[0]]["routes"][0]
#
#
#
#         ###################### FLOWLINE PRESSURE #############################
#         # if state[w[0]]["selected_route"]:
#         #     for i,r in enumerate(well_details[w[0]]["routes"]):
#         #         wd_route=str(r["unit"])+"--"+str(r["rms"])+"--"+str(r["tl"])+"--slot "+str(r["slot"])
#         #         if wd_route==state[w[0]]["selected_route"]:
#         #             fl_pipe_os=r["fl_pipe_os"]
#         # else:
#         #     fl_pipe_os=well_details[w[0]]["routes"][0]["fl_pipe_os"] # take first row for well, no other option
#         #
#         # if fl_pipe_os:
#         #     slotpres=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].PIPE[{"+fl_pipe_os+"}].SolverResults[0].PresOut")
#         #     slotpres=float(slotpres)
#         # else:
#         #     slotpres=0
#         slotpres=0
#         ######################################################################
#
#
#         pc[w[0]]={
#             "wellname":w[0],
#             "gor":w[1],
#             "fwhp":w[2],
#             "fwhp_raw":w[2],
#             "dp":w[3],
#             "qoil":w[4],
#             "qgas":w[5],
#             "dd":w[6],
#             "dd_lim":round(w[7],1),
#             "qliq":w[8],
#             "qliq_lim":round(w[9],1),
#             "choked":0,
#             "rank":d,
#             "unit_id":unit_id,
#             "route":this_route,
#             "connected":well_details[w[0]]["connected"],
#             "slotpres":slotpres
#
#         }
#
#     pc_data=pc
#
#     return pc_data
#
#
#
# def xl_get_all_unit_pc(well_details,state):
#
#     xlwells,xlunits,xlgap_wb=xlgap_conn()
#
#     """ SEQUENCE OF UNITS ====================================== """
#     units=["KPC","U3","U2"]
#     units_simple=["kpc","u3","u2"]
#     # units_qgas=[]
#
#     pc_data=[]
#     for idx,unit in enumerate(units):
#         # units_qgas.append(ut.get_unit_qgas(PE_server,unit))
#         # pc=generate_unit_pc(PE_server,unit,idx,well_details,state)
#         pc=xl_generate_unit_pc(unit,idx,well_details,state,xlwells,xlunits,xlgap_wb)
#
#         pc_data.append(pc)
#
#     # """ UNMASK ALL UNITS ====================================== """
#     # ut.unmask_all_units(PE_server)
#     # ut.solve_network(PE_server)
#     # ut.showinterface(PE_server,1)
#     #
#     # PE_server=ut.PE.Stop()
#     return pc_data





def xl_get_well_data(unit,unit_id,well_data):

    xlwells,xlunits,xlgap_wb=xlgap_conn()
    wellname=[]
    gor=[]
    xlroutes=[]
    qoil=[]
    qgas=[]
    fwhp=[]
    dp=[]

    r=2
    while xlwells.range((r,1)).value!=None:
        if xlwells.range((r,3)).value==unit:
            wellname.append(wellname_type(xlwells.range((r,1)).value)) # to avoid decimal point coming from excel
            gor.append(xlwells.range((r,7)).value)
            xlroutes.append(str(xlwells.range((r,2)).value))
            qoil.append(xlwells.range((r,8)).value)
            qgas.append(xlwells.range((r,9)).value)
            fwhp.append(xlwells.range((r,4)).value)
            dp.append(xlwells.range((r,6)).value)
        r+=1

    for d,w in enumerate(wellname):

        this_route=-1
        route_cnt=0
        for ri,r in enumerate(well_data[w]["connection"]["routes"]):
            if r["os"] == xlroutes[d]:
                this_route=ri
                route_cnt+=1

        well_data[w]["gor"]=round(gor[d],1)
        well_data[w]["unit_id"]=unit_id
        well_data[w]["curr_route"]=this_route
        well_data[w]["route_cnt"]=route_cnt
        well_data[w]["qoil"]=qoil[d]
        well_data[w]["qgas"]=qgas[d]
        well_data[w]["fwhp"]=fwhp[d]
        well_data[w]["dp"]=dp[d]
        well_data[w]["slotpres"]=0.0


    return well_data



def xl_get_all_well_data(well_data):

    """ SEQUENCE OF UNITS ====================================== """
    units=["KPC","U3","U2"]
    # units_simple=["kpc","u3","u2"]

    for idx,unit in enumerate(units):
        well_data=xl_get_well_data(unit,idx,well_data)

    return well_data
