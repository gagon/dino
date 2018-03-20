import os
import time
import datetime
#import cPickle
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from scipy import signal
import numpy
from numpy import *


#import pywintypes
from win32com.client import Dispatch

def Initialize():

    PISDK = Dispatch("PISDK.PISDK.1")
    server = PISDK.Servers.DefaultServer
    server.Open()
#    print(PISDK.Servers)
#    sys.exit()
#    server = PISDK.Servers["KPOAPI03"]
#    server.Open("UID='BUILTIN\Guests';PWD=''")


    return server


def RestartServer(server):

    server.Close()
    server2 = Initialize()

    return server2


def StopServer(server):

    server.Close()

    return None

def ExtractData(server, tag):

    point = server.PIPoints(tag)
    data = point.Data

    return data, point.PointType


def FormatDates(start, end):

    if isinstance(start, datetime.datetime):
        start = SecondsDatetime(start)
    else:
        start = SecondsDate(start)

    if isinstance(end, datetime.datetime):
        end = SecondsDatetime(end)
    else:
        end = SecondsDate(end)

    return start, end


def SecondsDatetime(value):

    value = value.isoformat().split('.')[0].replace('T',' ')
    #'2009-07-04 18:30:47'
    pattern = '%Y-%m-%d %H:%M:%S'
    value = int(time.mktime(time.strptime(value, pattern)))

    return value


def SecondsDate(value):

    value = time.mktime(time.strptime(value, "%d/%m/%Y"))
    return value


def InterpolatedValues(data, start, end, interval="1d"):

    # start, end = FormatDates(start, end)

    pvs = data.InterpolatedValues2(start, end, interval, "", 0, None)
    dates, points = [], []

    for pv in pvs:

        date = pv.TimeStamp.UTCSeconds
        date = time.gmtime(float(date))


        date = datetime.datetime(*date[0:6])
        value = pv.Value
        # print(date,value)

        try:
            value = float(value)
        # except AttributeError:
        except:
            continue

        dates.append(date)
        points.append(value)

    return dates, points


def SummaryValues(data, start, end):

    start, end = FormatDates(start, end)

    pv = data.Summary(start, end, 5, 0, None)
    return pv.Value


def RecordedValues(data, start, end):

#    start, end = FormatDates(start, end)

#    print(start,end)

    pvs = data.RecordedValues(start, end, 0, "", 0, None)
    dates, points = [], []
    piPoints = len(pvs)

    for pv in pvs:
        date = pv.TimeStamp.UTCSeconds
        date = time.gmtime(float(date))

        try:
            value = float(str(pv.Value))
            dates.append(datetime.datetime(*date[0:6]))
            points.append(value)
        except ValueError:
            continue

    return dates, points


def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise(ValueError, "smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise(ValueError, "Input vector needs to be bigger than window size.")


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise(ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    s=numpy.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=numpy.ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')

    y=numpy.convolve(w/w.sum(),s,mode='valid')
    return y




if __name__=="__main__":

    PI=Initialize()

    tag="KA:Unit3:1E150_TI012"
#    tag="Karachaganak_Test\Wells\Production Wells\106|MAP"
    data, pointType = ExtractData(PI, tag)

    start='01/03/2018 00:00:00'
    end='03/03/2018 00:00:00'
    dummy, values = RecordedValues(data, start, end)
    values=numpy.array(values)

    v=signal.medfilt(values,9)
    smooth_window=100
    v=smooth(v,smooth_window,"hanning")
    print(len(v),len(values))
#    v=signal.spline_filter(values, lmbda=5.0)
#    b, a = signal.butter(8, 0.125)
#    b, a = signal.ellip(3, 0.00001, 10, 0.5)
#    b, a = signal.butter(4, 100, 'low', analog=True)
#    fgust = signal.filtfilt(b, a, values, padlen=50)
#    v=signal.bspline(values, 3)

#    print(dummy)
#    print(values)
    dates=mdates.date2num(dummy)
    plt.plot(dates,values)
#    plt.plot(v)
    plt.plot(dates,v[int(smooth_window/2):-int((smooth_window/2-1))])
    plt.show()

    PI=StopServer(PI)
