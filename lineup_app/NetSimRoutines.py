import json
import requests


def dict2str(data):
    sorted_data=sorted(data,key=lambda x:x[0])
    data=""
    for d in sorted_data:
        data+=str(d[1])+"|"
    return data

def DoGet(item):
    dictToSend = {'path':item}
    headers = {'content-type': 'application/json'}
    res = requests.post('http://localhost:8080/api/doget', data=json.dumps(dictToSend),headers=headers)
    dictFromServer = res.json()
    data=str(dictFromServer["data"])

    return data


def DoGetAll(item,param):
    dictToSend = {'path':item,"search":param}
    headers = {'content-type': 'application/json'}
    res = requests.post('http://localhost:8080/api/dogetall', data=json.dumps(dictToSend),headers=headers)
    # res = requests.get('http://localhost:8080/api/optimize_network',headers = {'content-type': 'application/json'})
    dictFromServer = res.json()
    data=dict2str(dictFromServer["data"])

    return data


def DoSet(item,val):
    dictToSend = {'path':item,"val":val}
    headers = {'content-type': 'application/json'}
    res = requests.post('http://localhost:8080/api/doset', data=json.dumps(dictToSend),headers=headers)
    dictFromServer = res.json()
    data=str(dictFromServer["data"])

    return data


def DoSetAll(item,param,vals):
    dictToSend = {'path':item,"param":param,"vals":vals}
    headers = {'content-type': 'application/json'}
    res = requests.post('http://localhost:8080/api/dosetall', data=json.dumps(dictToSend),headers=headers)
    dictFromServer = res.json()
    data=dict2str(dictFromServer["data"])

    return data
