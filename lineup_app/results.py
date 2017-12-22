import json
import os


def calculate_totals(pc_data,well_maps,session):

    totals=[] # array to save unit totals and subtotals

    # loop through units
    for unit,unit_wells in enumerate(pc_data):

        unit_total_qgas=0.0 # initialise unit totals for Qgas
        unit_total_qoil=0.0 # initialise unit totals for Qoil
        rmss=[] # initialise RMS list

        # print(pc_data)

        # loop through wells in unit
        for rank,val in unit_wells.items():

            # merge pc_data with map from Deliverability
            well=pc_data[unit][rank]["wellname"]
            pc_data[unit][rank]["map"]=well_maps[well]["map"]
            pc_data[unit][rank]["target_fwhp"]=session["state"]["well_state"][well]["fwhp"]
            # pc_data[unit][rank]["target_fwhp_ref"]=ref_data[unit][well]["fwhp"]

            # remove DD and Qliq limits if not set in GAP
            if pc_data[unit][rank]["dd_lim"]>10000.0:
                pc_data[unit][rank]["dd_lim"]=""
            if pc_data[unit][rank]["qliq_lim"]>10000.0:
                pc_data[unit][rank]["qliq_lim"]=""

            # populate list of RMSs
            if pc_data[unit][rank]["route"]["rms"] not in rmss:
                rmss.append(pc_data[unit][rank]["route"]["rms"])

            # aggregate unit totals
            if pc_data[unit][rank]["qoil"]:
                unit_total_qoil+=float(pc_data[unit][rank]["qoil"])
            if pc_data[unit][rank]["qgas"]:
                unit_total_qgas+=float(pc_data[unit][rank]["qgas"])

        # aggregate subtotals for RMSs
        subtotals={}
        for rms in rmss: # loop through RMSs
            totoil=0.0
            totgas=0.0
            for rank,val in pc_data[unit].items(): # loop through wells
                if val["route"]["rms"] == rms: # if in this RMS, then add to RMS total
                    if val["qoil"]:
                        totoil+=float(val["qoil"])
                    if val["qgas"]:
                        totgas+=float(val["qgas"])
            subtotals[rms]={"qoil":round(totoil,1),"qgas":round(totgas,1)}

        # put subtotals and unit totals into totals dictionary
        totals.append({"subtotals":subtotals,"qgas":round(unit_total_qgas,1),"qoil":round(unit_total_qoil,1)})

    # calculate field totals from units
    field_gas=round(totals[0]["qgas"]+totals[1]["qgas"]+totals[2]["qgas"],1)
    field_oil=round(totals[0]["qoil"]+totals[1]["qoil"]+totals[2]["qoil"],1)

    # put all data into dictionary to pass to html
    data={"totals":totals,"well_data":pc_data,"field":{"qgas":field_gas,"qoil":field_oil}}

    return data




def merge_ref(data):
    # get current directory using os library
    dirname, filename = os.path.split(os.path.abspath(__file__))
    json_fullpath_ref=os.path.join(dirname,r"temp\results_ref_case.json")

    if os.path.isfile(json_fullpath_ref):
        data_ref = json.load(open(json_fullpath_ref))
    else:
        return data,0


    i=0
    for d in data["totals"]:
        for key,val in d["subtotals"].items():
            if key in data_ref["totals"][i]["subtotals"]:
                data["totals"][i]["subtotals"][key]["qgas_ref"]=data_ref["totals"][i]["subtotals"][key]["qgas"]
                data["totals"][i]["subtotals"][key]["qoil_ref"]=data_ref["totals"][i]["subtotals"][key]["qoil"]
        i+=1

    i=0
    for d in data["totals"]:
        data["totals"][i]["qoil_ref"]=data_ref["totals"][i]["qoil"]
        data["totals"][i]["qgas_ref"]=data_ref["totals"][i]["qgas"]
        i+=1

    data["field"]["qgas_ref"]=data_ref["field"]["qgas"]
    data["field"]["qoil_ref"]=data_ref["field"]["qoil"]


    for u in range(3):
        for well,val in data["well_data"][u].items():

            cols=list(data["well_data"][u][well].keys())

            for c in cols:
                if well in data_ref["well_data"][u]:
                    # print(data_ref["well_data"][u][well][c])
                    data["well_data"][u][well][c+"_ref"]=data_ref["well_data"][u][well][c]
                else:
                    if c =="wellname":
                        data["well_data"][u][well][c+"_ref"]=well
                    elif c =="route":
                        # data["well_data"][u][well]={c:""}
                        data["well_data"][u][well][c+"_ref"]=""
                    else:
                        data["well_data"][u][well][c+"_ref"]=0

        for well,val in data_ref["well_data"][u].items():
            cols=list(data_ref["well_data"][u][well].keys())
            # print(cols)
            if not well in data["well_data"][u]:
                # print(well)
                data["well_data"][u][well]={}

                for c in cols:
                    # print(c)
                    if c =="wellname":
                        data["well_data"][u][well][c]=well
                    elif c =="route":
                        # data["well_data"][u][well]={c:""}
                        data["well_data"][u][well][c]=""
                    else:
                        data["well_data"][u][well][c]=0

                    data["well_data"][u][well][c+"_ref"]=data_ref["well_data"][u][well][c]
                    # print(data["well_data"][u][well][c],data["well_data"][u][well][c+"_ref"])

                print(data["well_data"][u][well])

    return data,1




if __name__=="__main__":

    # get current directory using os library
    dirname, filename = os.path.split(os.path.abspath(__file__))
    # json_fullpath=os.path.join(dirname,r"temp\results.json")
    # json.dump(data, open(json_fullpath, 'w'))

    json_fullpath=os.path.join(dirname,r"temp\results.json")
    data = json.load(open(json_fullpath))

    data,merge=merge_ref(data)

    # print(data["well_data"][0]["15"].keys())
    # print("---")
    # print(data["well_data"][2]["15"].keys())

    # for d in data["well_data"]:
        # print(d)
    # print(len(data["well_data"]))


    # print(data["well_data"][0][data["well_data"][0].keys()[0]])
    # print(list(data["well_data"][0].keys())[0])



    print()
