
from lineup_app import app
from flask import render_template, request,redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, send, emit,disconnect
import flask_login as flask_login
from flask_login import LoginManager, UserMixin, login_required
from werkzeug.utils import secure_filename

import pyodbc
import datetime
import os
import xlrd
import json
import numpy as np

from lineup_app.GAP_modules import GAP_optimization as gob
from lineup_app.GAP_modules import GAP_get_results as ggr
from lineup_app.GAP_modules import GAP_setup as st
from lineup_app.GAP_modules import GAP_load_pcs2gap as pcs2gap

from lineup_app.utils import xl_setup
from lineup_app.utils import gathering_parser as gath_par
from lineup_app.utils import field_balance as fb
from lineup_app.utils import utils
from lineup_app.utils import results as rs
from lineup_app.utils import optimize_routing as ro

from lineup_app.NetSim_modules import NetSimRoutines as NS
from lineup_app.NetSim_modules import NetSim_setup as nsst
from lineup_app.NetSim_modules import NetSim_get_results as nsgr
from lineup_app.NetSim_modules import NetSim_optimization as nsopt
from lineup_app.NetSim_modules import NetSim_load_pcs2ns as pcs2ns




# use mockup from NetSim file
MOCKUP=True



# secret key initialized for the server
app.secret_key = 'any_random_string'
# socket IO initialized, time out set to 500 sec
socketio=SocketIO(app, ping_timeout=500000)


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
    utils.clear_well_data_session_json()
    utils.delete_refcase()
    session.pop("user",None)
    return redirect(url_for('index'))

# main fucntion where user is logged in if username and password are correct
# if not, redirect back to login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    page_active={"load_pcs":"","load_state":"","setup":"","live":"","results":""}

    user=""
    if "user" in session:
        user=session["user"]

    else:

        if request.method == 'POST':
            username = request.form.get('username')
            if username in users:
                if request.form.get('password') == users[username]['password']:
                    user = User()
                    user.id = username
                    flask_login.login_user(user)
                    session["user"]=str(request.remote_addr)
                    return redirect(url_for('index'))
                else:
                    flash("Incorrect")
            else:
                return render_template('login.html',page_active=page_active)
    return render_template('login.html',page_active=page_active,user=user)

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


""" SETUP PAGE ============================================================================ """
@app.route('/setup')
@login_required
def setup():

    session_json=utils.get_session_json() # read from json file all necessary app data

    if not "well_data" in session_json: # create a well_data if does not exist, this normally happens very first time user logs in.
        session_json["well_data"]={}
        # populate well data with wells from GAP
        if MOCKUP:
            session_json["well_data"]=nsst.get_gap_wells()
        else:
            print("add GAP openserver")
        print(session_json["well_data"])

    # get well connections from "well_connections.xlsm" file
    session_json["well_data"]=xl_setup.read_conns(session_json["well_data"])

    # get MAPs from "Deliverability.xlsx" file
    session_json["well_data"]=xl_setup.read_maps(session_json["well_data"])

    #------------------------------------------------------------------------------
    if MOCKUP:
        if session_json["state"]==1: # check if state has been saved by the user (1)
            nsst.set_unit_routes(session_json["well_data"]) # set well routes as per state
            nsst.set_sep_pres(session_json["unit_data"]) # set separator pressure as per state

        session_json["well_data"]=nsst.get_all_well_data(session_json["well_data"])
        session_json["unit_data"]=nsst.get_sep_pres(session_json["unit_data"])
    else:
        if session_json["state"]==1: # check if state has been saved by the user (1)
            st.set_unit_routes(session_json["well_data"]) # set well routes as per state
            st.set_sep_pres(session_json["unit_data"]) # set separator pressure as per state

        session_json["well_data"]=st.get_all_well_data(session_json["well_data"]) # get well data from GAP such as GOR, limits and current routes
        session_json["unit_data"]=st.get_sep_pres(session_json["unit_data"]) # get separator pressure if state doesn't exist
    #------------------------------------------------------------------------------

    # group wells by unit for html page
    session_json=utils.make_well_data_by_unit(session_json)

    # save gathered data to json file
    utils.save_session_json(session_json)

    page_active={"load_pcs":"","load_state":"","setup":"active","live":"","results":""}
    # render page, pass data dictionary to the page
    return render_template('setup.html',data=session_json,page_active=page_active)
"""========================================================================================="""


""" GAP CALCULATION PAGE ==================================================================================== """
@app.route('/live')
@login_required
def live():
    session_json=utils.get_session_json()
    if not "well_data" in session_json: # check if state was exists. well_data ~ state
        return "NO session well state. Go back to <b>Setup</b> and save state"

    page_active={"live":"active"}

    return render_template('live.html',page_active=page_active)
