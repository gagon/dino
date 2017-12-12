import time
from win32com.client import Dispatch


class PetexException(Exception):

    def __init__(self, message):

        self.message = message


    def GetError(self):

        return self.message


    def __str__(self):
            
        return self.message
    

def Initialize():

    server = Dispatch("PX32.OpenServer.1")
    return server


def Stop():
    
    server = None
    return server


def DoCmd(server, command):
    
    lErr = server.DoCommand(command)

    if lErr > 0:
        raise PetexException("DoCmd: %s"%server.GetErrorDescription(lErr))
    

def DoSet(server, Sv, Val):
    
    lErr = server.SetValue(Sv, Val)
    appName = GetAppName(Sv)
    lErr = server.GetLastError(appName)

    if lErr > 0:
        raise PetexException("DoSet: %s"%server.GetErrorDescription(lErr))
    

def DoGet(server, Gv):
    
    value = server.GetValue(Gv)
    appName = GetAppName(Gv)
    lErr = server.GetLastError(appName)

    if lErr > 0:
        raise PetexException("DoGet: %s"%server.GetLastErrorMessage(appName))
    
    return value


def DoSlowCmd(server, command):
    
    appName = GetAppName(command)
    lErr = server.DoCommandAsync(command)
    
    if lErr > 0:
        raise PetexException("DoSlowCmd 1: %s"%server.GetErrorDescription(lErr))

    secs = 1
    while server.IsBusy(appName) > 0:
        time.sleep(1)
        secs += 1

    lErr = server.GetLastError(appName)
    if lErr > 0:
        raise PetexException("DoSlowCmd 2: %s"%server.GetErrorDescription(lErr))
    

def DoSlowGAPFunc(server, Gv):
    
    DoSlowCmd(server, Gv)
    DoGet(server, "GAP.LASTCMDRET")
    
    lErr = server.GetLastError("GAP")
    if lErr > 0:
        raise PetexException("DoSlowGAPFunc: %s"%server.GetErrorDescription(lErr))


def DoGAPFunc(server, Gv):
    
    DoCmd(server, Gv)
    DoGet(server, "GAP.LASTCMDRET")
    
    lErr = server.GetLastError("GAP")
    if lErr > 0:
        raise PetexException("DoGAPFunc: %s"%server.GetErrorDescription(lErr))


def DoSlowProsperFunc(server, Gv):

    DoSlowCmd(server, Gv)
    DoGet("PROSPER.LASTCMDRET")
    
    lErr = server.GetLastError("PROSPER")
    if lErr > 0:
        raise PetexException("DoProsperFunc: %s"%server.GetErrorDescription(lErr))
    

def GetAppName(command):
    
   point = command.index(".")
   appName = command[0:point].upper()

   if appName not in ["PROSPER", "MBAL", "GAP", "PVT", "RESOLVE", "REVEAL"]:
       raise PetexException("Unrecognised application name in tag string (%s)"%appName)
    
   return appName


