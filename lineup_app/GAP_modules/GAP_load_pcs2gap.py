# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 14:34:45 2016

@author: zhumbo
"""

import numpy as np
# from lineup_app import PetexRoutines as PE
from lineup_app.GAP_modules import GAP_utils as ut
from flask_socketio import SocketIO, send, emit
import gevent
from gevent import monkey, sleep



def load_pcs2gap(well_pcs):

    PE_server=ut.PE.Initialize()
    ut.showinterface(PE_server,0)

    wells=sorted(well_pcs.keys())

    status=ut.get_all(PE_server,"GAP.MOD[{PROD}].WELL[$].MASKFLAG") # get status of wells in GAP model
    gap_wellnames=ut.get_filtermasked(PE_server,"GAP.MOD[{PROD}].WELL[$].Label",status,"string") # get wellnames of unmasked wells

    print(wells)
    for well in wells:

        if well in gap_wellnames: # make sure well exists in GAP model
            print(well)

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
            wcs=ut.list2gapstr(np.zeros(20)+well_pcs[well]["wct"]*100.0)
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
                ut.PE.DoSet(PE_server,"GAP.MOD[{PROD}].WELL[{"+well+"}].IPR[0].WCT",well_pcs[well]["wct"]*100.0)

            emit("load_progress",{"data":"Loaded PCs to GAP for well %s, GOR=%.1f sm3/sm3, Watercut=%.1f %%, MAP=%.1f bar" % (well,well_pcs[well]["gor"],well_pcs[well]["wct"]*100.0,well_pcs[well]["map"])})
            sleep(0.1)



    ut.showinterface(PE_server,1)
    PE_server=ut.PE.Stop()



    return None
