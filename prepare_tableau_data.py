#!/opt/miniconda3/bin/python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from shutil import get_terminal_size
pd.set_option('display.width', get_terminal_size()[0]) 
pd.set_option('display.max_columns', None)

df = pd.read_csv('WEEKLY_ORDERS.csv');

df['DATE'] = pd.to_datetime(df[['YEAR', 'MONTH', 'DAY']])
df['ORDERS_LATE_PERCENTAGE'] = df['ORDERS_LATE_PERCENTAGE'].str.rstrip('%').astype(float)
df['CITY'] = df['CITY'].str.title() # Clean City Names (ATHENS -> Athens)
df = df.drop(columns=['YEAR', 'MONTH', 'DAY']) # Final Cleanup: Drop split date columns

font = 10

import seaborn as sns
cmap = plt.cm.rainbow

cities = df['CITY'].unique()

#---------------------- TIME SERIES ----------------------------#
def TS_plot(date,para,ylabel,name):
    plt.rcParams.update({'font.size': font})
    plt.figure(figsize = (5,3)) # FOR POWER POINT
    ax = plt.gca();
    plt.setp(ax.spines.values(), linewidth=2)
    ax.tick_params(direction='in', pad = 7,length=6, width=1.5,right=True,top=True)
    sns.lineplot(data=df, x=date, y=para, hue='City', linewidth=2.5)
    plt.xlabel(date); plt.ylabel(ylabel)
    ax.legend(fontsize = 0.8*font, loc = 'upper left')
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    out = 'TS_%s.png' %(name); plt.savefig(out); print("Plot written to", out)
    plt.show()

# MIGHT BE SEEING A WEEKLY TREND
df['DAY'] = df['DATE'].dt.day_name()

# Define the correct calendar order
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
df['DAY'] = pd.Categorical(df['DAY'], categories=day_order, ordered=True)
unique_weeks = sorted(df['DATE'].dt.isocalendar().week.unique())
week_mapping = {raw_wk: f"Week {i+1}" for i, raw_wk in enumerate(unique_weeks)}
df['WEEK_LABEL'] = df['DATE'].dt.isocalendar().week.map(week_mapping)

geo_coords = {
    'Athens': {'lat': 37.9838, 'lon': 23.7275, 'pop': 3100000},
    'Thessaloniki': {'lat': 40.6401, 'lon': 22.9444, 'pop': 800000},
    'Patra': {'lat': 38.2466, 'lon': 21.7346, 'pop': 170000},
    'Piraeus': {'lat': 37.9430, 'lon': 23.6470, 'pop': 450000},
    'Heraklion': {'lat': 35.3387, 'lon': 25.1442, 'pop': 180000},
    'Larissa': {'lat': 39.6390, 'lon': 22.4191, 'pop': 150000},
    'Kalamaria': {'lat': 40.5812, 'lon': 22.9520, 'pop': 90000},
    'Chania': {'lat': 35.5138, 'lon': 24.0180, 'pop': 110000}
}
df['Population'] = df['CITY'].map(lambda x: geo_coords.get(x, {}).get('pop', np.nan))
df['LAT'] = df['CITY'].map(lambda x: geo_coords.get(x, {}).get('lat', np.nan))
df['LON'] = df['CITY'].map(lambda x: geo_coords.get(x, {}).get('lon', np.nan))

df['Orders count per 1000 population'] = 1000*df['ORDERS_COUNT']/df['Population']
df['Late orders count'] = df['ORDERS_COUNT']*df['ORDERS_LATE_PERCENTAGE']/100
df['Late orders count per 1000 population'] = 1000*df['Late orders count']/df['Population']

#--------- LET'S THINK ABOUT TOTAL HOURS DELAYED --------#
df['Total delivery time (hours)'] = df['ORDERS_COUNT']*df['AVG_DELIVERY_TIME_MINUTES']/60

## FROM THE 'Percentage of orders late','Average delivery time (minutes)'
## CORRELATION IT LOOKS OVER 30 MINUTES DELIVERY IS LATE
print('-'*50)
print('Minimum average delivery time is %1.2f minutes' %(min(df['AVG_DELIVERY_TIME_MINUTES']))) # 31.4  SO ON AVERAGE ALL LATE? 
df['Hours late'] = df['Late orders count']*(df['AVG_DELIVERY_TIME_MINUTES']-30)/60
print('Assuming > 30 mins late, total late =  %1.3e hours' %(sum(df['Hours late'])))
print('-'*50)
#------------------------------------------------------# 

