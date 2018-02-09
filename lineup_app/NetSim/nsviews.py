import json
# import numpy as np
# import os
# import dpath.util as dpu

# from netsim_app import app
# from flask import render_template, request,jsonify
# from flask_socketio import SocketIO, send, emit,disconnect
# from netsim_app import netsim as ns

from lineup_app.NetSim import netsim as ns



# secret key initialized for the server
# app.secret_key = 'any_random_string'
# socket IO initialized, time out set to 500 sec
# socketio=SocketIO(app, ping_timeout=500)


# @app.route('/api')
# def index_api():
#     gap=ns.read_gap_file()
#     return jsonify({"data":gap})

# -------------------------------------------------
# @app.route('/api/build_network')
# def build_network_api():
#     gap=ns.build_network()
#     return jsonify({"data":"network built!"})


def dino_build_network_api():
    gap=ns.build_network()
    return json.dumps({"data":"network built!"})
# -------------------------------------------------

# @app.route('/api/calculate_network')
# def calculate_network_api():
#     gap=ns.calculate_network()
#     return jsonify({"data":"calculation done!"})

def dino_calculate_network_api():
    gap=ns.calculate_network()
    return json.dumps({"data":"calculation done!"})


# -------------------------------------------------



# @app.route('/api/optimize_network')
# def optimize_network_api():
#     gap,time_spent=ns.optimize_network()
#     return jsonify({"data":"Calculation done! Time spent: %s" % time_spent})

def dino_optimize_network_api():
    gap,time_spent=ns.optimize_network()
    return json.dumps({"data":"Calculation done! Time spent: %s" % time_spent})


# -------------------------------------------------
# @app.route('/api/doget', methods=["POST"])
# def get_item_api():
#     # print(request)
#     code=request.get_json()["path"]
#     gap=ns.read_gap_file()
#     item=ns.DoGet(gap,code)
#     return jsonify({"data":item})


def dino_get_item_api(json_data):
    # print(request)
    # code=request.get_json()["path"]
    code=json_data["path"]
    gap=ns.read_gap_file()
    item=ns.DoGet(gap,code)
    return json.dumps({"data":item})


# -------------------------------------------------
# @app.route('/api/dogetall', methods=["POST"])
# def get_item_all_api():
#     # print(request.get_json())
#     code=request.get_json()["path"]
#     search=request.get_json()["search"]
#
#     gap=ns.read_gap_file()
#     code+="/**/"+search
#     items=ns.DoGetAll(gap,code)
#
#     return jsonify({"data":items})

def dino_get_item_all_api(json_data):
    # print(request.get_json())
    # code=request.get_json()["path"]
    # search=request.get_json()["search"]

    code=json_data["path"]
    search=json_data["search"]

    gap=ns.read_gap_file()
    code+="/**/"+search
    items=ns.DoGetAll(gap,code)

    return json.dumps({"data":items})

# -------------------------------------------------
# @app.route('/api/doset', methods=["POST"])
# def set_item_api():
#     code=request.get_json()["path"]
#     val=request.get_json()["val"]
#     gap=ns.read_gap_file()
#     gap=ns.DoSet(gap,code,val)
#     item=ns.DoGet(gap,code)
#     return jsonify({"data":item})

def dino_set_item_api(json_data):
    # code=request.get_json()["path"]
    # val=request.get_json()["val"]
    code=json_data["path"]
    val=json_data["val"]
    gap=ns.read_gap_file()
    gap=ns.DoSet(gap,code,val)
    item=ns.DoGet(gap,code)
    return json.dumps({"data":item})

# -------------------------------------------------
# @app.route('/api/dosetall', methods=["POST"])
# def set_item_all_api():
#     code=request.get_json()["path"]
#     param=request.get_json()["param"]
#     vals=request.get_json()["vals"]
#     gap=ns.read_gap_file()
#     gap=ns.DoSetAll(gap,code,param,vals)
#     code+="/**/"+param
#     items=ns.DoGetAll(gap,code)
#     return jsonify({"data":items})

def dino_set_item_all_api(json_data):
    # code=request.get_json()["path"]
    # param=request.get_json()["param"]
    # vals=request.get_json()["vals"]

    code=json_data["path"]
    param=json_data["param"]
    vals=json_data["vals"]

    gap=ns.read_gap_file()
    gap=ns.DoSetAll(gap,code,param,vals)
    code+="/**/"+param
    items=ns.DoGetAll(gap,code)
    return json.dumps({"data":items})

# -------------------------------------------------


if __name__=="__main__":

    # gap=read_gap_file()
    #
    # gap=DoSet(gap,"pipes/p_9815_tl1/masked",0)
    # gap=DoSet(gap,"pipes/p_9815_tl2/masked",1)
    #
    # gap=calculate_network(gap)
    # print(gap["seps"]["kpc"]["results"]["qgas"])
    #
    # gap=DoSet(gap,"pipes/p_9815_tl1/masked",1)
    # gap=DoSet(gap,"pipes/p_9815_tl2/masked",0)
    #
    # gap=calculate_network(gap)
    # print(gap["seps"]["kpc"]["results"]["qgas"])
















    print("")
