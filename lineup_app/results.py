import json
import os


def calculate_totals(pc_data):

    unit_totals=[] # array to save unit totals and subtotals

    # loop through units
    for unit,unit_wells in enumerate(pc_data):

        unit_total_qgas=0.0 # initialise unit totals for Qgas
        unit_total_qoil=0.0 # initialise unit totals for Qoil
        rmss=[] # initialise RMS list

        # print(pc_data)

        # loop through wells in unit
        for well,val in unit_wells.items():

            # merge pc_data with map from Deliverability
            # well=pc_data[unit][rank]["wellname"]
            # pc_data[unit][rank]["map"]=well_maps[well]["map"]
            # pc_data[unit][rank]["target_fwhp"]=session["state"]["well_state"][well]["fwhp"]
            # pc_data[unit][rank]["target_fwhp_ref"]=ref_data[unit][well]["fwhp"]

            # # remove DD and Qliq limits if not set in GAP
            # if pc_data[unit][rank]["dd_lim"]>10000.0:
            #     pc_data[unit][rank]["dd_lim"]=""
            # if pc_data[unit][rank]["qliq_lim"]>10000.0:
            #     pc_data[unit][rank]["qliq_lim"]=""

            # populate list of RMSs
            curr_route_idx=val["curr_route"]
            curr_route_dict=val["connection"]["routes"][curr_route_idx]
            # print(curr_route_dict)
            if curr_route_dict["rms"] not in rmss:
                rmss.append(curr_route_dict["rms"])

            # aggregate unit totals
            if val["qoil"]:
                unit_total_qoil+=float(val["qoil"])
            if pc_data[unit][well]["qgas"]:
                unit_total_qgas+=float(val["qgas"])

        # aggregate subtotals for RMSs
        subtotals={}
        for rms in rmss: # loop through RMSs
            totoil=0.0
            totgas=0.0
            for well,val in pc_data[unit].items(): # loop through wells

                curr_route_idx=val["curr_route"]
                curr_route_dict=val["connection"]["routes"][curr_route_idx]

                if curr_route_dict["rms"] == rms: # if in this RMS, then add to RMS total
                    if val["qoil"]:
                        totoil+=float(val["qoil"])
                    if val["qgas"]:
                        totgas+=float(val["qgas"])
            subtotals[rms]={"qoil":totoil,"qgas":totgas}

        # put subtotals and unit totals into totals dictionary
        unit_totals.append({"subtotals":subtotals,"qgas":unit_total_qgas,"qoil":unit_total_qoil})

    # calculate field totals from units
    field_gas=unit_totals[0]["qgas"]+unit_totals[1]["qgas"]+unit_totals[2]["qgas"]
    field_oil=unit_totals[0]["qoil"]+unit_totals[1]["qoil"]+unit_totals[2]["qoil"]

    totals={
        "field":{"qgas":field_gas,"qoil":field_oil},
        "unit":unit_totals
    }


    # put all data into dictionary to pass to html
    # data={"totals":totals,"well_data":pc_data,"field":{"qgas":field_gas,"qoil":field_oil}}

    return totals




def merge_ref(data):
    # get current directory using os library
    dirname, filename = os.path.split(os.path.abspath(__file__))
    json_fullpath_ref=os.path.join(dirname,r"temp\session_ref_case.json")

    if os.path.isfile(json_fullpath_ref):
        data_ref = json.load(open(json_fullpath_ref))
    else:
        return data,0



    for i,d in enumerate(data["totals"]["unit"]):
        for key,val in d["subtotals"].items():
            if key in data_ref["totals"]["unit"][i]["subtotals"]:
                data["totals"]["unit"][i]["subtotals"][key]["qgas_ref"]=data_ref["totals"]["unit"][i]["subtotals"][key]["qgas"]
                data["totals"]["unit"][i]["subtotals"][key]["qoil_ref"]=data_ref["totals"]["unit"][i]["subtotals"][key]["qoil"]



    for i,d in enumerate(data["totals"]["unit"]):
        data["totals"]["unit"][i]["qoil_ref"]=data_ref["totals"]["unit"][i]["qoil"]
        data["totals"]["unit"][i]["qgas_ref"]=data_ref["totals"]["unit"][i]["qgas"]


    data["totals"]["field"]["qgas_ref"]=data_ref["totals"]["field"]["qgas"]
    data["totals"]["field"]["qoil_ref"]=data_ref["totals"]["field"]["qoil"]


    for u in range(3):
        # matching current results with reference case
        for well,val in data["well_data_byunit"][u].items():
            cols=list(data["well_data_byunit"][u][well].keys())
            for c in cols:
                if well in data_ref["well_data_byunit"][u]:
                    data["well_data_byunit"][u][well][c+"_ref"]=data_ref["well_data_byunit"][u][well][c]
                else: # leave blank if does not exist in reference case
                    if c =="wellname":
                        data["well_data_byunit"][u][well][c+"_ref"]=well
                    elif c =="route":
                        data["well_data_byunit"][u][well][c+"_ref"]=""
                    else:
                        data["well_data_byunit"][u][well][c+"_ref"]=0

        # matching reference case with current results, add well rows from reference case if does not exist in current results
        for well,val in data_ref["well_data_byunit"][u].items():
            cols=list(data_ref["well_data_byunit"][u][well].keys())
            if not well in data["well_data_byunit"][u]: # if does not exist in current results add row for current results columns as blank.
                data["well_data_byunit"][u][well]={}
                for c in cols:
                    # if c =="wellname":
                    #     data["well_data_byunit"][u][well][c]=well
                    # elif c =="route":
                    #     data["well_data_byunit"][u][well][c]=""
                    # else:
                    data["well_data_byunit"][u][well][c]=0
                    data["well_data_byunit"][u][well][c+"_ref"]=data_ref["well_data_byunit"][u][well][c] # add data from ref case to ref case colunms
                # data["well_data_byunit"][u][well]["connection"]["wellname"]=well

                # print(data["well_data_byunit"][u][well])

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