rename_dict = { # LOWER CASE AND NO SQUARE BRACKETS FOR TABLEAU
    'DATE':'Date',
    'DAY': 'Day',
    'WEEK_LABEL': 'Week Label',
    'CITY': 'City',
    'LAT': 'Latitude',
    'LON': 'Longitude',
    'ORDERS_COUNT': 'Orders Count',
    'AVG_DELIVERY_TIME_MINUTES': 'Average delivery time (minutes)',
    'ORDERS_LATE_PERCENTAGE':'Percentage of late orders'
}

columns_to_keep = list(rename_dict.keys())
#df = df[columns_to_keep].rename(columns=rename_dict)
df = df.rename(columns=rename_dict)
#print(df)
df.to_csv('tableau_delivery_dashboard.csv', index = False)

#print('For Select Analysis Metric', df.columns)

#TS_plot('Date','Orders Count','Orders count','Orders_Count')
#TS_plot('Date','Average delivery time (minutes)','Ave delivery time [mins]','Ave_delivery_time')
#TS_plot('Date','Percentage of orders late','Orders late [%]','Orders_late')
#TS_plot('Date','Late orders count','Late orders count','Late_orders_count')
#TS_plot('Date','Late orders count per 1000 population','Late orders per 1000 pop','Late_per_1000')


#TS_plot('Day','Orders Count','Orders count','TS-Orders_Count_day')
TS_plot('Day','Percentage of late orders','Orders late [%]','Orders_late_day')


#---------------------- HISTOGRAMS  ----------------------------#
#print(len(cities))

cities = df['City'].unique()
colors = sns.color_palette("muted", len(cities)) # Or use your 'palette' list

city_colors = dict(zip(cities, colors))
city_colors['Average (All Cities)'] = 'silver'

def bars(city,para,ylabel,name):
    plt.rcParams.update({'font.size': font})
    plt.figure(figsize=(5, 3))
    ax = plt.gca()
    plt.setp(ax.spines.values(), linewidth=2)
    ax.tick_params(direction='in', pad = 7,length=6, width=1.5,right=True,top=True)

    if city == 'Average (All Cities)':
        plot_data = df.groupby('DAY', observed=True)[para].mean().reset_index()
        current_color = city_colors['Average (All Cities)']
    else:
        plot_data = df[df['City'] == city]
        current_color = city_colors[city]
    
    sns.barplot(data=plot_data, x='Day', y=para, color = current_color,label = "%s" %(city),
                ec='black',width=1.0,lw = 2,errorbar=None)

    #Create the truncated names (Mon, Tue, etc.)
    ticks = range(len(day_order))
    labels = [str(day)[:3] for day in day_order]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    
    plt.xlabel('Day of the Week')
    plt.ylabel(ylabel)
    ax.legend(fontsize = 0.8*font, loc = 'upper left')
    plt.tight_layout()
    out = 'BAR_%s-%s.png' %(name,city); plt.savefig(out); print("Plot written to", out)
    plt.show()

#bars('Athens','Orders Count','Orders count','Orders_Count')
#bars('Athens','Percentage of late orders','Orders late [%]','Orders_late_day')
#bars('Athens','Percentage of late orders','Orders late [%]','Orders_late_day')
#bars('Heraklion','Percentage of late orders','Orders late [%]','Orders_late_day')


#---------------------- CORRELATIONS ----------------------------#
from scipy.stats.stats import pearsonr
from scipy.stats import norm

font = 14
def sca_plot(para1,para2,hue,name,show):
    plt.rcParams.update({'font.size': font})
    plt.figure(figsize=(7, 5))
    ax = plt.gca()
    plt.setp(ax.spines.values(), linewidth=2)
    ax.tick_params(direction='in', pad = 7,length=6, width=1.5,right=True,top=True)
    sns.scatterplot(x=para1,y=para2, data=df, hue = hue)# , palette = hue_colors)
    r,p_value = pearsonr(df[para1], df[para2])
    Z = norm.ppf(1-p_value,loc=0,scale=1)
    print('p_value = %1.3e, Z = %1.3f' %(p_value,Z))
    M,C = np.polyfit(df[para1], df[para2],1); #print(M,C)
    if show == True:
        xplot = np.linspace(min(df[para1]),max(df[para1]),100);
        yplot = M*xplot + C
        ax.plot(xplot,yplot, 'r', ls = 'dashed', label = 'y = %1.3fx + %1.3f' %(M,C))
    plt.xlabel(para1); plt.ylabel(para2)
    plt.legend(loc="upper left", fontsize = 0.8*font)
    plt.tight_layout()
    out = 'Corr_%s_show=%s.png' %(name,show); plt.savefig(out); print("Plot written to", out)
    plt.show()
#sca_plot('Percentage of late orders','Average delivery time (minutes)','City','late_AVT',True) # looks like >~30 mins is late (0%)
#sca_plot('Percentage of late orders','Average delivery time (minutes)','City','late_AVT',False) 

