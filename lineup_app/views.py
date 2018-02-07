from lineup_app import app
from flask import render_template, request,redirect, url_for, session, flash, jsonify

import pyodbc
import datetime
from flask_socketio import SocketIO, send, emit,disconnect
from lineup_app import GAP_optimization as gob
from lineup_app import xlGAP_optimization as xlgob
from lineup_app import GAP_get_results as ggr
from lineup_app import xlGAP_get_results as xlggr
from lineup_app import GAP_setup as st
from lineup_app import xlGAP_setup as xlst
from lineup_app import xl_setup
from lineup_app import GAP_load_pcs2gap as pcs2gap
import flask_login as flask_login
from flask_login import LoginManager, UserMixin, login_required
import os
from werkzeug.utils import secure_filename
from lineup_app import gathering_parser as gath_par
import xlrd
import json
from lineup_app import field_balance as fb
from lineup_app import state_init
from lineup_app import results as rs
import numpy as np
from lineup_app import NetSimRoutines as NS
from lineup_app import NetSim_setup as nsst
from lineup_app import NetSim_get_results as nsgr
from lineup_app import NetSim_optimization as nsopt
# import requests



# use mockup from EXCEL GAP file
MOCKUP=True



# secret key initialized for the server
app.secret_key = 'any_random_string'
# socket IO initialized, time out set to 500 sec
socketio=SocketIO(app, ping_timeout=500)
sid=None