""" ========================================================================================================= """


""" GAP CALCULATION PAGE ==================================================================================== """
@app.route('/live_ro')
@login_required
def live_ro():
    session_json=utils.get_session_json()
    if not "well_data" in session_json: # check if state was exists. well_data ~ state
        return "NO session well state. Go back to <b>Setup</b> and save state"
    ro_data=ro.get_well_routes(session_json)
    comb_num=ro.count_combs(ro_data)
    page_active={"live_ro":"active"}
    return render_template('live_ro.html',page_active=page_active,ro_data=ro_data,comb_num=comb_num)
""" ========================================================================================================= """


""" GET GAP RESULTS =========================================================================================== """
@app.route('/results')
@login_required
def results():

    session_json=utils.get_session_json()

    if not "well_data" in session_json: # check if state was exists. well_data ~ state
        return "NO session well state. Go back to <b>Setup</b> and save state"

    # get well results from GAP
    #------------------------------------------------------------------------------

    # get results from GAP or mockup excel
    if MOCKUP:
        session_json["well_data"]=nsgr.get_all_well_data(session_json)
    else:
        session_json["well_data"]=ggr.get_all_well_data(session_json)
    #------------------------------------------------------------------------------

    # group wells by unit for html page
    session_json=utils.make_well_data_by_unit(session_json)

    # calculate totals by field/unit/rms
    session_json["totals"]=rs.calculate_totals(session_json["well_data_byunit"])

    # field balance calculation
    session_json["fb_data"]=fb.calculate(session_json)

    # this is done so that routings/sep pres dont get updated as cant be done on results page
    session_json["state"]=0

    # save results to json
    utils.save_session_json(session_json)

    # merge data to present if ref case exists
    data,merge_done=rs.merge_ref(session_json)

    page_active={"load_pcs":"","load_state":"","setup":"","live":"","results":"active"}

    return render_template('results.html',data=data,page_active=page_active,merge_done=merge_done)
"""========================================================================================="""


""" LOAD PC PAGE RENDER ================================================================= """
@app.route('/load')
@login_required
def load():
    session_json=utils.get_session_json()
    if not "well_data" in session_json: # check if state was exists. well_data ~ state
        return "NO session well state. Go back to <b>Setup</b> and save state"
    page_active={"load_pcs":"active","load_state":"","setup":"","live":"","results":""}
    return render_template('load.html',page_active=page_active)
"""========================================================================================="""


""" LOAD STATE PAGE RENDER ================================================================= """
@app.route('/load_state')
@login_required
def load_state():
    session_json=utils.get_session_json()
    if not "well_data" in session_json: # check if state was exists. well_data ~ state
        return "NO session well state. Go back to <b>Setup</b> and save state"
    page_active={"load_pcs":"","load_state":"active","setup":"","live":"","results":""}
    return render_template('load_state.html',page_active=page_active)
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
    session_json=utils.calc_target_fwhps(request.json)
    utils.save_session_json(session_json)
    return jsonify({'data':"Saved State successfully!\nReload Page to update tables"})
"""========================================================================================="""


""" SAVE FWHP TO STATE FUNCTION ==================================================================== """
@app.route('/savestate_results', methods = ['POST'])
def savestate_results():
    fwhp_results=request.json # remember fwhp data from results page passed from AJAX call
    session_json=utils.get_session_json()
    for well,s in fwhp_results["wells"].items(): # loop through fwhp data from results page
        session_json["well_data"][well]["target_fwhp"]=s["fwhp"] # overwrite existing session state fwhps with data from results page
        utils.save_session_json(session_json)
        # Note: no need to check if session state exists because precondition to go to results page is to have state initialized
    return "None"
"""========================================================================================="""


""" SAVE LOADED STATE ==================================================================== """
@app.route('/savestate_loaded', methods = ['POST'])
def savestate_loaded():
    loaded_data=request.json # get data loaded in load state page
    session_json=utils.get_session_json() # read session data
    session_json=utils.save_loaded2session(session_json,loaded_data) # populate session with loaded data
    utils.save_session_json(session_json) # save data to file

    return "None"
"""========================================================================================="""


""" START GAP CALCULATION ==================================================================== """
@socketio.on('start_gap_calc')
def start_gap_calc():

    session_json=utils.get_session_json()
    if MOCKUP:
        print("skip xls calc")
        post_opt_state=nsopt.run_optimization(session_json,1) # pass state to GAP to make calculations, mode 1= normal optimization
    else:
        post_opt_state=gob.run_optimization(session_json,"None",1) # pass state to GAP to make calculations, "None" is placeholder for PE_server
    #------------------------------------------------------------------------------
    return "None"
