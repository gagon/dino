import numpy as np
import json
import os



def calculate(pc_data,fb_data):

    units_tot=[]
    units_pc=[]
    # unit
    unit_idx={"kpc":0,"u3":1,"u2":2}
    for unit in pc_data:
        pcs_raw=[]
        unit_qoil=0.0
        unit_qgas=0.0

        u=[]
        for key,well in unit.items():
            unit_qoil=unit_qoil+float(well["qoil"])
            unit_qgas=unit_qgas+float(well["qgas"])
            u.append([well["wellname"],float(well["gor"]),float(well["qoil"]),float(well["qgas"])])

        units_tot.append([unit_qoil,unit_qgas])


        units_mingor = sorted(u, key=lambda x: x[1])
        units_mingor=[list(i) for i in zip(*units_mingor)]

        units_mingor_qgas_cum=[0]
        qgas_cum=0.0
        for qgas in units_mingor[3]:
            qgas_cum+=qgas
            units_mingor_qgas_cum.append(qgas_cum)
        print(units_mingor_qgas_cum)

        units_mingor_qoil_cum=[0]
        qoil_cum=0.0
        for qoil in units_mingor[2]:
            qoil_cum+=qoil
            units_mingor_qoil_cum.append(qoil_cum)


        units_maxgor = sorted(u, key=lambda x: x[1], reverse=True)
        units_maxgor=[list(i) for i in zip(*units_maxgor)]

        units_maxgor_qgas_cum=[0]
        qgas_cum=0.0
        for qgas in units_maxgor[3]:
            qgas_cum+=qgas
            units_maxgor_qgas_cum.append(qgas_cum)

        units_maxgor_qoil_cum=[0]
        qoil_cum=0.0
        for qoil in units_maxgor[2]:
            qoil_cum+=qoil
            units_maxgor_qoil_cum.append(qoil_cum)

        u_pc=[[0.0,0.0,0.0]]
        for i,w in enumerate(units_mingor_qgas_cum):
            u_pc.append([units_mingor_qgas_cum[i],units_mingor_qoil_cum[i], \
                np.interp(units_mingor_qgas_cum[i],units_maxgor_qgas_cum,units_maxgor_qoil_cum)])

        units_pc.append(u_pc)

    for u,v in unit_idx.items():
        fb_data["unit_pcs"][u+"_pc"]=units_pc[v]


    fb_data["wells"]["kpc"]["mp_rs"]=fb_data["lab"]["kpc_mp_rs"]
    fb_data["wells"]["u3"]["mp_rs"]=fb_data["lab"]["u3_mp_rs"]
    fb_data["wells"]["u3"]["lp_rs"]=fb_data["lab"]["u3_lp_rs"]
    fb_data["wells"]["u2"]["mp_rs"]=fb_data["lab"]["u2_mp_rs"]



    """ FIELD BALANCE =================================================================================================== """


    for u,val in fb_data["wells"].items():
        fb_data["wells"][u]["qoil"]=units_tot[unit_idx[u]][0]
        fb_data["wells"][u]["qoil_alloc"]=units_tot[unit_idx[u]][0]*1.0
        fb_data["wells"][u]["qgas"]=units_tot[unit_idx[u]][1]
        fb_data["wells"][u]["qgas_alloc"]=units_tot[unit_idx[u]][1]*1.0
        if fb_data["wells"][u]["qoil"]>0:
            fb_data["wells"][u]["gor"]=fb_data["wells"][u]["qgas"]/fb_data["wells"][u]["qoil"]*1000.0
        else:
            fb_data["wells"][u]["gor"]=0


    if fb_data["wells"]["kpc"]["qgas_alloc"]>fb_data["streams"]["constraints"]["fuel_gas_max"]:
        fb_data["streams"]["actuals"]["fuel_gas"]=fb_data["streams"]["constraints"]["fuel_gas_max"]


    fb_data["streams"]["actuals"]["u2_oil_2_kpc"]=max(
            0.0,
            min(
                fb_data["streams"]["constraints"]["cpc_oil_max"]-fb_data["wells"]["kpc"]["qoil_alloc"],
                fb_data["wells"]["u2"]["qoil_alloc"]
            )
        )

    fb_data["streams"]["actuals"]["u2_oil_2_u3"]=max(
            0.0,
            fb_data["wells"]["u2"]["qoil_alloc"]-fb_data["streams"]["actuals"]["u2_oil_2_kpc"]
        )

    fb_data["streams"]["actuals"]["u3_tot_oil"]=fb_data["wells"]["u3"]["qoil_alloc"]+fb_data["streams"]["actuals"]["u2_oil_2_u3"]

    fb_data["streams"]["actuals"]["u3_oil_2_kpc"]=max(
            0.0,
            min(
                fb_data["streams"]["constraints"]["cpc_oil_max"] \
                -fb_data["wells"]["kpc"]["qoil_alloc"] \
                -fb_data["streams"]["actuals"]["u2_oil_2_kpc"],

                fb_data["streams"]["actuals"]["u3_tot_oil"]
            )
        )

    fb_data["streams"]["actuals"]["cpc_oil"]= \
        fb_data["wells"]["kpc"]["qoil_alloc"] \
        +fb_data["streams"]["actuals"]["u2_oil_2_kpc"] \
        +fb_data["streams"]["actuals"]["u3_oil_2_kpc"]

    fb_data["streams"]["actuals"]["mtu_oil"]=min(
            fb_data["streams"]["constraints"]["mtu_oil_max"],
            fb_data["streams"]["actuals"]["u3_tot_oil"]-fb_data["streams"]["actuals"]["u3_oil_2_kpc"]
        )

    fb_data["streams"]["actuals"]["ogp_oil"]= \
        fb_data["streams"]["actuals"]["u3_tot_oil"] \
        -fb_data["streams"]["actuals"]["u3_oil_2_kpc"] \
        -fb_data["streams"]["actuals"]["mtu_oil"]


    fb_data["streams"]["actuals"]["kpc_free_gas"]= \
        fb_data["wells"]["kpc"]["qgas_alloc"] \
        -fb_data["streams"]["actuals"]["fuel_gas"] \
        -fb_data["wells"]["kpc"]["qoil_alloc"]*fb_data["wells"]["kpc"]["mp_rs"]/1000.0


    fb_data["streams"]["actuals"]["u2_gas_2_kpc"]=fb_data["streams"]["actuals"]["u2_oil_2_kpc"]*fb_data["wells"]["u2"]["mp_rs"]/1000.0
    fb_data["streams"]["actuals"]["u2_gas_2_u3"]=fb_data["streams"]["actuals"]["u2_oil_2_u3"]*fb_data["wells"]["u2"]["mp_rs"]/1000.0
    fb_data["streams"]["actuals"]["u3_gas_2_kpc"]=fb_data["streams"]["actuals"]["u3_oil_2_kpc"]*fb_data["wells"]["u3"]["lp_rs"]/1000.0

    fb_data["streams"]["actuals"]["kpc_tot_gas"]= \
        fb_data["wells"]["kpc"]["qgas_alloc"] \
        +fb_data["streams"]["actuals"]["u2_gas_2_kpc"] \
        +fb_data["streams"]["actuals"]["u3_gas_2_kpc"] \
        -fb_data["streams"]["actuals"]["fuel_gas"]


    fb_data["streams"]["actuals"]["u3_free_gas"]= \
        fb_data["wells"]["u3"]["qgas_alloc"] \
        -fb_data["wells"]["u3"]["qoil_alloc"]*fb_data["wells"]["u3"]["mp_rs"]/1000.0


    fb_data["streams"]["actuals"]["u2_free_gas"]= \
        fb_data["wells"]["u2"]["qgas_alloc"] \
        -fb_data["wells"]["u2"]["qoil_alloc"]*fb_data["wells"]["u2"]["mp_rs"]/1000.0


    fb_data["streams"]["actuals"]["u3_tot_gas"]= \
        fb_data["wells"]["u3"]["qgas_alloc"] \
        -fb_data["streams"]["actuals"]["mtu_oil"]*fb_data["wells"]["u3"]["mp_rs"]/1000.0 \
        -fb_data["streams"]["actuals"]["ogp_oil"]*fb_data["wells"]["u3"]["mp_rs"]/1000.0 \
        -fb_data["streams"]["actuals"]["u3_gas_2_kpc"]


    fb_data["streams"]["actuals"]["kpc_gas_2_u3"]=min(
            fb_data["streams"]["actuals"]["kpc_tot_gas"],
            fb_data["streams"]["constraints"]["kpc_gas_2_u3_max"],
            max(
                fb_data["streams"]["constraints"]["ogp_gas_max"]-fb_data["streams"]["actuals"]["u3_tot_gas"], \
                0.0
            ),
        )

    fb_data["streams"]["actuals"]["ogp_gas"]= \
        fb_data["streams"]["actuals"]["u3_tot_gas"] \
        +fb_data["streams"]["actuals"]["kpc_gas_2_u3"] \
        +fb_data["streams"]["actuals"]["u2_gas_2_u3"]

    fb_data["streams"]["actuals"]["kpc_gas_2_u2"]=max(
            fb_data["streams"]["actuals"]["kpc_tot_gas"]-fb_data["streams"]["actuals"]["kpc_gas_2_u3"],
            0.0
        )

    fb_data["streams"]["actuals"]["gas_inj"]=fb_data["streams"]["actuals"]["kpc_gas_2_u2"]+fb_data["streams"]["actuals"]["u2_free_gas"]



    if fb_data["streams"]["constraints"]["cpc_oil_max"]>0.0:
        fb_data["streams"]["perc"]["cpc_oil_perc"]=round(fb_data["streams"]["actuals"]["cpc_oil"]/fb_data["streams"]["constraints"]["cpc_oil_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["cpc_oil_perc"]=0.0

    if fb_data["streams"]["constraints"]["fuel_gas_max"]>0.0:
        fb_data["streams"]["perc"]["fuel_gas_perc"]=round(fb_data["streams"]["actuals"]["fuel_gas"]/fb_data["streams"]["constraints"]["fuel_gas_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["fuel_gas_perc"]=0.0

    if fb_data["streams"]["constraints"]["gas_inj_max"]>0.0:
        fb_data["streams"]["perc"]["gas_inj_perc"]=round(fb_data["streams"]["actuals"]["gas_inj"]/fb_data["streams"]["constraints"]["gas_inj_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["gas_inj_perc"]=0.0

    if fb_data["streams"]["constraints"]["ogp_gas_max"]>0.0:
        fb_data["streams"]["perc"]["ogp_gas_perc"]=round(fb_data["streams"]["actuals"]["ogp_gas"]/fb_data["streams"]["constraints"]["ogp_gas_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["ogp_gas_perc"]=0.0

    if fb_data["streams"]["constraints"]["ogp_oil_max"]>0.0:
        fb_data["streams"]["perc"]["ogp_oil_perc"]=round(fb_data["streams"]["actuals"]["ogp_oil"]/fb_data["streams"]["constraints"]["ogp_oil_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["ogp_oil_perc"]=0.0

    if fb_data["streams"]["constraints"]["mtu_oil_max"]>0.0:
        fb_data["streams"]["perc"]["mtu_oil_perc"]=round(fb_data["streams"]["actuals"]["mtu_oil"]/fb_data["streams"]["constraints"]["mtu_oil_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["mtu_oil_perc"]=0.0

    if fb_data["streams"]["constraints"]["kpc_gas_2_u2_max"]>0.0:
        fb_data["streams"]["perc"]["kpc_gas_2_u2_perc"]=round(fb_data["streams"]["actuals"]["kpc_gas_2_u2"]/fb_data["streams"]["constraints"]["kpc_gas_2_u2_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["kpc_gas_2_u2_perc"]=0.0

    if fb_data["streams"]["constraints"]["kpc_gas_2_u3_max"]>0.0:
        fb_data["streams"]["perc"]["kpc_gas_2_u3_perc"]=round(fb_data["streams"]["actuals"]["kpc_gas_2_u3"]/fb_data["streams"]["constraints"]["kpc_gas_2_u3_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["kpc_gas_2_u3_perc"]=0.0


    if fb_data["streams"]["constraints"]["kpc_free_gas_max"]>0.0:
        fb_data["streams"]["perc"]["kpc_free_gas_perc"]=round(fb_data["streams"]["actuals"]["kpc_free_gas"]/fb_data["streams"]["constraints"]["kpc_free_gas_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["kpc_free_gas_perc"]=0.0

    if fb_data["streams"]["constraints"]["kpc_tot_gas_max"]>0.0:
        fb_data["streams"]["perc"]["kpc_tot_gas_perc"]=round(fb_data["streams"]["actuals"]["kpc_tot_gas"]/fb_data["streams"]["constraints"]["kpc_tot_gas_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["kpc_tot_gas_perc"]=0.0

    if fb_data["streams"]["constraints"]["u2_free_gas_max"]>0.0:
        fb_data["streams"]["perc"]["u2_free_gas_perc"]=round(fb_data["streams"]["actuals"]["u2_free_gas"]/fb_data["streams"]["constraints"]["u2_free_gas_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["u2_free_gas_perc"]=0.0

    if fb_data["streams"]["constraints"]["u3_free_gas_max"]>0.0:
        fb_data["streams"]["perc"]["u3_free_gas_perc"]=round(fb_data["streams"]["actuals"]["u3_free_gas"]/fb_data["streams"]["constraints"]["u3_free_gas_max"]*100, 2)
    else:
        fb_data["streams"]["perc"]["u3_free_gas_perc"]=0.0


    # print(fb_data["wells"]["kpc"]["qoil_alloc"])
    # print(fb_data["wells"]["u2"]["qoil_alloc"])
    # print(fb_data["wells"]["u3"]["qoil_alloc"])
    # print("---")
    # print(fb_data["wells"]["kpc"]["qgas_alloc"])
    # print(fb_data["wells"]["u2"]["qgas_alloc"])
    # print(fb_data["wells"]["u3"]["qgas_alloc"])
    # print("---")
    # print(fb_data["streams"]["constraints"]["cpc_oil_max"])
    # print(fb_data["streams"]["actuals"]["u2_oil_2_kpc"])
    # print(fb_data["streams"]["actuals"]["u3_oil_2_kpc"])
    # print(fb_data["streams"]["actuals"]["cpc_oil"])
    # print(fb_data["streams"]["actuals"]["mtu_oil"])
    # print(fb_data["streams"]["actuals"]["ogp_oil"])
    # print("---")
    # print(fb_data["streams"]["actuals"]["kpc_free_gas"])
    # print(fb_data["wells"]["kpc"]["qoil_alloc"]*fb_data["wells"]["kpc"]["mp_rs"]/1000.0)
    # print(fb_data["streams"]["actuals"]["u2_gas_2_kpc"])
    # print(fb_data["streams"]["actuals"]["u3_gas_2_kpc"])
    # print(fb_data["streams"]["actuals"]["kpc_tot_gas"])
    # print(fb_data["streams"]["actuals"]["u3_free_gas"])
    # print(fb_data["streams"]["actuals"]["u3_tot_gas"])
    # print(fb_data["streams"]["actuals"]["kpc_gas_2_u3"])
    # print(fb_data["streams"]["actuals"]["kpc_gas_2_u2"])
    # print(fb_data["streams"]["actuals"]["ogp_gas"])
    # print(fb_data["streams"]["actuals"]["u2_free_gas"])
    # print(fb_data["streams"]["actuals"]["gas_inj"])



    return fb_data


def fb_init():

    fb_data={
        "unit_pcs":{
          "kpc_pc":[],
          "u2_pc":[],
          "u3_pc":[],
        },
        "wells":{
          "kpc":{
            "qoil":-1,
            "qgas":-1,
            "gor":-1,
            "qoil_pot":-1,
            "qgas_pot":-1,
            "mp_rs":-1,
            "lp_rs":-1,
            "af_oil":-1,
            "af_gas":-1,
          },
          "u2":{
            "qoil":-1,
            "qgas":-1,
            "gor":-1,
            "qoil_pot":-1,
            "qgas_pot":-1,
            "mp_rs":-1,
            "lp_rs":-1,
            "af_oil":-1,
            "af_gas":-1,
          },
          "u3":{
            "qoil":-1,
            "qgas":-1,
            "gor":-1,
            "qoil_pot":-1,
            "qgas_pot":-1,
            "mp_rs":-1,
            "lp_rs":-1,
            "af_oil":-1,
            "af_gas":-1,
          },
        },
        "streams":{
          "actuals":{
            "cpc_oil":-1,
            "fuel_gas":-1,
            "gas_inj":-1,
            "ogp_gas":-1,
            "ogp_oil":-1,
            "mtu_oil":-1,
            "kpc_gas_2_u2":-1,
            "kpc_gas_2_u3":-1,
            "u3_oil_2_kpc":-1,
            "u3_gas_2_kpc":-1,
            "u2_oil_2_kpc":-1,
            "u2_gas_2_kpc":-1,
            "u2_oil_2_u3":-1,
            "u2_gas_2_u3":-1,
            "kpc_free_gas":-1,
            "kpc_tot_gas":-1,
            "kpc_tot_oil":-1,
            "u2_free_gas":-1,
            "u2_tot_gas":-1,
            "u2_tot_oil":-1,
            "u3_free_gas":-1,
            "u3_tot_gas":-1,
            "u3_tot_oil":-1,

          },
          "constraints":{
            "cpc_oil_max":-1,
            "fuel_gas_max":-1,
            "gas_inj_max":-1,
            "ogp_gas_max":-1,
            "ogp_oil_max":-1,
            "mtu_oil_max":-1,
            "kpc_gas_2_u2_max":-1,
            "kpc_gas_2_u3_max":-1,
            "kpc_free_gas_max":-1,
            "kpc_tot_gas_max":-1,
            "u2_free_gas_max":-1,
            "u3_free_gas_max":-1,
          },
          "perc":{
            "cpc_oil_perc":-1,
            "fuel_gas_perc":-1,
            "gas_inj_perc":-1,
            "ogp_gas_perc":-1,
            "ogp_oil_perc":-1,
            "mtu_oil_perc":-1,
            "kpc_gas_2_u2_perc":-1,
            "kpc_gas_2_u3_perc":-1,
            "kpc_free_gas_perc":-1,
            "kpc_tot_gas_perc":-1,
            "u2_free_gas_perc":-1,
            "u3_free_gas_perc":-1,
          }
        }
    }

    return fb_data




if __name__=="__main__":

    pc=[]
    fb=fb_init()
    a=calculate(pc,fb)
    print(a)



    print("")
