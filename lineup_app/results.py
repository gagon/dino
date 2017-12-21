import json
import os


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
            # print(cols)
            for c in cols:
                if well in data_ref["well_data"][u]:
                    data["well_data"][u][well][c+"_ref"]=data_ref["well_data"][u][well][c]

        for well,val in data_ref["well_data"][u].items():
            cols=list(data_ref["well_data"][u][well].keys())
            if not well in data["well_data"][u]:
                data["well_data"][u][well]={}
                for c in cols:
                    if c =="wellname":
                        data["well_data"][u][well][c]=well
                    elif c =="route":
                        # data["well_data"][u][well]={c:""}
                        data["well_data"][u][well][c]=""
                    else:
                        data["well_data"][u][well][c]=0

                    data["well_data"][u][well][c+"_ref"]=data_ref["well_data"][u][well][c]

        # print(data["well_data"][0][well])

    return data,1




if __name__=="__main__":

    # get current directory using os library
    dirname, filename = os.path.split(os.path.abspath(__file__))
    # json_fullpath=os.path.join(dirname,r"temp\results.json")
    # json.dump(data, open(json_fullpath, 'w'))

    json_fullpath=os.path.join(dirname,r"temp\results.json")
    data = json.load(open(json_fullpath))

    data,merge=merge_ref(data)

    print(data["well_data"][2]["15"])
    print(data["well_data"][0]["15"])

    # for d in data["well_data"]:
        # print(d)
    # print(len(data["well_data"]))


    # print(data["well_data"][0][data["well_data"][0].keys()[0]])
    # print(list(data["well_data"][0].keys())[0])



    print()