uploader_dirname, uploader_filename = os.path.split(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(uploader_dirname,'temp')
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Flask-login initialized
login_manager = LoginManager()
login_manager.init_app(app)

# users dictionary to login to the app
# temporary solution, must be placed outside of the code (database or xls)
users_json=os.path.join(uploader_dirname,r"temp\users.json")
users = json.load(open(users_json))


# Driver to be used to query data from EC. This is different on different computers
# db_driver="Oracle in OraClient11g"
db_driver="Oracle in OraClient11g_32bit"


# # using session_json instead of flask session due to cookie size limitation
# session_json={}


""" LOGIN ROUTINES (using flask-login library) ================================================================ """

class User(UserMixin):
    pass

# gets user from user dictionary
@login_manager.user_loader
def user_loader(username):
    if username not in users: # users dictionary already defined on very top
        return
    user = User()
    user.id = username
    return user

# gets user from request form in login page
@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in users:
        return
    user = User()
    user.id = username
    user.is_authenticated = request.form['pw'] == users[username]['pw']
    return user

# logout and clear session "state" variables
@app.route('/logout')
def logout():
    flask_login.logout_user()
    clear_well_data_session_json()
    delete_refcase()
    return redirect(url_for('index'))

# main fucntion where user is logged in if username and password are correct
# if not, redirect back to login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    page_active={"load_pcs":"","load_state":"","setup":"","live":"","results":""}
    if request.method == 'POST':
        username = request.form.get('username')
        # print(username,users)
        if username in users:
            if request.form.get('password') == users[username]['password']:
                user = User()
                user.id = username
                flask_login.login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Incorrect")
        else:
            return render_template('login.html',page_active=page_active)
    return render_template('login.html',page_active=page_active)

# error handing in case of incorrect or no login, redirects to login page
@app.errorhandler(401)
def custom_401(error):
    return redirect(url_for('login'))

# main welcome page if logged in successfully
@app.route('/')
@login_required
def index():
    page_active={"load_pcs":"","load_state":"","setup":"","live":"","results":""}
    return render_template('index.html',page_active=page_active)

""" ========================================================================================================== """





""" GAP CALCULATION PAGE ==================================================================================== """
@app.route('/live')
@login_required
def live():
    session_json=get_session_json()
    if not "well_data" in session_json: # check if state was exists. well_data ~ state
        return "NO session well state. Go back to setup and save state"

    page_active={"load_pcs":"","load_state":"","setup":"","live":"active","results":""}
    # else load live page
    return render_template('live.html',page_active=page_active)
""" ========================================================================================================= """



""" GET GAP RESULTS =========================================================================================== """
@app.route('/results')
@login_required
def results():


    session_json=get_session_json()
    if not "state" in session_json: # check if state was exists. well_data ~ state
        return "NO session well state. Go back to setup and save state"
    # get well results from GAP
    #------------------------------------------------------------------------------

    # get results from GAP or mockup excel
    if MOCKUP:
        session_json["well_data"]=nsgr.get_all_well_data(session_json)
    else:
        session_json["well_data"]=ggr.get_all_well_data(session_json)
    #------------------------------------------------------------------------------

    # group well results by unit
    session_json["well_data_byunit"]=[{},{},{}]
    for well,val in session_json["well_data"].items():
        if "masked" in val: #required to know which well is masked/unmasked in GAP to include/exclude well in the list
            if val["masked"]==0:
                session_json["well_data_byunit"][val["unit_id"]][well]=val

    # calculate totals by field/unit/rms
    session_json["totals"]=rs.calculate_totals(session_json["well_data_byunit"])

    # field balance calculation
    session_json["fb_data"]=fb.calculate(session_json)

    # this is done so that routings/sep pres dont get updated as cant be done on results page
    session_json["state"]=0

    # save results to json
    save_session_json(session_json)

    # merge data to present if ref case exists
    data,merge_done=rs.merge_ref(session_json)

    page_active={"load_pcs":"","load_state":"","setup":"","live":"","results":"active"}

    return render_template('results.html',data=data,page_active=page_active,merge_done=merge_done)
"""========================================================================================="""



""" LOAD PC PAGE RENDER ================================================================= """
@app.route('/load')
@login_required
def load():
    page_active={"load_pcs":"active","load_state":"","setup":"","live":"","results":""}
    return render_template('load.html',page_active=page_active)
"""========================================================================================="""



""" LOAD STATE PAGE RENDER ================================================================= """
@app.route('/load_state')
@login_required
def load_state():
    session_json=get_session_json()
    # check is session "state" exists, if not send message and stop
    if not "state" in session_json: # check if state was exists. well_data ~ state
        return "NO session well state. Go back to setup and save state"
    page_active={"load_pcs":"","load_state":"active","setup":"","live":"","results":""}
    return render_template('load_state.html',page_active=page_active)
"""========================================================================================="""



""" SETUP PAGE ============================================================================ """
@app.route('/setup')
@login_required
def setup():

    session_json=get_session_json() # read from json file all necessary app data

    if not "well_data" in session_json: # create a well_data if does not exist, this normally happens very first time user logs in.
        session_json["well_data"]={}
        # populate well data with wells from GAP
        if MOCKUP:
            session_json["well_data"]=nsst.get_gap_wells()
        else:
            print("add GAP openserver")
        print(session_json["well_data"])

    # get well connections from "well_connections.xlsm" file
    well_conns=xl_setup.read_conns()
    for well,m in session_json["well_data"].items(): # merge with well_data
        if well in well_conns:
            session_json["well_data"][well]["connection"]=well_conns[well] # assign list of connections

    # get MAPs from "Deliverability.xlsx" file
    well_maps=xl_setup.read_maps()
    for well,m in session_json["well_data"].items(): # merge with well_data
        if well in well_maps:
            session_json["well_data"][well]["map"]=well_maps[well]["map"]

    # print(session_json["well_data"])

    #------------------------------------------------------------------------------
    if MOCKUP:
        if session_json["state"]==1: # check if state has been saved by the user (1)
            nsst.set_unit_routes(session_json["well_data"]) # set well routes as per state
            nsst.set_sep_pres(session_json["unit_data"]["sep"]) # set separator pressure as per state

        session_json["well_data"]=nsst.get_all_well_data(session_json["well_data"])
        session_json["unit_data"]["sep"]=nsst.get_sep_pres()
    else:
        if session_json["state"]==1: # check if state has been saved by the user (1)
            st.set_unit_routes(session_json["well_data"]) # set well routes as per state
            st.set_sep_pres(session_json["unit_data"]["sep"]) # set separator pressure as per state

        session_json["well_data"]=st.get_all_well_data(session_json["well_data"]) # get well data from GAP such as GOR, limits and current routes
        session_json["unit_data"]["sep"]=st.get_sep_pres() # get separator pressure if state doesn't exist
    #------------------------------------------------------------------------------

    # group wells by unit for html page
    session_json["well_data_byunit"]=[{},{},{}]
    for well,val in session_json["well_data"].items():
        if "masked" in val: #required to know which well is masked/unmasked in GAP to include/exclude well in the list
            if val["masked"]==0:
                session_json["well_data_byunit"][val["unit_id"]][well]=val

    #save gathered data to json file
    save_session_json(session_json)


    page_active={"load_pcs":"","load_state":"","setup":"active","live":"","results":""}
    # render page, pass data dictionary to the page
    return render_template('setup.html',data=session_json,page_active=page_active)
"""========================================================================================="""



""" CLEAR STATE FUNCTION ==================================================================== """
@app.route('/clearstate', methods = ['POST'])
def clearstate():
    session.pop('state', None) # clears state in session
    return "Session['state'] cleared!"
"""========================================================================================="""



""" SAVE STATE FUNCTION ==================================================================== """
@app.route('/savestate', methods = ['POST'])
def savestate():
    session_json=request.json

    for well,val in session_json["well_data"].items(): # additional step to pre calculate required qgas_max equivalent to target FWHP
        # print(well,val)
        if "target_fwhp" in val:
            if val["target_fwhp"]>0:
                if MOCKUP:
                    # NetSim uses fwhp_min to reach target THP
                    # session_json["well_data"][well]["target_fwhp"]
                    session_json["well_data"][well]["fwhp_min"]=val["target_fwhp"] # mimic GAP behavior with qgas_max
                else:
                    pc_fwhp=session_json["well_data"][well]["pc"]["thps"]
                    pc_qgas=session_json["well_data"][well]["pc"]["qgas"]
                    # GAP uses qgas_max to reach target THP
                    session_json["well_data"][well]["qgas_max"]=np.interp(val["target_fwhp"],pc_fwhp,pc_qgas)


    session_jsonfile=os.path.join(uploader_dirname,r"temp\session.json")
    json.dump(request.json, open(session_jsonfile, 'w'))
    return "None"
"""========================================================================================="""



""" SAVE FWHP TO STATE FUNCTION ==================================================================== """
@app.route('/savestate_results', methods = ['POST'])
def savestate_results():
    fwhp_results=request.json # remember fwhp data from results page passed from AJAX call
    session_json=get_session_json()
    for well,s in fwhp_results["wells"].items(): # loop through fwhp data from results page
        session_json["well_data"][well]["target_fwhp"]=s["fwhp"] # overwrite existing session state fwhps with data from results page
        save_session_json(session_json)
        # Note: no need to check if session state exists because precondition to go to results page is to have state initialized
    return "None"
"""========================================================================================="""



""" SAVE LOADED STATE ==================================================================== """
@app.route('/savestate_loaded', methods = ['POST'])
def savestate_loaded():

    # get data loaded in load state page
    data=request.json
    loaded_state=data["state"]
    shut_the_rest=data["shut_the_rest"]
    session_json=get_session_json() # read session data

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

    save_session_json(session_json) # save data to file

    return "None"
"""========================================================================================="""



""" START GAP CALCULATION ==================================================================== """
@socketio.on('start_gap_calc')
def gap_calc_start():

    session_json=get_session_json()
    if MOCKUP:
        print("skip xls calc")
        post_opt_state=nsopt.run_optimization(session_json) # pass state to GAP to make calculations
    else:
        post_opt_state=gob.run_optimization(session_json) # pass state to GAP to make calculations
    #------------------------------------------------------------------------------
    return "None"
"""========================================================================================="""


""" START GAP CALCULATION ==================================================================== """
@socketio.on('start_route_opt')
def route_opt_start():

    session_json=get_session_json()
    if MOCKUP:
        print("skip xls calc")
        post_opt_state=nsopt.route_optimization(session_json)
    else:
        print("route_opt")
        post_opt_state=gob.route_optimization(session_json) # pass state to GAP to make calculations
    #------------------------------------------------------------------------------
    return "None"
"""========================================================================================="""


# @socketio.on('disconnect_gap_calc')
# def disconnect_calc_start():
#     print("hi")
#     return "None"
#
#
# @app.route('/stop', methods = ['POST'])
# def stop():
#     print("stop received")
#     disconnect(sid)
#     return "Session['state'] cleared!"



""" LOAD PCS ==================================================================== """
@socketio.on('load_pcs')
def load_pcs():
    print('start loading PCs')
    well_pcs=xl_setup.read_pcs()
    emit('load_progress',{"data":"Well PCs read from Deliverability complete"})

    print('saving PCs to session')
    session_json=get_session_json()
    session_json["well_pcs"]=well_pcs
    # for well,val in session_json["well_data"].items():
    #     if well in well_pcs: # create well record in does not exist in well_data
    #         session_json["well_data"][well]["pc"]=well_pcs[well]["pc"]
    save_session_json(session_json)

    print('loading PCs to GAP')
    pcs2gap.load_pcs2gap(well_pcs)
    # print(well_pcs)
    # json_fullpath_pcs=os.path.join(uploader_dirname,r"temp\well_pcs.json")
    # json.dump(well_pcs, open(json_fullpath_pcs, 'w'))

    emit('load_progress',{"data":"Finished PCs loading!"})

    return "None"
"""========================================================================================="""


""" SAVE RESULTS TO REFEREENCE JSON FILE==================================================== """
@socketio.on('save_2ref')
def save_2ref():
    json_fullpath=os.path.join(uploader_dirname,r"temp\session.json")
    data = json.load(open(json_fullpath))

    json_fullpath_ref=os.path.join(uploader_dirname,r"temp\session_ref_case.json")
    json.dump(data, open(json_fullpath_ref, 'w'))

    emit('save_complete',{"data":"Reference case saved"})
    #------------------------------------------------------------------------------
    return "None"
"""========================================================================================="""



""" REMOVE REFERENCE JSON FILE==================================================== """
@socketio.on('delete_refcase')
def delete_refcase_url():
    delete_refcase()
    emit('delete_complete',{"data":"Reference case deleted"})
    return "None"
"""========================================================================================="""

def delete_refcase():
    json_fullpath_ref=os.path.join(uploader_dirname,r"temp\session_ref_case.json")
    if os.path.isfile(json_fullpath_ref):
        os.remove(json_fullpath_ref)
    return "None"



""" SAVE SESSION JSON FILE==================================================== """
def save_session_json(session_json):
    json_fullpath=os.path.join(uploader_dirname,r"temp\session.json")
    json.dump(session_json, open(json_fullpath, 'w'),indent=4, sort_keys=True)

    return "None"
"""========================================================================================="""


""" CLEAR WELL DATA FROM SESSION JSON FILE==================================================== """
def clear_well_data_session_json(): # when user logged out well_data to clear for cleaning after user.
    session_json=get_session_json()
    session_json.pop('well_data', None)
    # session_json["well_data"]={}
    session_json["state"]=0
    save_session_json(session_json)
    return "None"
"""========================================================================================="""



""" READ SESSION JSON FILE==================================================== """
def get_session_json():
    json_fullpath=os.path.join(uploader_dirname,r"temp\session.json")
    if os.path.isfile(json_fullpath):
        data = json.load(open(json_fullpath))
    else:
        data={}
    return data
"""========================================================================================="""


""" READ PCS FROM JSON FILE==================================================== """
def get_well_pcs_json():
    json_fullpath_pcs=os.path.join(uploader_dirname,r"temp\well_pcs.json")
    if os.path.isfile(json_fullpath_pcs):
        well_pcs = json.load(open(json_fullpath_pcs))
    else:
        well_pcs={}
    return well_pcs
"""========================================================================================="""


""" PARSER GATHERING REPORT ==================================================================== """
def allowed_file(filename): # make sure file is one of allowed extentions (look on top)
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def merge_route_slot(result_text,well_details):
    result_text_new=[]
    for well in result_text:
        for w,val in well_details.items():
            if well[0]==w:
                for r in val["routes"]:
                    print(w,well[1],well[2],well[3])
                    print(w,r["unit"],r["rms"],r["tl"])
                    if well[1]==r["unit"] and well[2]==r["rms"] and well[3]==r["tl"]:

                        row=well
                        row.append(r["slot"])
                        result_text_new.append(row)
    return result_text_new

@app.route('/upload_gath_rep', methods=['POST'])
def upload_file():
    if request.method == 'POST': # check if method is POST
        # check if the post request has the file part
        if 'file' not in request.files: # check if file in received form
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '': # check if filename is not empty
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename): # check if file exists and file is one of the allowed (look on top)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) # save file in temp folder

            result_text,warn_text=gath_par.parse_gathering_report() # parse the data in excel file and return results
            well_details=xl_setup.read_conns()

            result_text=merge_route_slot(result_text,well_details)

            #remove file after getting data
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return jsonify({"result_text":result_text,"warn_text":warn_text}) # send back AJAX response with results from parsing
""" ==================================================================================== """


