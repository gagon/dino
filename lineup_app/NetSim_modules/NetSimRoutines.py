import json
import requests
from lineup_app.NetSim import nsviews as nsv

def dict2str(data):
    sorted_data=sorted(data,key=lambda x:x[0])
    data=""
    for d in sorted_data:
        data+=str(d[1])+"|"
    return data

def DoGet(item):
    dictToSend = {'path':item}
    # headers = {'content-type': 'application/json'}
    # res = requests.post('http://localhost:8080/api/doget', data=json.dumps(dictToSend),headers=headers)
    # dictFromServer = res.json()
    res = nsv.dino_get_item_api(dictToSend)
    dictFromServer = json.loads(res)

    data=str(dictFromServer["data"]) # to mimic Openserver

    return data


def DoGetAll(item,param):
    dictToSend = {'path':item,"search":param}
    # headers = {'content-type': 'application/json'}
    # res = requests.post('http://localhost:8080/api/dogetall', data=json.dumps(dictToSend),headers=headers)
    # dictFromServer = res.json()
    res = nsv.dino_get_item_all_api(dictToSend)
    dictFromServer = json.loads(res)

    data=dict2str(dictFromServer["data"]) # to mimic Openserver

    return data


def DoSet(item,val):
    dictToSend = {'path':item,"val":val}
    # headers = {'content-type': 'application/json'}
    # res = requests.post('http://localhost:8080/api/doset', data=json.dumps(dictToSend),headers=headers)
    # dictFromServer = res.json()
    res = nsv.dino_set_item_api(dictToSend)
    dictFromServer = json.loads(res)

    data=str(dictFromServer["data"]) # to mimic Openserver

    return data


def DoSetAll(item,param,vals,t):
    dictToSend = {'path':item,"param":param,"vals":gapstr2list(vals,t)}
    # headers = {'content-type': 'application/json'}
    # res = requests.post('http://localhost:8080/api/dosetall', data=json.dumps(dictToSend),headers=headers)
    # dictFromServer = res.json()
    res = nsv.dino_set_item_all_api(dictToSend)
    # print(type(res))
    dictFromServer = json.loads(res)

    data=dict2str(dictFromServer["data"]) # to mimic Openserver

    return data


def DoCmd(cmd):
    # headers = {'content-type': 'application/json'}
    # res = requests.get('http://localhost:8080/api/'+cmd,headers=headers)
    # dictFromServer = res.json()
    if cmd=="calculate_network":
        res = nsv.dino_calculate_network_api()
    elif cmd=="optimize_network":
        res = nsv.dino_optimize_network_api()
    elif cmd=="build_network":
        res = nsv.dino_build_network_api()

    dictFromServer = json.loads(res)

    data=str(dictFromServer["data"]) # to mimic Openserver

    return data

def list2gapstr(l):
    l=list(map(str, l))
    return "|".join(l)+"|"

def gapstr2list(l,t):
    l=l.split("|")[:-1]
    if t=="float":
        l=[float(i) for i in l]
    elif t=="int":
        l=[int(i) for i in l]
    return l
