import numpy as np


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
