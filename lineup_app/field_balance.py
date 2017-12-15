import numpy as np
import json
import os



def calculate(pc_data,fb_data):
    # print(pc_data[0][0])

    units=[]
    units_tot=[]
    unit_idx={"kpc":0,"u3":1,"u2":2}
    for unit in pc_data:
        pcs_raw=[]
        unit_qoil=0.0
        unit_qgas=0.0
        for key,well in unit.items():
            pcs_raw.append([well["wellname"],well["gor"],well["qoil"],well["qgas"]])
            unit_qoil=unit_qoil+well["qoil"]
            unit_qgas=unit_qgas+well["qgas"]
        units.append(pcs_raw)
        units_tot.append([unit_qoil,unit_qgas])

    # units_tot=[
    #     [26207.0,21119.0],
    #     [12409.0,21093.0],
    #     [11417.0,19742.0]
    # ]


    # fb_data={
    #     "unit_pcs":{
    #       "kpc_pc":[[0,0,0],[1000,100,3000],[2000,500,9000],[5000,1000,11000],[6000,2000,12000],[7000,3000,13000],[12000,15000,15000]],
    #       "u2_pc":[[0,0,0],[1000,100,3000],[2000,500,6000],[5000,1000,9000],[6000,2000,10000],[7000,3000,11000],[12000,15000,15000]],
    #       "u3_pc":[[0,0,0],[1000,100,3000],[2000,500,8000],[5000,1000,12000],[6000,2000,13000],[7000,3000,14000],[12000,15000,15000]],
    #     },
    #     "wells":{
    #       "kpc":{
    #         "qoil":15000,
    #         "qgas":10000,
    #         "gor":2,
    #         "qoil_pot":16000,
    #         "qgas_pot":4,
    #         "mp_rs":114.192848579,
    #         "lp_rs":50.0,
    #         "af_oil":0.97,
    #         "af_gas":1,
    #       },
    #       "u2":{
    #         "qoil":0,
    #         "qgas":1,
    #         "gor":2,
    #         "qoil_pot":3,
    #         "qgas_pot":4,
    #         "mp_rs":92.284234698,
    #         "lp_rs":50.0,
    #         "af_oil":0.97,
    #         "af_gas":1,
    #       },
    #       "u3":{
    #         "qoil":0,
    #         "qgas":1,
    #         "gor":2,
    #         "qoil_pot":3,
    #         "qgas_pot":4,
    #         "mp_rs":131.470751703,
    #         "lp_rs":70.562525908,
    #         "af_oil":0.97,
    #         "af_gas":1,
    #       },
    #     },
    #     "streams":{
    #       "actuals":{
    #         "cpc_oil":0,
    #         "fuel_gas":2500.0,
    #         "gas_inj":2,
    #         "ogp_gas":3,
    #         "ogp_oil":4,
    #         "mtu_oil":5,
    #         "kpc_gas_2_u2":6,
    #         "kpc_gas_2_u3":7,
    #         "u3_oil_2_kpc":8,
    #         "u3_gas_2_kpc":9,
    #         "u2_oil_2_kpc":10,
    #         "u2_gas_2_kpc":11,
    #         "u2_oil_2_u3":12,
    #         "u2_gas_2_u3":13,
    #         "kpc_free_gas":14,
    #         "kpc_tot_gas":15,
    #         "kpc_tot_oil":16,
    #         "u2_free_gas":14,
    #         "u2_tot_gas":15,
    #         "u2_tot_oil":16,
    #         "u3_free_gas":14,
    #         "u3_tot_gas":15,
    #         "u3_tot_oil":16,
    #
    #       },
    #       "constraints":{
    #         "cpc_oil_max":38000.0,
    #         "fuel_gas_max":2500.0,
    #         "gas_inj_max":26000.0,
    #         "ogp_gas_max":28000.0,
    #         "ogp_oil_max":2500.0,
    #         "mtu_oil_max":0.0,
    #         "kpc_gas_2_u2_max":9600.0,
    #         "kpc_gas_2_u3_max":10100.0,
    #         "kpc_free_gas_max":15000.0,
    #         "kpc_tot_gas_max":14900.0,
    #         "u2_free_gas_max":18000.0,
    #         "u3_free_gas_max":19000.0,
    #       },
    #       "perc":{
    #         "cpc_oil_perc":0,
    #         "fuel_gas_perc":1,
    #         "gas_inj_perc":2,
    #         "ogp_gas_perc":3,
    #         "ogp_oil_perc":4,
    #         "mtu_oil_perc":5,
    #         "kpc_gas_2_u2_perc":6,
    #         "kpc_gas_2_u3_perc":7,
    #         "kpc_free_gas_perc":8,
    #         "kpc_tot_gas_perc":9,
    #         "u2_free_gas_perc":10,
    #         "u3_free_gas_perc":11,
    #       }
    #     }
    # }

    for u,val in fb_data["wells"].items():
        fb_data["wells"][u]["qoil"]=units_tot[unit_idx[u]][0]
        fb_data["wells"][u]["qoil_alloc"]=units_tot[unit_idx[u]][0]*fb_data["wells"][u]["af_oil"]
        fb_data["wells"][u]["qgas"]=units_tot[unit_idx[u]][1]
        fb_data["wells"][u]["qgas_alloc"]=units_tot[unit_idx[u]][1]*fb_data["wells"][u]["af_gas"]
        if fb_data["wells"][u]["qoil"]>0:
            fb_data["wells"][u]["gor"]=fb_data["wells"][u]["qgas"]/fb_data["wells"][u]["qoil"]*1000.0
        else:
            fb_data["wells"][u]["gor"]=0


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