"""========================================================================================="""


""" START GAP CALCULATION ==================================================================== """
@socketio.on('start_route_opt')
def start_route_opt(data):
    session_json=utils.get_session_json()
    ro.route_optimization(session_json,data["ro_data"],data["filters"],MOCKUP)
    return "None"
"""========================================================================================="""

#
# """ START GAP CALCULATION ==================================================================== """
# @socketio.on('prep_route_opt')
# def prep_route_opt():
#
#     session_json=utils.get_session_json()
#
#     ro.prep_route_opt(session_json)
#
#     # if MOCKUP:
#     #     print("skip xls calc")
#     #     post_opt_state=nsopt.route_optimization(session_json)
#     # else:
#     #     print("route_opt")
#     #     post_opt_state=gob.route_optimization(session_json) # pass state to GAP to make calculations
#     #------------------------------------------------------------------------------
#     return "None"
# """========================================================================================="""


#
""" START GAP CALCULATION ==================================================================== """
@socketio.on('update_combs')
def update_combs(data):
    session_json=utils.get_session_json()
    combs=ro.generate_comb2(data["ro_data"])
    # for comb in combs:
    #     for c in comb:
    #         print(c)
    #     print("--")
    # data["filters"]["tl_max_num"]
    # data["filters"]["test_max_num"]
    # print(data["filters"])
    # print(session_json.keys())
    combs=ro.filter_combs(combs,data["filters"],session_json)
    # print("++++++++++++++++++++++++++")
    # for comb in combs:
    #     for c in comb:
    #         print(c)
    #     print("--")
    emit("comb_num",{"comb_num":len(combs)})
    return "None"
"""========================================================================================="""




""" LOAD PCS ==================================================================== """
@socketio.on('load_pcs')
def load_pcs():
    print('start loading PCs')
    well_pcs=xl_setup.read_pcs()
    emit('load_progress',{"data":"Well PCs read from Deliverability complete"})

    print('saving PCs to session')
    session_json=utils.get_session_json()
    session_json["well_pcs"]=well_pcs
    utils.save_session_json(session_json)

    print('loading PCs to GAP')
    if MOCKUP:
        pcs2ns.load_pcs2ns(well_pcs)
    else:
        pcs2gap.load_pcs2gap(well_pcs)

    emit('load_progress',{"data":"Finished PCs loading!"})

    return "None"
"""========================================================================================="""


""" SAVE RESULTS TO REFEREENCE JSON FILE==================================================== """
@socketio.on('save_2ref')
def save_2ref():
    session_json=utils.get_session_json()
    utils.save_2ref(session_json)
    emit('save_complete',{"data":"Reference case saved"})
    return "None"
"""========================================================================================="""


""" REMOVE REFERENCE JSON FILE==================================================== """
@socketio.on('delete_refcase')
def delete_refcase_url():
    utils.delete_refcase()
    emit('delete_complete',{"data":"Reference case deleted"})
    return "None"
""" PARSER GATHERING REPORT ==================================================================== """

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
        if file and utils.allowed_file(file.filename): # check if file exists and file is one of the allowed (look on top)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) # save file in temp folder

            result_text,warn_text=gath_par.parse_gathering_report() # parse the data in excel file and return results
            well_details=xl_setup.read_conns()

            result_text=utils.merge_route_slot(result_text,well_details)

            #remove file after getting data
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return jsonify({"result_text":result_text,"warn_text":warn_text}) # send back AJAX response with results from parsing
""" ==================================================================================== """

""" GET DATA FROM EC ==================================================================== """
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

    sqlstr=\
    """
    SELECT OBJECT_CODE,DAYTIME,AVG_WH_PRESS,ON_STREAM_HRS
    FROM DV_PWEL_DAY_STATUS
    WHERE DAYTIME BETWEEN
            to_date('{0}','dd/mm/yyyy hh24:mi:ss') AND
            to_date('{1}','dd/mm/yyyy hh24:mi:ss')
    ORDER BY OBJECT_CODE;
    """
    sqlstr=sqlstr.format(dt_start, dt_end)

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


""" SOCKETIO HEARTBEAT ==================================================== """
@socketio.on('ping')
def ping():
    emit("ping")
    return "None"
"""========================================================================================="""


# help page
@app.route('/help')
@login_required
def help():
    page_active={"load_pcs":"","load_state":"","setup":"","live":"","results":"","help":"active"}
    return render_template('help.html',page_active=page_active)
