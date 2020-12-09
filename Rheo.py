import csv
import numpy as np
import pandas as pd
import glob
import os
import xlsxwriter
import matplotlib.pyplot as plt # Deprecate
#from plotnine import ggplot, geom_point, aes, stat_smooth, facet_wrap
from plotnine import *

#### Input instructions:
## Adaptation of Rheo2, for analyzing whole groups
# Define number of experiments, list ID's for each
# Create sweep.xlsx file WITH HEADERS from Clampfit Statistics. Append for each .atf
# Create .atf event files for each file as 'mm-dd_cell_group_file-protocol', e.g. 10-21_1_ctmorph_005-Rheo5
# First two characters of group will become Genotype. Remaining characters will become 'group' e.g. treatment condition.
# Output data is written as both full dataset in long-form, as well as means for each unique Trace(row)/Genotype/Group.
# Subfolder names are expected to be the date of the experiment.


#Search path
path = r'C:\Program Files (x86)\HEKA2x903\Data\PyRheo'
group_paths = [x[0] for x in os.walk(path)]
group_paths = group_paths[1:] # Slice removes root folder PyRheo leaving only subdirectories in PyRheo
group_atfpaths = []
group_sweepfile = []
group_dict = {}

for count, i in enumerate(group_paths):
    group_atfpaths.append(glob.glob(i + '\*.atf'))
    group_sweepfile.append(i + '\\sweep.xlsx')
    group_dict[count] = os.path.basename(i)
for file in group_atfpaths:
    print(file)

summaryfilepath = path + '\\output.xlsx'
sweepfile = str(path + "\\sweep.xlsx") # Sweep filename
infilepath = glob.glob(path + '\*.atf')  # Get all .atf files in 'path'
outfilename = []
sweepfilename = []

def find_nth(hay, needle, n):
    start = hay.find(needle)
    while start >= 0 and n > 1:
        start = hay.find(needle, start+1)
        n -= 1
    return start

# Generate output filenames from input filenames, generate associated sweep file substrings
for i in infilepath:
    outfilename.append(os.path.splitext(os.path.basename(i))[0])
    sweepname = (os.path.splitext(os.path.basename(i))[0])  # Get base filename of .csv
    #print('Sweepname1:',sweepname)
    sweepname = sweepname[find_nth(sweepname, '_', 3)+1:]  # Trim filename after last_: to match Clampfit string
    # print('Sweepname2:',sweepname)
    sweepfilename.append(sweepname) # Append trimmed filename to sweepname list for enumeration in rheoplotter


# Vars
stimfactor = 5  # Stimulus per sweep, in pA
# "ID" map to group, e.g. 10-21_1_002-Rheo5 : KO_Baseline
#### Used .atf's filenames instead. For others, sweep.xlsx from parameters?
"""id_group = {'10-28_0_003-Rheo5': 'Ctrl_Baseline',
            '10-28_0_008-Rheo5': 'Ctrl_Morphine',
            '10-28_1_011-Rheo5': 'Ctrl_Recovery',
            '10-28_2_015-Rheo5': 'Ctrl_Baseline',
            '10-28_2_017-Rheo5': 'Ctrl_Morphine',
            '10-28_2_021-Rheo5': 'Ctrl_Recovery',
            '10-28_2_025-Rheo5': 'Ctrl_Morphine2',
            '10-28_3_029-Rheo5': 'Ctrl_Baseline'}"""

"""grouplist = ['Ctrl_Baseline', 'Ctrl_Morphine', 'Ctrl_Recovery', 'Ctrl_Baseline', 'Ctrl_Morphine', 'Ctrl_Recovery', 'Ctrl_Morphine2', 'Ctrl_Baseline']
for num, id in enumerate(outfilename):
    id_group[id] = grouplist[num]
print('id_group: ', id_group)"""

# Enable/disable all rows/columns or columns
# pd.set_option("display.max_rows", None, "display.max_columns", None)
pd.set_option("display.max_columns", None)



