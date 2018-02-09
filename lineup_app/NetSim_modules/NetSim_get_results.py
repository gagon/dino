# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""

import numpy as np
# from lineup_app import utils as ut
from lineup_app.NetSim_modules import NetSim_utils as nsut


def get_well_data(well_data,afs):


    # status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG")
    # wellname=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string")
    # gor=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].IPR[0].GOR",status,"float")
    # qoil=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].OilRate",status,"float")
    # qgas=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].GasRate",status,"float")
    # qwat=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].WatRate",status,"float")
    # fwhp=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].FWHP",status,"float")
    # dp=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].SolverResults[0].PControlResult",status,"float")

    status=nsut.get_all("wells","maskflag")
    wellname=nsut.get_filtermasked("wells","label",status,"string")
    # gor=nsut.get_filtermasked("wells","gor",status,"float")
    # wct=nsut.get_filtermasked("wells","wct",status,"float")
    qoil=nsut.get_filtermasked("wells","results/qoil",status,"float")
    qgas=nsut.get_filtermasked("wells","results/qgas",status,"float")
    qwat=nsut.get_filtermasked("wells","results/qwat",status,"float")
    fwhp=nsut.get_filtermasked("wells","results/fwhp",status,"float")
    dp=nsut.get_filtermasked("wells","results/dp",status,"float")


    for d,w in enumerate(wellname):

        ###################### FLOWLINE PRESSURE #############################
        # if well_data[w]["selected_route"]:
        #     for i,r in enumerate(well_data[w]["connection"]["routes"]):
        #         # wd_route=str(r["unit"])+"--"+str(r["rms"])+"--"+str(r["tl"])+"--slot "+str(r["slot"])
        #         wd_route=r["route_name"]
        #         if wd_route==well_data[w]["selected_route"]:
        #             fl_pipe_os=r["fl_pipe_os"]
        # else:
        #     fl_pipe_os=well_data[w]["connection"]["routes"][0]["fl_pipe_os"] # take first row for well, no other option
        #
        # if fl_pipe_os:
        #     # slotpres=ut.PE.DoGet(PE_server,"GAP.MOD[{PROD}].PIPE[{"+fl_pipe_os+"}].SolverResults[0].PresOut")
        #     slotpres=nsut.NS.DoGet("pipes/"+fl_pipe_os+"/results/pres")
        #     slotpres=float(slotpres)
        # else:
        #     slotpres=0
        slotpres=0
        ######################################################################


        well_data[w]["qoil"]=qoil[d]*afs[well_data[w]["unit_id"]][0] # oil rate multiplied by af_oil
        well_data[w]["qgas"]=qgas[d]*afs[well_data[w]["unit_id"]][1] # gas rate multiplied by af_gas
        well_data[w]["qwat"]=qwat[d]*afs[well_data[w]["unit_id"]][2] # water rate multiplied by af_wat
        well_data[w]["fwhp"]=fwhp[d]
        well_data[w]["dp"]=dp[d]
        well_data[w]["slotpres"]=slotpres

    return well_data



def get_all_well_data(session_json):

    # PE_server=ut.PE.Initialize()

    """ SEQUENCE OF UNITS ====================================== """
    units=["KPC MP A","UN3 - TR1","UN2 - Slug01"]
    units_simple=["kpc","u3","u2"]

    afs=[
        [
            session_json["fb_data"]["wells"]["kpc"]["af_oil"],
            session_json["fb_data"]["wells"]["kpc"]["af_gas"],
            session_json["fb_data"]["wells"]["kpc"]["af_wat"]
        ],
        [
            session_json["fb_data"]["wells"]["u3"]["af_oil"],
            session_json["fb_data"]["wells"]["u3"]["af_gas"],
            session_json["fb_data"]["wells"]["u3"]["af_wat"]
        ],
        [
            session_json["fb_data"]["wells"]["u2"]["af_oil"],
            session_json["fb_data"]["wells"]["u2"]["af_gas"],
            session_json["fb_data"]["wells"]["u2"]["af_wat"]
        ]
    ]

    well_data=session_json["well_data"]

    well_data=get_well_data(well_data,afs)

    # PE_server=ut.PE.Stop()
    return well_data
