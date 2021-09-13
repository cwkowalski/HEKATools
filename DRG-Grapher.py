import numpy as np
import pandas as pd
import os
from scipy import stats as scistat
from plotnine import *
from functools import reduce

path = r'C:\Users\ckowalski\Dropbox\FileTransfers\DRG'
xlspath = path + '\\' + 'finaldata.xlsx'
xls = pd.ExcelFile(xlspath, engine='openpyxl')
dataramp = pd.read_excel(xls, 'Ramps')
datac1 = pd.read_excel(xls, 'C1')
datac23 = pd.read_excel(xls, 'C2_3')
datac2 = datac23[datac23['Protocol'].str.contains('C2')].copy()
datac3 = datac23[datac23['Protocol'].str.contains('C3')].copy()

#Compensate for HEKA CC weirdness:
dataramp['Stim (pA)'] = dataramp['Stim (pA)']/5
#Add CellID for funky free-axis facets
#todo: maybe just make iterator to plot individually...
dataramp['CellID'] = dataramp['Date'] + str(dataramp['Cell'])
dataramp = dataramp.replace('RampTreat', 'RampBase').replace('RampBaseline', 'RampTreat')

bool_id_TAC         = 1
bool_id_HAC         = 1
bool_id_HACBase     = 1
bool_id_C2DecayTau  = 1
bool_id_C3DecayTau  = 1
bool_id_ramptime    = 1
bool_id_ramp        = 1
bool_id_rampfree    = 1
bool_id_Rheo        = 1

#stim_pa 1/5th!

if bool_id_TAC:
    id_TAC = (ggplot(data=datac1, mapping=aes(x='Trace', y='TACAntipeak', color='Protocol'))
                    + geom_line(size=1)
                    + facet_grid('Cell ~ Date', space='free')
                    #+ theme_light()
                    + theme(aspect_ratio=1)
                    + theme(subplots_adjust={'right': 0.75})
                    + theme(strip_text_y= element_text(angle = 0, ha = 'left')))
    fig = id_TAC.draw()
    #fig.set_size_inches(9, 108, forward=True)
    #group_stimfreq.draw(show=True)
    fig.savefig(str(path+ '\\id_TAC.png'), dpi=300)

if bool_id_HAC:
    id_HAC = (ggplot(data=datac1, mapping=aes(x='Trace', y='HACDiff', color='Protocol'))
                    + geom_line(size=1)
                    + facet_grid('Cell ~ Date', space='free')
                    #+ theme_light()
                    + theme(aspect_ratio=1)
                    + theme(subplots_adjust={'right': 0.75})
                    + theme(strip_text_y= element_text(angle = 0, ha = 'left')))
    fig = id_HAC.draw()
    #fig.set_size_inches(9, 108, forward=True)
    #group_stimfreq.draw(show=True)
    fig.savefig(str(path+ '\\id_HAC.png'), dpi=300)

if bool_id_HACBase:
    id_HACbase = (ggplot(data=datac1, mapping=aes(x='Trace', y='HACBase', color='Protocol'))
              + geom_line(size=1)
              + facet_grid('Cell ~ Date', space='free')
              # + theme_light()
              + theme(aspect_ratio=1)
              + theme(subplots_adjust={'right': 0.75})
              + theme(strip_text_y=element_text(angle=0, ha='left')))
    fig = id_HACbase.draw()
    # fig.set_size_inches(9, 108, forward=True)
    # group_stimfreq.draw(show=True)
    fig.savefig(str(path + '\\id_HACbase.png'), dpi=300)

if bool_id_C2DecayTau:
    id_C2DecayTau = (ggplot(data=datac2, mapping=aes(x='A', y='tau', color='Protocol'))
                    + geom_point(size=1)
                    + facet_grid('Date ~ Cell', space='free')
                    #+ theme_light()
                    + theme(aspect_ratio=1)
                    + theme(subplots_adjust={'right': 0.75})
                    + theme(strip_text_y= element_text(angle = 0, ha = 'left')))
    fig = id_C2DecayTau.draw()
    #fig.set_size_inches(9, 108, forward=True)
    #group_stimfreq.draw(show=True)
    fig.savefig(str(path+ '\\id_C2DecayTauByIntercept.png'), dpi=300)

