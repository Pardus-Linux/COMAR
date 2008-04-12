# -*- coding: utf-8 -*-

### Modeline Calculation ###
def GetInt(name, dict, default=0):
    _str = dict.get(name , default)
    try:
        return int(_str)
    except:
        return default

# _ GetFloat ___________________________________________________________
def GetFloat(name, dict, default=0.0):
    _str = dict.get(name , default)
    try:
        return float(_str)
    except:
        return default


# _ ModeLine ___________________________________________________________
def ModeLine(dict={}):
    '''
    This routine will calculate XF86Config Modeline entries.
    The Parameters are supplies as a dictionary due to the large number.
    The Calculated values are also returned in dictionary form.

    The parameter dictionary entries are:
    hPix       Horizontal displayed pixels    Default: 1280)
    hSync      Horizontal sync in uSec        Default: 1)
    hBlank     Horizontal blanking in uSec    Default: 3)
    vPix       Vertical displayed pixels      Default: 960)
    vFreq      Vertical scan frequency in Hz  Default: 75)
    vSync      Vertical sync in uSec          Default: 0)
    vBlank     Vertical blanking in uSec      Default: 500)
    v4x3       Constrain h/v to 4/3           Default: 0 (not constrained)

    hRatio1    Horizontal front poarch ratio  Default: 1)
    hRatio2    Horizontal sync ratio          Default: 4)
    hRatio3    Horizontal back poarch ratio   Default: 7)
    vRatio1    Vertical front poarch ratio    Default: 1)
    vRatio2    Vertical sync ratio            Default: 1)
    vRatio3    Vertical back poarch ratio     Default: 10)

    If v4x3="1" vPix is ignored.

    If any of the following:hSync, hBlanking, vSync, vBlanking
    are not specified then they are set based on the ratios,
    at a minimum is is best to specify either sync or blanking.

    The return dictionary entries are:
    The "entry" value is really all that is needed
    entry     Modeline entry string

    These are the values that make up the modeline entry
    dotClock    Dot clock in MHz
    hPix        Horizontal displayed pixels
    hFreq       Horizontal scan frequency in Hz.
    hTim1       Horizontal front poarch pixels
    hTim2       Horizontal sync pixels
    hTim3       Horizontal back poarch pixels
    vPix        Vertical displayed pixels
    vFreq       Vertical scan frequency in Hz.
    vTim1       Vertical front poarch pixels
    vTim2       Vertical sync pixels
    vTim3       Vertical back poarch pixels
    '''
    results = {}
    hPix    = GetInt(  "hPix"    , dict, 1280)
    hSync   = GetFloat("hSync"   , dict, 1)
    hBlank  = GetFloat("hBlank"  , dict, 3)
    hRatio1 = GetFloat("hRatio1" , dict, 1)
    hRatio2 = GetFloat("hRatio2" , dict, 4)
    hRatio3 = GetFloat("hRatio3" , dict, 7)
    vPix    = GetInt(  "vPix"    , dict, 960)
    vFreq   = GetFloat("vFreq"   , dict, 75)
    vSync   = GetFloat("vSync"   , dict, 0)
    vBlank  = GetFloat("vBlank"  , dict, 500)
    vRatio1 = GetFloat("vRatio1" , dict, 1)
    vRatio2 = GetFloat("vRatio2" , dict, 1)
    vRatio3 = GetFloat("vRatio3" , dict, 10)
    if (dict.has_key("v4x3")    == 0):
        v4x3        = ""
    else:
        v4x3        = "checked"
        vPix        = int(hPix) / 4 * 3

    vSyncUs = vSync / 1000000.0
    vBlankUs = vBlank / 1000000.0

    vRatioT = vRatio1 + vRatio2 + vRatio3
    if   ((vSyncUs > 0.0) and (vBlankUs > 0.0)):
        vRatio2 = (vRatio1 + vRatio3) * (vSyncUs / (vBlankUs - vSyncUs))
        vRatioT = vRatio1 + vRatio2 + vRatio3
    elif ((vSyncUs > 0.0) and (vBlankUs <= 0.0)):
        vBlankUs = vSyncUs * (vRatioT / vRatio2)
    elif ((vSyncUs <= 0.0) and (vBlankUs > 0.0)):
        vSyncUs = vBlankUs * (vRatio2 / vRatioT)

    vBase = 1.0 / vFreq
    vBase = (vPix / (vBase - vBlankUs)) * vBase
    vBase = (vBase - vPix) / vRatioT

    vTim1 = vPix  + int((vBase * vRatio1) + 1.0)
    vTim2 = vTim1 + int((vBase * vRatio2) + 1.0)
    vTim3 = vTim2 + int((vBase * vRatio3) + 1.0)

    hFreq    = (vTim3 * vFreq)

    hSyncUs  = hSync / 1000000.0
    hBlankUs = hBlank / 1000000.0

    hPix    = ((hPix + 7) / 8) * 8

    hRatioT = hRatio1 + hRatio2 + hRatio3
    if   ((hSyncUs > 0.0) and (hBlankUs > 0.0)):
        hRatio2 = (hRatio1 + hRatio3) * (hSyncUs / (hBlankUs - hSyncUs))
        hRatioT = hRatio1 + hRatio2 + hRatio3
    elif ((hSyncUs > 0.0) and (hBlankUs <= 0.0)):
        hBlankUs = hSyncUs * (hRatioT / hRatio2)
    elif ((hSyncUs <= 0.0) and (hBlankUs > 0.0)):
        hSyncUshBlankUs = hBlankUs * (hRatio2 / hRatioT)

    hBase = 1.0 / hFreq
    hBase = (hPix / (hBase - hBlankUs)) * hBase
    hBase = (hBase - hPix) / hRatioT

    hTim1 = hPix  + ((int((hBase * hRatio1)+8.0) / 8) * 8)
    hTim2 = hTim1 + ((int((hBase * hRatio2)+8.0) / 8) * 8)
    hTim3 = hTim2 + ((int((hBase * hRatio3)+8.0) / 8) * 8)

    dotClock = (hTim3 * vTim3 * vFreq) / 1000000.0

    hFreqKHz = hFreq / 1000.0

    results = {}
    results["entry"]    = '''\
# %(hPix)dx%(vPix)d @ %(vFreq)dHz, %(hFreqKHz)6.2f kHz hsync
    Mode "%(hPix)dx%(vPix)d"
        DotClock  %(dotClock)8.2f
        HTimings  %(hPix)d %(hTim1)d %(hTim2)d %(hTim3)d
        VTimings  %(vPix)d %(vTim1)d %(vTim2)d %(vTim3)d
    EndMode\
    ''' % vars()
    results["hPix"]     = hPix
    results["vPix"]     = vPix
    results["vFreq"]    = vFreq
    results["hFreq"]    = hFreq
    results["dotClock"] = dotClock
    results["hTim1"]    = hTim1
    results["hTim2"]    = hTim2
    results["hTim3"]    = hTim3
    results["vTim1"]    = vTim1
    results["vTim2"]    = vTim2
    results["vTim3"]    = vTim3

    return results

