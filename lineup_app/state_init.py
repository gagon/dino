import json
import os


def init():

    # get current directory using os library
    dirname, filename = os.path.split(os.path.abspath(__file__))
    # construct excel file full path
    json_fullpath=os.path.join(dirname,"temp\state.json")
    state = json.load(open(json_fullpath))

    return state


if __name__=="__main__":

    state=init()
    print(state["fb_data"]["streams"]["constraints"])