if bool_id_C3DecayTau:
    id_C3DecayTau = (ggplot(data=datac3, mapping=aes(x='tau1', y='tau2', color='Protocol'))
                    + geom_point(size=1)
                    + facet_grid('Date ~ Cell', space='free')
                    #+ theme_light()
                    + theme(aspect_ratio=1)
                    + theme(subplots_adjust={'right': 0.75})
                    + theme(strip_text_y= element_text(angle = 0, ha = 'left')))
    fig = id_C3DecayTau.draw()
    #fig.set_size_inches(9, 108, forward=True)
    #group_stimfreq.draw(show=True)
    fig.savefig(str(path+ '\\id_C3DecayTauByTau.png'), dpi=300)

if bool_id_ramp:
    id_ramp = (ggplot(data=dataramp, mapping=aes(x='Stim (pA)', y='Inst. Freq. (Hz)', color='Protocol'))
                    + geom_point(size=.05)
                    + facet_grid('Cell ~ Date', space='free')
                    #+ theme_light()
                    #+ theme(aspect_ratio=2)
                    + theme(subplots_adjust={'right': 0.75})
                    + theme(strip_text_y= element_text(angle = 0, ha = 'left')))
    fig = id_ramp.draw()
    #fig.set_size_inches(9, 108, forward=True)
    #group_stimfreq.draw(show=True)
    fig.savefig(str(path+ '\\id_ramp.png'), dpi=300)

if bool_id_rampfree:
    id_rampfree = (ggplot(data=dataramp, mapping=aes(x='Stim (pA)', y='Inst. Freq. (Hz)', color='Protocol'))
                    + geom_point(size=.05)
                    + facet_wrap('CellID', scales='free')
                    #+ theme_light()
                    #+ theme(aspect_ratio=2)
                    + theme(subplots_adjust={'right': 0.75})
                    + theme(subplots_adjust={'wspace': 0.25})
                    + theme(strip_text_y= element_text(angle = 0, ha = 'left')))
    fig = id_rampfree.draw()
    #fig.set_size_inches(9, 108, forward=True)
    #group_stimfreq.draw(show=True)
    fig.savefig(str(path+ '\\id_rampfree.png'), dpi=300)

if bool_id_ramptime:
    id_ramptime = (ggplot(data=dataramp, mapping=aes(x='Event Start Time (ms)', y='Inst. Freq. (Hz)', color='Protocol'))
                    + geom_point(size=.05)
                    + facet_grid('Cell ~ Date', space='free')
                    #+ theme_light()
                    #+ theme(aspect_ratio=2)
                    + theme(subplots_adjust={'right': 0.75})
                    + theme(strip_text_y= element_text(angle = 0, ha = 'left')))
    fig = id_ramptime.draw()
    #fig.set_size_inches(9, 108, forward=True)
    #group_stimfreq.draw(show=True)
    fig.savefig(str(path+ '\\id_ramptime.png'), dpi=300)

if bool_id_Rheo:
    id_Rheo = (ggplot(data=dataramp, mapping=aes(x='Cell', y='Rheobase', color='Protocol'))
                    + geom_point(size=1)
                    + facet_grid('Date ~ ', space='free')
                    #+ theme_light()
                    + theme(aspect_ratio=1/3)
                    + theme(subplots_adjust={'right': 0.75})
                    + theme(strip_text_y= element_text(angle = 0, ha = 'left')))
    fig = id_Rheo.draw()
    #fig.set_size_inches(9, 108, forward=True)
    #group_stimfreq.draw(show=True)
    fig.savefig(str(path+ '\\id_Rheo.png'), dpi=300)