def rheoplotter(group, infile, sweepname):
    eventdata = pd.read_csv(infile, sep='	', header=2, index_col=False, encoding='cp1252')
    sweepfile = path + '\\' + group_dict[group] + '\\sweep.xlsx'
    sweepdata = pd.read_excel(sweepfile)
    #print('Sweepdata: ', '\n', sweepdata)
    #print('Sweepname: ', sweepname)
    sweepdata = sweepdata[sweepdata['FileName'].str.contains(sweepname)] # sweepname[find_nth(sweepname, '_', 2)+1:]
    #print('Sweedata: ', sweepdata)
    # outdata = eventdata.groupby(by='Trace', axis=0)

    # Pull unique spiketimes from eventdata, place into column 'Spiketime' with non-index key column 'Trace'
    outdata = eventdata.groupby(by='Trace', axis=0).apply(lambda x: x['Time of Peak (ms)'].unique()).reset_index()
    outdata.rename(columns={0:'spiketime'}, inplace=True)  # Rename column header int:0 as str:spiketime
    # print('Events resorted into sweeps: ', '\n', outdata)

    # Pull Antipeak Amplitude (pA) from event data, as 0 where no spikes detected.
    rheosubframe = pd.merge(eventdata[['Trace', 'Baseline (mV)', 'Antipeak Amp (mV)']], outdata, how='right', on=['Trace', 'Trace'])
    rheosubframe['Rheobase'] = rheosubframe['Baseline (mV)'] + rheosubframe['Antipeak Amp (mV)']
    # rheosubframe.drop('Baseline (mV)', 'Antipeak Amp (mV)')
    # rheosubframe.rename(columns={'Antipeak Amp (pA)': 'Rheobase'}, inplace=True)
    # Convert repeated values of antipeak amplitude to a list, then to min/max/mean columns, then reinsert
    # print('Rheosub before groupby: ', '\n', rheosubframe)

    rheosubframe = rheosubframe.groupby('Trace')['Rheobase'].apply(list).reset_index()
    # print('Rheosub after groupby: ', '\n', rheosubframe)
    rheosubframe['RheobaseMax'] = rheosubframe.Rheobase.apply(max)
    rheosubframe['RheobaseMin'] = rheosubframe.Rheobase.apply(min)
    rheosubframe['RheobaseMean'] = rheosubframe.Rheobase.apply(np.mean)
    # print('Rheosub after summary stats, before drop rheobase col:', '\n', rheosubframe)
    rheosubframe = rheosubframe.drop(columns='Rheobase')
    outdata = pd.merge(rheosubframe, outdata, how='right', on=['Trace', 'Trace']).fillna(0) # Pull Rheo max/min/mean
    # print('Outdata merging rheosub: ', '\n', outdata)

    # Pull sweep mean (R1S1Mean) from sweep data
    outdata = pd.merge(sweepdata[['Trace', 'R1S1Mean']], outdata, how='left', on=['Trace', 'Trace']).fillna(0)
    # outdata.rename(columns={'R1S1Mean': 'Sweep Mean'}, inplace=True)
    # print('Outdata merging sweepdata: ', '\n', outdata)
    # Generate pA stim based on protocol (5pA per step)
    # print('Outdata: ', outdata)
    outdata.insert(1, 'stim_pA', outdata.apply(lambda row: row.Trace*stimfactor, axis=1))
    #outdata['stim_pA'] = outdata.apply(lambda row: row.Trace*stimfactor, axis=1)  # 5pa/sweep. Run after joining with sweeps

    # Generate Hz from spike time lists in cells of 'spiketime', from average of interevent intervals
    sweepfreq = []
    for index, spikes in enumerate(outdata['spiketime']):
        # print('Index: ', index, 'Length: ', len(spikes), 'list: ', spikes)
        hzlist = []
        # if spikes == 0:
            # hzlist.append(0)
        try:
            if len(spikes) < 2:  # If contains less than two spikes in sweep, outdata = 0
                hzlist.append(0)
        except TypeError:  # len(0) -> typerror, for sweeps with no spikes, outdata = 0
            hzlist.append(0)
        else:
            for i, time in enumerate(spikes):
                freq = (spikes[i-1] - time)  # Get next interevent interval
            if freq != 0:
                hzlist.append(freq) # Append interevent interval to list
        try:
            sweepfreq.append(1 / (abs(sum(hzlist) / len(hzlist))/1000)) # Calculate average outdata from intervals
        except ZeroDivisionError:
            sweepfreq.append(0)
    outdata['frequency'] = sweepfreq
    outdata['spikenum'] = outdata['spiketime'].str.len()
    outdata = outdata.drop(columns='spiketime')
    # print('________________________', '\n', 'Final output: ', '\n', '________________________', '\n', outdata)
    return outdata

# Run the function and store each dataframe in dict with filenames as keys, listed in datakeys.
datadict = {}
datakeys = []
longframe = pd.DataFrame()

