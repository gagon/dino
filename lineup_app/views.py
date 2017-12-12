from lineup_app import app
from flask import render_template, request,redirect, url_for, session, flash, jsonify

import pyodbc
import datetime
from flask_socketio import SocketIO, send, emit
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



# secret key initialized for the server
app.secret_key = 'any_random_string'
# socket IO initialized, time out set to 500 sec
socketio=SocketIO(app, ping_timeout=500)

uploader_dirname, uploader_filename = os.path.split(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(uploader_dirname,'temp')
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Flask-login initialized
login_manager = LoginManager()
login_manager.init_app(app)

# users dictionary to login to the app
# temporary solution, must be placed outside of the code (database or xls)
users = { # can add more users if needed
    'admin':{'password':'kpo'},
}

# Driver to be used to query data from EC. This is different on different computers
db_driver="Oracle in OraClient11g"
#db_driver="Oracle in OraClient11g_32_bit"



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
    clearstate()
    return redirect(url_for('index'))

# main fucntion where user is logged in if username and password are correct
# if not, redirect back to login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username in users:
            if request.form.get('password') == users[username]['password']:
                user = User()
                user.id = username
                flask_login.login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Incorrect")
        else:
            return render_template('login.html')
    return render_template('login.html')

# error handing in case of incorrect or no login, redirects to login page
@app.errorhandler(401)
def custom_401(error):
    return redirect(url_for('login'))

# main welcome page if logged in successfully
@app.route('/')
@login_required
def index():
    return render_template('index.html')

""" ========================================================================================================== """





""" GAP CALCULATION PAGE ==================================================================================== """
@app.route('/live')
@login_required
def live():
    # check is session "state" exists, if not send message and stop
    if not "state" in session:
        return "NO session state. Go back to setup and save state"
    # else load live page
    return render_template('live.html')
""" ========================================================================================================= """



""" GET GAP RESULTS =========================================================================================== """
@app.route('/results')
@login_required
def results():

    # check is session "state" exists, if not send message and stop
    if not "state" in session:
        return "NO session state. Go back to setup and save state"

    # get well connections from "well_connection.xlsm" file
    well_details=xl_setup.read_conns()
    # get MAPs from "Deliverability,xlsx" file
    well_maps=xl_setup.read_maps()

    # get well results from GAP
    #------------------------------------------------------------------------------
    # pc_data=ggr.get_all_unit_pc(well_details,session["state"]["wells"])
    pc_data=xlggr.xl_get_all_unit_pc(well_details,session["state"]["wells"])
    #------------------------------------------------------------------------------

    # a dictionary for mapping unit index and name
    unit_map={0:"KPC",1:"U3",2:"U2"}

    fb_data=fb.fb_init()
    fb_data=fb.calculate(pc_data,fb_data)

    #
    # get current directory using os library
    #dirname, filename = os.path.split(os.path.abspath(__file__))
    # construct excel file full path
    #json_fullpath=os.path.join(dirname,"static\\field_balance_plot.json")
    #fb_plot = json.load(open(json_fullpath))





    totals=[] # array to save unit totals and subtotals

    # loop through units
    for unit,unit_wells in enumerate(pc_data):

        unit_total_qgas=0.0 # initialise unit totals for Qgas
        unit_total_qoil=0.0 # initialise unit totals for Qoil
        rmss=[] # initialise RMS list

        # loop through wells in unit
        for rank,val in unit_wells.items():

            # merge pc_data with map from Deliverability
            well=pc_data[unit][rank]["wellname"]
            pc_data[unit][rank]["map"]=well_maps[well]["map"]
            pc_data[unit][rank]["target_fwhp"]=session["state"]["wells"][well]["fwhp"]

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
    data={"totals":totals,"wells":pc_data,"field":{"qgas":field_gas,"qoil":field_oil},"fb_data":fb_data}

    return render_template('results.html',data=data)
"""========================================================================================="""



""" LOAD PC PAGE RENDER ================================================================= """
@app.route('/load')
@login_required
def load():
    return render_template('load.html')
"""========================================================================================="""



""" LOAD STATE PAGE RENDER ================================================================= """
@app.route('/load_state')
@login_required
def load_state():
    # check is session "state" exists, if not send message and stop
    if not "state" in session:
        return "NO session state. Go back to setup and save state"
    return render_template('load_state.html')
"""========================================================================================="""



""" SETUP PAGE ============================================================================ """
@app.route('/setup')
@login_required
def setup():

    # get well connections from "well_connections.xlsm" file
    well_details=xl_setup.read_conns()
    # get MAPs from "Deliverability.xlsx" file
    well_maps=xl_setup.read_maps()

    # get or set well routes and Separator pressure depending on state
    if len(session)>0: # if session exists
        if "state" in session: # if state has been saved in session
            # for sss,ss in session["state"]["wells"].items():
            #     print(sss,ss)

            #------------------------------------------------------------------------------
            #st.set_unit_routes(well_details,session["state"]["wells"]) # set well routes as per state
            xlst.xl_set_unit_routes(well_details,session["state"]["wells"]) # set well routes as per state
            #------------------------------------------------------------------------------

            #------------------------------------------------------------------------------
            #st.set_sep_pres(session["state"]["sep"]) # set separator pressure as per state
            xlst.xl_set_sep_pres(session["state"]["sep"]) # set separator pressure as per state
            #------------------------------------------------------------------------------

            sep=session["state"]["sep"] # remember what set to separator pressure to show it on setup page
        else:
            #------------------------------------------------------------------------------
            #sep=st.get_sep_pres() # get separator pressure if state doesn't exist
            sep=xlst.xl_get_sep_pres() # get separator pressure if state doesn't exist
            #------------------------------------------------------------------------------
    else:
        #------------------------------------------------------------------------------
        # sep=st.get_sep_pres() # get separator pressure if state doesn't exist
        sep=xlst.xl_get_sep_pres() # get separator pressure if state doesn't exist
        #------------------------------------------------------------------------------

    data={} # initialize data dictionary to pass to setup.html
    data["sep"]=sep # save separator pressures to data dict

    #------------------------------------------------------------------------------
    #data["well_data"]=st.get_all_well_data(well_details) # get well data from GAP such as GOR, limits and current routes
    data["well_data"]=xlst.xl_get_all_well_data(well_details) # get well data from GAP such as GOR, limits and current routes
    #------------------------------------------------------------------------------

    for unit,unit_wells in enumerate(data["well_data"]): # loop through units
        for rank,val in unit_wells.items(): # loop through wells in unit
            well=data["well_data"][unit][rank]["wellname"] # remember wellname

            data["well_data"][unit][rank]["map"]=well_maps[well]["map"] # merge well data with well MAPs to pass it to page


            # initialize well data fwhp and in_opt to default
            data["well_data"][unit][rank]["fwhp"]=""
            data["well_data"][unit][rank]["in_opt"]=1
            if len(session)>0: # if session exists
                if "state" in session: # if state exists in session
                    if well in session["state"]["wells"]: # if well exists in session
                        # then overwrite well data fwhp and in_opt as per session
                        data["well_data"][unit][rank]["fwhp"]=session["state"]["wells"][well]["fwhp"]
                        data["well_data"][unit][rank]["in_opt"]=session["state"]["wells"][well]["in_opt"]


    # initialise constraints to default
    data["constraints"]={
        "kpc":{"qgas":100000,"qoil":100000},
        "u3":{"qgas":100000,"qoil":100000},
        "u2":{"qgas":100000,"qoil":100000},
    }
    if len(session)>0: # if session exists
        if "state" in session: # if state in session
            if "constraints" in session["state"]: # if constraints in state
                # then overwrite constraints as per session
                data["constraints"]=session["state"]["constraints"]

    # render page, pass data dictionary to the page
    return render_template('setup.html',data=data)
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
    session.pop('state', None) # clears state in session
    session["state"]=request.json # set state to the data passed from AJAX call in setup page javascript
    session.modified=True
    return "None"
"""========================================================================================="""



""" SAVE STATE FUNCTION ==================================================================== """
@app.route('/savestate_results', methods = ['POST'])
def savestate_results():
    fwhp_results=request.json # remember fwhp data from results page passed from AJAX call
    for well,s in fwhp_results["wells"].items(): # loop through fwhp data from results page
        session["state"]["wells"][well]["fwhp"]=s["fwhp"] # overwrite existing session state fwhps with data from results page
        # Note: no need to check if session state exists because precondition to go to results page is to have state initialized
    session.modified=True
    return "None"
"""========================================================================================="""



""" SAVE LOADED STATE ==================================================================== """
@app.route('/savestate_loaded', methods = ['POST'])
def savestate_loaded():

    # get data loaded in load state page
    data=request.json
    loaded_state=data["state"]
    shut_the_rest=data["shut_the_rest"]
    print(shut_the_rest)
    # get MAPs from "Deliverability.xlsx" file.
    # This is done in order to check if loaded fwhp is lower than MAP, if it is, then fwhp is set to MAP
    well_maps=xl_setup.read_maps()

    wells2delete=[]
    for well,s in loaded_state.items(): # loop through loaded well data
        if well in well_maps: # if wells exists in well MAPs. This is to avoid incorrect or non-existing wells to be passed to session state
            if s["fwhp"]: # if loaded fwhp is not empty
                if float(s["fwhp"])<float(well_maps[well]["map"]) and float(s["fwhp"])!=float(-1): # if loaded fwhp is lower than MAP and not -1
                    loaded_state[well]["fwhp"]=well_maps[well]["map"] # then set fwhp to MAP
            else:
                loaded_state[well]["fwhp"]=well_maps[well]["map"] # else set it loaded fwhp
        else:
            wells2delete.append(well) # remember wells to delete if well does not exist

    # delete wells with incorrect names/ does not exist
    for w in wells2delete:
        loaded_state.pop(w) # remove loaded well data if well does not exists in well MAPs

    if len(session)>0: # if session exists
        if "state" in session: # if state exists
            if "wells" in session["state"]: # if wells exists in session

                for well,s in loaded_state.items(): # loop through loaded well data
                    # check if loaded well exists in session
                    if well in session["state"]["wells"]:
                        if s["selected_route"]: # if loaded route is not empty
                            session["state"]["wells"][well]["selected_route"]=s["selected_route"] # then save it to session state
                        session["state"]["wells"][well]["fwhp"]=s["fwhp"] # overwrite loaded well fwhp to session state

                # when bulk copy/paste states, you can choose to shut the rest of wells other than loaded
                # this is done in case of replication of certain day in the field
                if shut_the_rest==1:
                    for well,s in session["state"]["wells"].items(): # loop through loaded well data
                        # check if loaded well exists in session
                        if not well in loaded_state:
                            print("shut",well)
                            session["state"]["wells"][well]["fwhp"]=-1

        else:
            session["state"]={} # initialize state if no state
            session["state"]["wells"]=loaded_state # save loaded data to state
    else:
        session["state"]={} # initialize state if no state
        session["state"]["wells"]=loaded_state # save loaded data to state

    session.modified=True
    return "None"
"""========================================================================================="""



""" HEARTBEAT OF SERVER ==================================================================== """
# @socketio.on('heartbeat_ask')
# def heartbeat_reply():
#     print('heartbeat question: what time is it?')
#     emit('heartbeat_reply',{"data":str(datetime.datetime.now())})
#     return None
#
# @app.route('/heartbeat')
# @login_required
# def heartbeat():
#     data={}
#     return render_template('heartbeat.html',data=data)
"""========================================================================================="""


""" START GAP CALCULATION ==================================================================== """
@socketio.on('start_gap_calc')
def gap_calc():
    print('received start command!')
    #------------------------------------------------------------------------------
    # post_opt_state=gob.run_optimization(session["state"]) # pass state to GAP to make calculations
    post_opt_state=xlgob.xl_run_optimization(session["state"]) # pass state to GAP to make calculations
    #------------------------------------------------------------------------------
    return "None"
"""========================================================================================="""



""" LOAD PCS ==================================================================== """
@socketio.on('load_pcs')
def load_pcs():
    print('start loading PCs')
    well_pcs=xl_setup.read_pcs()
    emit('load_progress',{"data":"Well PCs read from Deliverability complete"})
    pcs2gap.load_pcs2gap(well_pcs)
    return "None"
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
