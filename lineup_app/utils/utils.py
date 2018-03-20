import numpy as np
import os
import json

# required for saving json files
dirname=os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')) # added after restructuring files/folders

def make_well_data_by_unit(session_json):
    # group wells by unit for html page
    session_json["well_data_byunit"]=[{},{},{}]
    for well,val in session_json["well_data"].items():
        if "masked" in val: #required to know which well is masked/unmasked in GAP to include/exclude well in the list
            if val["masked"]==0:
                session_json["well_data_byunit"][val["unit_id"]][well]=val
    return session_json



def calc_target_fwhps(session_json):
    for well,val in session_json["well_data"].items(): # additional step to pre calculate required qgas_max equivalent to target FWHP
        # print(well,val)
        if "target_fwhp" in val:
            if val["target_fwhp"]>0:
                pc_fwhp=session_json["well_pcs"][well]["pc"]["thps"]
                pc_qgas=session_json["well_pcs"][well]["pc"]["qgas"]
                # GAP uses qgas_max to reach target THP
                session_json["well_data"][well]["qgas_max"]=np.interp(val["target_fwhp"],pc_fwhp,pc_qgas)
    return session_json



def save_loaded2session(session_json,loaded_data):

    loaded_state=loaded_data["state"]
    shut_the_rest=loaded_data["shut_the_rest"]

    for well,val in session_json["well_data"].items():
        if well in loaded_state:
            # check if selected route exist in well connection list
            in_routes=0
            for r in session_json["well_data"][well]["connection"]["routes"]:
                if loaded_state[well]["selected_route"]==r["route_name"]:
                    in_routes=1
                    break

            if in_routes==1:
                session_json["well_data"][well]["selected_route"]=loaded_state[well]["selected_route"]
                session_json["well_data"][well]["target_fwhp"]=round(float(loaded_state[well]["target_fwhp"]),1)
            else:
                print("Route is not in well connections list! Well %s, %s" % (well,loaded_state[well]["selected_route"]))

        else: # if well is not in loaded_state then shut the well
            if shut_the_rest:
                session_json["well_data"][well]["target_fwhp"]=-1

    return session_json


def allowed_file(filename,ALLOWED_EXTENSIONS): # make sure file is one of allowed extentions (look on top)
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def merge_route_slot(result_text,well_details):
    result_text_new=[]
    print(well_details.keys())
    for well in result_text:
        for w,val in well_details.items():
            if well[0]==w:
                for r in val["connection"]["routes"]:
                    print(w,well[1],well[2],well[3])
                    print(w,r["unit"],r["rms"],r["tl"])
                    if well[1]==r["unit"] and well[2]==r["rms"] and well[3]==r["tl"]:

                        row=well
                        row.append(r["slot"])
                        result_text_new.append(row)
    return result_text_new



def delete_refcase():
    json_fullpath_ref=os.path.join(dirname,r"temp\session_ref_case.json")
    if os.path.isfile(json_fullpath_ref):
        os.remove(json_fullpath_ref)
    return "None"

def save_session_json(session_json):
    json_fullpath=os.path.join(dirname,r"temp\session.json")
    json.dump(session_json, open(json_fullpath, 'w'),indent=4, sort_keys=True)
    return "None"

def save_orig_session_json(session_json):
    json_fullpath=os.path.join(dirname,r"temp\route_opt\orig_session.json")
    json.dump(session_json, open(json_fullpath, 'w'),indent=4, sort_keys=True)
    return "None"

def save_best_session_json(session_json):
    json_fullpath=os.path.join(dirname,r"temp\route_opt\best_session.json")
    json.dump(session_json, open(json_fullpath, 'w'),indent=4, sort_keys=True)
    return "None"

def clear_well_data_session_json(): # when user logged out well_data to clear for cleaning after user.
    session_json=get_session_json()
    session_json.pop('well_data', None)
    session_json["state"]=0
    save_session_json(session_json)
    return "None"

def get_session_json():
    json_fullpath=os.path.join(dirname,r"temp\session.json")
    if os.path.isfile(json_fullpath):
        data = json.load(open(json_fullpath))
    else:
        data={}
    return data

def get_orig_session_json():
    json_fullpath=os.path.join(dirname,r"temp\route_opt\orig_session.json")
    if os.path.isfile(json_fullpath):
        data = json.load(open(json_fullpath))
    else:
        data={}
    return data

def get_best_session_json():
    json_fullpath=os.path.join(dirname,r"temp\route_opt\best_session.json")
    if os.path.isfile(json_fullpath):
        data = json.load(open(json_fullpath))
    else:
        data={}
    return data

def save_2ref(session_json):
    json_fullpath_ref=os.path.join(dirname,r"temp\session_ref_case.json")
    json.dump(session_json, open(json_fullpath_ref, 'w'))
    return "None"


def save_streams2session(data,session_json):
    unit_data=data["unit_data"]
    lab=data["lab"]
    streams=data["streams"]

    for u,v in unit_data.items(): # save unit_data
        unit=u.split("-")[0] # unit and phase separated by -
        phase=u.split("-")[1]
        session_json["fb_data"]["unit_data"][unit]["measured"][phase]=v

    for l,v in lab.items():
        session_json["fb_data"]["lab"][l]=v

    for s,v in streams.items():
        session_json["fb_data"]["streams"]["measured"][s]=v


    return session_json


def save_afs2session(afs,session_json):
    for unit,af in afs.items():
        for a,v in af.items():
            for p,n in v.items():
                print(unit,p,n)
                session_json["fb_data"]["unit_data"][unit]["af"][p]=n

    return session_json