# Group generator to analyze cohort
for group, dir in enumerate(group_atfpaths):
    for n, inputfile in enumerate(dir):
        outfilename = os.path.splitext(os.path.basename(inputfile))[0]
        sweepfilename = outfilename[find_nth(outfilename, '_', 3)+1:]

        print('group: ', group, 'n: ', n, 'inputfile: ', inputfile)
        filedata = rheoplotter(group, inputfile, sweepfilename)
        filedata.insert(0, 'date', group_dict[group])
        filedata.insert(0, 'ID', outfilename)
        filedata.insert(0, 'cell', filedata['ID'].apply(lambda st: st[find_nth(st, '_', 1) + 1:find_nth(st, '_', 2)]))
        # filedata.insert(0,'cell', filedata['ID'].apply(lambda st: st[st.find('_')+1:st.find('_')+2]))
        filedata.insert(0, 'group', filedata['ID'].apply(lambda st: st[find_nth(st, '_', 2) + 1:find_nth(st, '_', 3)]))
        filedata.insert(0, 'genotype', filedata['group'].apply(lambda st: st[:2]))
        filedata['group'] = filedata['group'].apply(lambda x: x[2:])

        # filedata.insert(0, 'group', id_group[outfilename[n]])
        datadict[sweepfilename] = filedata
        datakeys.append(sweepfilename)
        longframe = longframe.append(filedata)

# Original to analyze single day
"""for n, inputfile in enumerate(infilepath):
    print('Inputfile: ', inputfile, 'sweepfilename[n]: ', sweepfilename[n])
    filedata = rheoplotter(inputfile, sweepfilename[n])
    filedata.insert(0, 'ID', outfilename[n])
    #filedata.insert(0,'cell', filedata['ID'].apply(lambda st: st[st.find('_')+1:st.find('_')+2]))
    filedata.insert(0, 'group', filedata['ID'].apply(lambda st: st[find_nth(st, '_', 2)+1:find_nth(st, '_', 3)]))
    filedata.insert(0, 'cell', filedata['ID'].apply(lambda st: st[find_nth(st, '_', 1):find_nth(st, '_', 2)]))
    # filedata.insert(0, 'group', id_group[outfilename[n]])
    datadict[sweepfilename[n]] = filedata
    datakeys.append(sweepfilename[n])
    longframe = longframe.append(filedata)
    # print(datadict[sweepfilename[n]], '\n')"""


# Convert summary page 0's to NaN for means/empty cells
longframenan = longframe.replace(0, np.NaN) # Convert placeholders to NaN for summary statistics
# Split group ID into genotype, treatment 'group'. Convert to category to reorder for plotnine facets.
# longframenan['genotype'] = longframenan['group'].apply(lambda x: x[:2]) # Performed above instead

longframenan['group'] = longframenan['group'].astype('category')
longframenan['group'] = longframenan['group'].cat.reorder_categories(['base', 'morph', 'recov', 'morph2', 'recov2'])
# longframemeans = longframenan.groupby(longframe['Trace'], axis=0).mean() # Take mean of all non-NaN values
# longframemeans.set_index('Trace', inplace=True)
# longframemeans.to_excel(writer, sheet_name='Summary')

# Split by genotype, then average by groups:
#lfk = longframenan[longframenan['genotype'] == 'ko']
#lfc = longframenan[longframenan['genotype'] == 'ct']
lf_means = longframenan.groupby(['Trace', 'genotype', 'group']).agg(np.mean).reset_index()
# ^ Creates multi-index for each unique Trace/genotype/group combination, averages each row (Trace) within each
# combination of genotype and group, then reset_index() converts multi-index back to columns for plotnine.


#Create cell subsets
cell_df_dict = {}
for cell in longframenan['cell'].unique():
    # Subset dataframe by Cell and save each sub to dictionary cell_dict
    cell_df = longframenan[longframenan['cell'] == cell]
    cell_df_dict[cell] = cell_df

###### Refactor to average values across each sweep in group_df.
#Create group subsets
group_df_dict = {}
for id in longframenan['group'].unique():
    group_df = longframenan[longframenan['group'] == id]
    group_df_dict[id] = group_df


#Gather rheobases
rheodict = {}
for key in datakeys:
    rheodf = datadict[key].replace(0, np.NaN)
    rheoID = str(rheodf['ID'].unique())
    rheodf = rheodf['RheobaseMax']
    rheo = str(rheodf.loc[rheodf.first_valid_index()])
    rheodict[rheoID] = [rheo]