def calcModeLine(w, h, vfreq):
    vals = {}
    vals["hPix"] = w
    vals["vPix"] = h
    vals["vFreq"] = vfreq
    m = ModeLine(vals)
    return m["entry"]

def calcFromEdid(edid):
    dt = edid["detailed_timing"]
    hActive = dt["horizontal_active"]
    vActive = dt["vertical_active"]
    hBlanking = dt["horizontal_blanking"]
    vBlanking = dt["vertical_blanking"]
    pixelClock = dt["pixel_clock"]

    hTotal = hActive + hBlanking
    vTotal = vActive + vBlanking

    ret = {}

    ret["mode"] = (hActive, vActive)
    try:
        ret["vfreq"] = float(pixelClock) / (hTotal * vTotal)
        ret["hfreq"] = float(pixelClock) / (hTotal * 1000.0)
    except ZeroDivisionError:
        return

    ret["dot_clock"] = pixelClock / 1000000.0

    ret["htimings"] = (hActive, \
                       hActive + dt["hsync_offset"],\
                       hActive + dt["hsync_offset"] + dt["hsync_pulse_width"], \
                       hTotal)
    ret["vtimings"] = (vActive, \
                       vActive + dt["vsync_offset"],\
                       vActive + dt["vsync_offset"] + dt["vsync_pulse_width"], \
                       vTotal)
    flags = dt["flags"]
    ret["flags"] = []
    if flags["interlaced"] or flags["separate_sync"]:
        if flags["interlaced"]:
            ret["flags"].append("Interlace")

        if flags["hsync_positive"]:
            ret["flags"].append("+HSync")
        else:
            ret["flags"].append("-HSync")

        if flags["vsync_positive"]:
            ret["flags"].append("+VSync")
        else:
            ret["flags"].append("-VSync")

    return ret