def ec_connect(driver):
    connStr = "DRIVER={"+driver+"};" +\
                "DSN=ECPROD;" +\
                "UID=ec_reader;" +\
                "PWD=veryhardpaS$w0rd;" +\
                "DBQ=ECPROD;"
    conn = pyodbc.connect(connStr)
    cursor = conn.cursor()
    return cursor,conn

def get_wellnames():
    dirname, filename = os.path.split(os.path.abspath(__file__))
    xl_fullpath=os.path.join(dirname,'static\well_connections.xlsm')
    book = xlrd.open_workbook(xl_fullpath)
    sheet = book.sheet_by_name("Wellnames")
    wells={}
    for r in range(1,sheet.nrows):
        w1=str(sheet.cell_value(r, 0)).replace('.0','')
        w2=str(sheet.cell_value(r, 1)).replace('.0','')
        wells[w1]=w2
    return wells

@app.route('/get_alloc_thp', methods=["POST"])
def get_alloc_thp():

    dt=request.json
    dt = datetime.datetime.strptime(dt,"%Y-%m-%d")
    cursor,conn = ec_connect(db_driver)
    #cursor,conn = ec_connect("Oracle in OraClient11g_32bit")
    dt_start=dt.strftime('%d/%m/%Y %H:%M:%S')
    dt_end=(dt+datetime.timedelta(hours=23.9999)).strftime('%d/%m/%Y %H:%M:%S')

    sqlstr="SELECT OBJECT_CODE,DAYTIME,AVG_WH_PRESS,ON_STREAM_HRS FROM DV_PWEL_DAY_STATUS "+\
            "WHERE DAYTIME BETWEEN to_date('"+dt_start+"','dd/mm/yyyy hh24:mi:ss') AND "+\
            "to_date('"+dt_end+"','dd/mm/yyyy hh24:mi:ss') ORDER BY OBJECT_CODE;"

    cursor.execute(sqlstr)
    thp_result=cursor.fetchall() # restructure list from db to send to jinja2

    wellnames=get_wellnames() # get wellnames PA vs GAP

    thps=[]
    for r in thp_result:
        row=[]
        if r[3]:
            if r[3]>0:
                row=[wellnames[str(r[0])],r[1].strftime('%Y-%m-%d'),r[2],r[3]]
                thps.append(row)

    return jsonify({"thps":thps})




@app.route('/netsim_test', methods = ['POST'])
def netsim_test():

    print('NS.DoGetAll("wells","label")')
    data=NS.DoGetAll("wells","label")
    print(data)

    print('NS.DoGet("wells/9815/gor")')
    data=NS.DoGet("wells/9815/gor")
    print(data)

    print('NS.DoSet("wells/9815/gor",1600.0)')
    data=NS.DoSet("wells/9815/gor",1600.0)
    print(data)

    print('NS.DoGet("wells/9815/gor")')
    data=NS.DoGet("wells/9815/gor")
    print(data)

    print('NS.DoSetAll("wells","dp",vals)')
    vals=[0,0]
    vals=NS.list2gapstr(vals)
    data=NS.DoSetAll("wells","dp",vals)
    print(data)

    print('NS.DoGetAll("wells","gor")')
    data=NS.DoGetAll("wells","gor")
    print(data)

    print('NS.DoCmd("calculate_network")')
    data=NS.DoCmd("calculate_network")
    print(data)

    print('NS.DoCmd("optimize_network")')
    data=NS.DoCmd("optimize_network")
    print(data)

    print('NS.DoGetAll("wells","results/fwhp")')
    data=NS.DoGetAll("wells","results/fwhp")
    print(data)

    return data