rheo_df = pd.DataFrame.from_dict(rheodict, orient='index')
rheo_df = rheo_df.reset_index()
rheo_df.insert(0, 'cell', rheo_df['index'].apply(lambda st: st[find_nth(st, '_', 1)+1:find_nth(st, '_', 2)]))
#rheo_df.insert(0, 'cell', rheo_df.index.apply(lambda st: st[find_nth(st, '_', 1) + 1:find_nth(st, '_', 2)]))
# filedata.insert(0,'cell', filedata['ID'].apply(lambda st: st[st.find('_')+1:st.find('_')+2]))
rheo_df.insert(0, 'group', rheo_df['index'].apply(lambda st: st[find_nth(st, '_', 2) + 1:find_nth(st, '_', 3)]))
rheo_df.insert(0, 'genotype', rheo_df['group'].apply(lambda st: st[:2]))
rheo_df['group'] = rheo_df['group'].apply(lambda x: x[2:])


#Write to file
writer = pd.ExcelWriter(summaryfilepath, engine='xlsxwriter')
longframenan.to_excel(writer, 'Longform Data', index=False)
lf_means.to_excel(writer, 'Means')
rheo_df.to_excel(writer, 'Rheobase')
writer.save()
"""for key in cell_df_dict:
    cell_df_dict[key].to_excel(writer, key, index=False)
rheo_df.to_excel(writer, 'Rheobase')
writer.save()"""

#Plots
# Stimulus frequency response
"""for key in cell_df_dict:
    stimhz = (ggplot(cell_df_dict[key], aes('stim_pA', 'frequency', color='ID'))
                    + geom_point()
                    + facet_grid('ID ~ .')
                    + theme(aspect_ratio=1/3))
    fig = stimhz.draw()
    fig.savefig(str(path+ '\\cell_stimfreq_' + key + '.png'))"""

# Stimulus frequency response Groups
group_stimfreq = (ggplot(data=longframenan, mapping=aes(x='stim_pA', y='frequency', color='ID'))
                + geom_point(size=0.1)
                + facet_grid('genotype ~ group', space='free')
                + theme_light())
fig = group_stimfreq.draw()
fig.set_size_inches(15,6, forward=True)
fig.savefig(str(path+ '\\group_stimfreq_alt.png'), dpi=1000)

group_voltfreq = (ggplot(data=longframenan, mapping=aes(x='R1S1Mean', y='frequency', color='ID'))
                + geom_point(size=0.1)
                + facet_grid('genotype ~ group', space='free')
                + theme_light())
fig = group_voltfreq.draw()
fig.set_size_inches(15,6, forward=True)
fig.savefig(str(path+ '\\group_voltfreq_alt.png'), dpi=1000)

group_stimspikenum = (ggplot(data=longframenan, mapping=aes(x='stim_pA', y='spikenum', color='ID'))
                + geom_point(size=0.1)
                + facet_grid('genotype ~ group', space='free')
                + theme_light())
fig = group_stimspikenum.draw()
fig.set_size_inches(15,6, forward=True)
fig.savefig(str(path+ '\\group_stimnum_alt.png'), dpi=1000)

#Stimulus frequency response means of each unique Trace(row) x Genotype x Group combination
group_stimfreq_means = (ggplot(data=lf_means, mapping=aes(x='stim_pA', y='frequency', color='genotype'))
                + geom_point(size=0.1)
                + facet_grid('genotype ~ group', space='free')
                + theme_light())
fig = group_stimfreq_means.draw()
fig.set_size_inches(15,6, forward=True)
fig.savefig(str(path+ '\\group_stimfreq_means_alt.png'), dpi=1000)

"""for key in group_df_dict:
    stimhz = (ggplot(group_df_dict[key], aes('stim_pA', 'frequency', color='cell'))
                    + geom_point()
                    + facet_grid('group ~ .')
                    + theme(aspect_ratio=1/3))
    fig = stimhz.draw()
    fig.savefig(str(path+ '\\group_stimfreq_' + key + '.png'))"""

# Membrane potential frequency response
"""for key in cell_df_dict:
    sweepfreq = (ggplot(cell_df_dict[key], aes('R1S1Mean', 'frequency', color='ID'))
                    + geom_point()
                    + facet_grid('ID ~ .')
                    + theme(aspect_ratio=1/3))
    fig = sweepfreq.draw()
    fig.savefig(str(path+ '\\cell_sweepfreq_' + key + '.png'))
# Stimulus spike# response
for key in cell_df_dict:
    sweepfreq = (ggplot(cell_df_dict[key], aes('stim_pA', 'spikenum', color='ID'))
                    + geom_point()
                    + facet_grid('ID ~ .')
                    + theme(aspect_ratio=1/3))
    fig = sweepfreq.draw()
    fig.savefig(str(path+ '\\cell_stimnum_' + key + '.png'))"""

