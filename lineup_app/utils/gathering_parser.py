# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 14:27:08 2017

@author: zhumbo
"""

from openpyxl import load_workbook
import os
import numpy as np
import xlrd
import re
# from flask_socketio import SocketIO, send, emit
# import gevent
# from gevent import monkey, sleep



def read_files(folder):
    allfiles = []
    for dirpath, subdirs, files in os.walk(folder):
        for x in files:
            if x.endswith(".xls"):
                allfiles.append(os.path.join(dirpath, x))
    return allfiles

def find(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]

def get_wellnames(book):
    sheet = book.sheet_by_name("Wellnames")
    wells=[]
    for r in range(1,sheet.nrows):
        w1=str(sheet.cell_value(r, 2)).replace('.0','')
        w2=str(sheet.cell_value(r, 1)).replace('.0','')
        wells.append({w1:w2})
    return wells

def get_rmss(book):
    sheet = book.sheet_by_name("Gathering")
    rmss={}
    for r in range(1,sheet.nrows):
        rmss[sheet.cell_value(r, 0)]={
            "unit":sheet.cell_value(r, 1),
            "rms":sheet.cell_value(r, 2),
            "routes":int(sheet.cell_value(r, 3))
        }
    return rmss


def parse_gathering_report():

    # get current directory using os library
    dirname=os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')) # added after restructuring files/folders
    # construct excel file full path
    xl_fullpath=os.path.join(dirname,'static\well_connections.xlsm')

    wc_book = xlrd.open_workbook(xl_fullpath)


    # folder=os.path.join(os.path.dirname(os.path.abspath(__file__)),"temp")
    folder=os.path.join(dirname,'temp')
    print(folder)
    allfiles=read_files(folder)
    rmss=get_rmss(wc_book)
    wells=get_wellnames(wc_book)
    print(allfiles)

    result_text=[]
    warn_text=[]
    for f in allfiles:
        book = xlrd.open_workbook(f)
        sheet = book.sheet_by_name("ENG")
        dt=sheet.cell_value(2, 2)
        print(dt)



        for r in range(0,sheet.nrows):
            col=str(sheet.cell_value(r, 1)).replace('"','').replace(' ','').replace('-','').replace('/','')
            for key,val in rmss.items():
                if key in col:

                    cells=""
                    for c in range(3,12):
                        cells+=str(sheet.cell_value(r, c))+","

                    rmss[key]["rawstr"]=cells.replace(' ','')
                    rmss[key]["split_str"]=re.split('Line|Test',rmss[key]["rawstr"])
                    if not rmss[key]["split_str"][0]:
                        rmss[key]["split_str"]=rmss[key]["split_str"][1:]
                    rmss[key]["well_cnt"]=sheet.cell_value(r, 2)

                    print(key,rmss[key]["split_str"])

        well_routes={}
        for well_dict in wells:
            well=list(well_dict.keys())[0]
            well_label=well_dict[well]

            for key,val in rmss.items():

                for l,line in enumerate(val["split_str"]):
                    if well in line:
                        iters = re.finditer(well, line)
                        starts = [x.start() for x in iters]
                        # print(iters,starts)

                        flag=0
                        for start in starts:

                            end=start+len(well)

                            if start>=0:
                                try:
                                    d=float(line[start-1:start])
                                    flag+=1
                                except:
                                    pass
                            if end<len(line):
                                try:
                                    d=float(line[end:end+1])
                                    flag+=1
                                except:
                                    pass

                            if flag==0:
                                well_routes[well]={
                                    "unit":val["unit"],
                                    "rms":val["rms"],
                                    "TL":l+1,
                                    "routes":val["routes"],
                                    "rms_rawstr":key,
                                    "well_label":well_label
                                    }

                            flag=0

        for well,val in well_routes.items():

            # print(val["rms_rawstr"],val)
            if val["rms_rawstr"]=="ToUnit2":
                if val["TL"]==1:
                    tl="GORline1"
                elif val["TL"]==2:
                    tl="GORline2"
            else:
                if val["routes"]==1:
                    tl=""
                elif val["routes"]==2:
                    if val["TL"]==1:
                        tl="TL1"
                    elif val["TL"]==2:
                        tl="TEST"
                elif val["routes"]==3:
                    if val["TL"]==1:
                        tl="TL1"
                    elif val["TL"]==2:
                        tl="TL2"
                    elif val["TL"]==3:
                        tl="TEST"


            route_result=[val["well_label"],val["unit"],val["rms"],tl]
            print(route_result)

            result_text.append(route_result)

        # QC step

        # calc number of wells
        for key,val in rmss.items():
            well_cnt=0
            for well,val2 in well_routes.items():
                if key==val2["rms_rawstr"]:
                    well_cnt+=1
            if val["well_cnt"]!=well_cnt:
                print("ERROR FOUND!!! Check below: =================")
                log_text="ERROR FOUND!!! Check below: ================="
                warn_text.append(log_text)
                log_text="not passed QC. %s,%s, %s--%s, %s, well_count: %s vs report well_count: %s" \
                        % (dt,key,val["unit"],val["rms"],val["split_str"],well_cnt,val["well_cnt"])
                print(log_text)
                warn_text.append(log_text)


        # break
    result_text=sorted(result_text, key=lambda x: x[0])
    return result_text, warn_text
