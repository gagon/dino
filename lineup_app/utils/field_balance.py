import numpy as np
import json
import os



def calculate(session_json):

    pc_data=session_json["well_data_byunit"]
    fb_data=session_json["fb_data"]
    # unit_data=session_json["unit_data"]

    units_tot=[]
    units_pc=[]
    # unit
    unit_idx={"kpc":0,"u3":1,"u2":2}
    for unit in pc_data:
        pcs_raw=[]
        unit_qoil=0.0
        unit_qgas=0.0

        u=[]
        for well,val in unit.items():
            unit_qoil=unit_qoil+float(val["qoil"])
            unit_qgas=unit_qgas+float(val["qgas"])
            u.append([well,float(val["gor"]),float(val["qoil"]),float(val["qgas"])])

        units_tot.append([unit_qoil,unit_qgas])


        units_mingor = sorted(u, key=lambda x: x[1])
        units_mingor=[list(i) for i in zip(*units_mingor)]

        units_mingor_qgas_cum=[0]
        qgas_cum=0.0
        for qgas in units_mingor[3]:
            qgas_cum+=qgas
            units_mingor_qgas_cum.append(qgas_cum)
        # print(units_mingor_qgas_cum)

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


    # fb_data["unit_data"]["kpc"]["mp_rs"]=fb_data["lab"]["kpc_mp_rs"]
    # fb_data["unit_data"]["u3"]["mp_rs"]=fb_data["lab"]["u3_mp_rs"]
    # fb_data["unit_data"]["u3"]["lp_rs"]=fb_data["lab"]["u3_lp_rs"]
    # fb_data["unit_data"]["u2"]["mp_rs"]=fb_data["lab"]["u2_mp_rs"]




    """ FIELD BALANCE =================================================================================================== """


    for u,val in fb_data["unit_data"].items():
        if not "tr" in u:
            fb_data["unit_data"][u]["actual"]["qoil"]=units_tot[unit_idx[u]][0]
            # fb_data["unit_data"][u]["qoil_alloc"]=units_tot[unit_idx[u]][0]*1.0
            fb_data["unit_data"][u]["actual"]["qgas"]=units_tot[unit_idx[u]][1]
            # fb_data["unit_data"][u]["qgas_alloc"]=units_tot[unit_idx[u]][1]*1.0
            if fb_data["unit_data"][u]["actual"]["qoil"]>0:
                fb_data["unit_data"][u]["actual"]["gor"]=fb_data["unit_data"][u]["actual"]["qgas"]/fb_data["unit_data"][u]["actual"]["qoil"]*1000.0
            else:
                fb_data["unit_data"][u]["actual"]["gor"]=0


    if fb_data["unit_data"]["kpc"]["actual"]["qgas"]>fb_data["streams"]["constraints"]["fuel_gas_max"]:
        fb_data["streams"]["actuals"]["fuel_gas"]=fb_data["streams"]["constraints"]["fuel_gas_max"]


    fb_data["streams"]["actuals"]["u2_oil_2_kpc"]=max(
            0.0,
            min(
                fb_data["streams"]["constraints"]["cpc_oil_max"]-fb_data["unit_data"]["kpc"]["actual"]["qoil"],
                fb_data["unit_data"]["u2"]["actual"]["qoil"]
            )
        )

    fb_data["streams"]["actuals"]["u2_oil_2_u3"]=max(
            0.0,
            fb_data["unit_data"]["u2"]["actual"]["qoil"]-fb_data["streams"]["actuals"]["u2_oil_2_kpc"]
        )

    fb_data["streams"]["actuals"]["u2_tot_oil"]=fb_data["unit_data"]["u2"]["actual"]["qoil"]


    fb_data["streams"]["actuals"]["u3_tot_oil"]=fb_data["unit_data"]["u3"]["actual"]["qoil"]+fb_data["streams"]["actuals"]["u2_oil_2_u3"]

    fb_data["streams"]["actuals"]["u3_oil_2_kpc"]=max(
            0.0,
            min(
                fb_data["streams"]["constraints"]["cpc_oil_max"] \
                -fb_data["unit_data"]["kpc"]["actual"]["qoil"] \
                -fb_data["streams"]["actuals"]["u2_oil_2_kpc"],

                fb_data["streams"]["actuals"]["u3_tot_oil"]
            )
        )

    fb_data["streams"]["actuals"]["cpc_oil"]= \
        fb_data["unit_data"]["kpc"]["actual"]["qoil"] \
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
        fb_data["unit_data"]["kpc"]["actual"]["qgas"] \
        -fb_data["streams"]["actuals"]["fuel_gas"] \
        -fb_data["unit_data"]["kpc"]["actual"]["qoil"]*fb_data["lab"]["kpc_mp_rs"]/1000.0


    fb_data["streams"]["actuals"]["u2_oil_2_kpc_diss_gas"]=fb_data["streams"]["actuals"]["u2_oil_2_kpc"]*fb_data["lab"]["u2_mp_rs"]/1000.0
    fb_data["streams"]["actuals"]["u2_oil_2_u3_diss_gas"]=fb_data["streams"]["actuals"]["u2_oil_2_u3"]*fb_data["lab"]["u2_mp_rs"]/1000.0
    fb_data["streams"]["actuals"]["u3_oil_2_kpc_diss_gas"]=fb_data["streams"]["actuals"]["u3_oil_2_kpc"]*fb_data["lab"]["u3_lp_rs"]/1000.0

    fb_data["streams"]["actuals"]["kpc_tot_gas"]= \
        fb_data["unit_data"]["kpc"]["actual"]["qgas"] \
        +fb_data["streams"]["actuals"]["u2_gas_2_kpc"] \
        +fb_data["streams"]["actuals"]["u3_gas_2_kpc"] \
        -fb_data["streams"]["actuals"]["fuel_gas"]


    fb_data["streams"]["actuals"]["u3_free_gas"]= \
        fb_data["unit_data"]["u3"]["actual"]["qgas"] \
        -fb_data["unit_data"]["u3"]["actual"]["qoil"]*fb_data["lab"]["u3_mp_rs"]/1000.0


    fb_data["streams"]["actuals"]["u2_free_gas"]= \
        fb_data["unit_data"]["u2"]["actual"]["qgas"] \
        -fb_data["unit_data"]["u2"]["actual"]["qoil"]*fb_data["lab"]["u2_mp_rs"]/1000.0

    fb_data["streams"]["actuals"]["u2_tot_gas"]=fb_data["streams"]["actuals"]["u2_free_gas"]


    fb_data["streams"]["actuals"]["u3_tot_gas"]= \
        fb_data["unit_data"]["u3"]["actual"]["qgas"] \
        -fb_data["streams"]["actuals"]["mtu_oil"]*fb_data["lab"]["u3_lp_rs"]/1000.0 \
        -fb_data["streams"]["actuals"]["ogp_oil"]*fb_data["lab"]["u3_lp_rs"]/1000.0 \
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




    fb_data["streams"]["actuals"]["kpc_tot_oil"]=fb_data["unit_data"]["kpc"]["actual"]["qoil"]+fb_data["streams"]["actuals"]["u2_oil_2_kpc"]+fb_data["streams"]["actuals"]["u3_oil_2_kpc"]






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


    # print(fb_data["unit_data"]["kpc"]["qoil_alloc"])
    # print(fb_data["unit_data"]["u2"]["qoil_alloc"])
    # print(fb_data["unit_data"]["u3"]["qoil_alloc"])
    # print("---")
    # print(fb_data["unit_data"]["kpc"]["qgas"])
    # print(fb_data["unit_data"]["u2"]["qgas"])
    # print(fb_data["unit_data"]["u3"]["qgas"])
    # print("---")
    # print(fb_data["streams"]["constraints"]["cpc_oil_max"])
    # print(fb_data["streams"]["actuals"]["u2_oil_2_kpc"])
    # print(fb_data["streams"]["actuals"]["u3_oil_2_kpc"])
    # print(fb_data["streams"]["actuals"]["cpc_oil"])
    # print(fb_data["streams"]["actuals"]["mtu_oil"])
    # print(fb_data["streams"]["actuals"]["ogp_oil"])
    # print("---")
    # print(fb_data["streams"]["actuals"]["kpc_free_gas"])
    # print(fb_data["unit_data"]["kpc"]["qoil_alloc"]*fb_data["unit_data"]["kpc"]["mp_rs"]/1000.0)
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





if __name__=="__main__":

    pc=[]
    fb=fb_init()
    a=calculate(pc,fb)
    print(a)



    print("")
