
# coding: utf-8

import pandas as pd
import numpy as np
import os
import shutil
import coinmarketcap
import time
from datetime import datetime
from coinmarketcap import Market
import smtplib
import glob
import matplotlib.pyplot as plt
get_ipython().magic(u'matplotlib notebook')
plt.rcParams['figure.figsize'] = (14.0, 10.0)



def send_email_alert(coin, increase):
    gmail_user = '' # your dummy gmail account here
    gmail_password = '' #your dummy gmail account password here since this method only works w/out 2fa
    sender = gmail_user
    to = '' # email to send to here 
    
    subject = 'Break out alert for ' + coin + '!'
  
    email_text =  coin + ' is breaking out! It is up ' + str(increase) + '% in 1 hour.' 

    message = 'Subject: {}\n\n{}'.format(subject, email_text)

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_user, gmail_password)
    server.sendmail(sender, to, message)
    server.close()
    print 'Email sent!'

      

def coin_killer():
    #pull data for the top 100 marketcap coins on CMC and convert to df
    coinmarketcap = Market()
    top_100_coins_df = pd.DataFrame(coinmarketcap.ticker(start=0, limit=100, convert='USD'))

    #top_100_coins_df
    
    # make pull_request column and fill with current timestamp for index later on
    top_100_coins_df['pull_request'] = pd.Timestamp.now()

    # convert these colums from strings to floats
    top_100_coins_df['24h_volume_usd'] = pd.to_numeric(top_100_coins_df['24h_volume_usd'], errors='coerce')
    top_100_coins_df['percent_change_1h'] = pd.to_numeric(top_100_coins_df['percent_change_1h'], errors='coerce')
    top_100_coins_df['percent_change_24h'] = pd.to_numeric(top_100_coins_df['percent_change_24h'], errors='coerce')
    top_100_coins_df['percent_change_7d'] = pd.to_numeric(top_100_coins_df['percent_change_7d'], errors='coerce')

    #make a newdf of the top 24 hour gainers, and store symbols in top_15_24hr_gainers_symbol_list for later
    top_15_24hr_gainers_df = top_100_coins_df.sort_values('percent_change_24h', ascending = False)
    top_15_24hr_gainers_df = top_15_24hr_gainers_df.iloc[0:15,:]
    top_15_24hr_gainers_symbol_list = top_15_24hr_gainers_df['symbol'].values.tolist()
    
    

    # make a df of top 50 coins and plot bars for'percent_change_1h','percent_change_24h'
    top_50_coins_df = pd.DataFrame(top_100_coins_df.head(50), columns=['percent_change_1h','percent_change_24h','symbol'] )
    top_50_coins_df.set_index([range(50), 'symbol'])

    top_50_coins_df.plot.bar(x=top_50_coins_df.symbol)

    plt.savefig(r'C:\crypto_day_trader\top_50_coins.jpg', bbox_inches='tight')

    
    # make a list of the top 100 coins by market cap and put the symbols in the all_coins_list
    all_coins_list = top_100_coins_df['symbol'].values.tolist()

    # send conditional email alerts
    for c in all_coins_list:
        single_coin_df = top_100_coins_df[top_100_coins_df.symbol == c]
        
        # send email if 1h change is greater than 10%
        if single_coin_df.iloc[0]['percent_change_1h'] > 10:
            #send_email_alert(c, single_coin_df.iloc[0]['percent_change_1h'] )  
            #send_email_alert_morgan(c, single_coin_df.iloc[0]['percent_change_1h'])
            print "c" + " breakout! in progress"
        
        #convert 'pull_request' to string, store it in 'pull_request_string' 
        single_coin_df['pull_request_string'] = single_coin_df['pull_request'].apply(lambda x: x.strftime('%y/%m/%d/%H:%M:%S'))
        
        #create a .csv for each coin in the all_coins_list
        single_coin_df.to_csv(os.path.join(r'C:\crypto_day_trader\PULL_REQUESTS', c + '.csv'), sep=',', index=False)

        
    # make a list of the pull reuest single coin .csvs 
    csv_folder = r'C:\crypto_day_trader\PULL_REQUESTS'
    csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

    #make a list for storing the .csvs that will get appended to  
    pull_requests_by_coin_folder = r'C:\crypto_day_trader\PULL_REQUESTS_BY_COIN'
    pull_requests_by_coin_folder_files = [f for f in os.listdir(pull_requests_by_coin_folder) if f.endswith('.csv')]
    
    
    # copy the inital pull request .csvs if the pull_requests_by_coin_folder folder is empty, because we need the header
    if len(pull_requests_by_coin_folder_files) == 0:
        for f in csv_files:
            shutil.copy2(os.path.join(csv_folder,f), os.path.join(pull_requests_by_coin_folder,f))
        print 'seed files copied to pull_requests_by_coin_folder'
    else:
        print 'seed files already in pull_requests_by_coin_folder'
        
    
        
        # append pull requests without header to the .csvs in pull_requests_by_coin_folder
        for f in csv_files:
            x = pd.read_csv(os.path.join(csv_folder,f), sep=',')

            with open(os.path.join(pull_requests_by_coin_folder,f), 'a') as f:
                x.to_csv(f, header=False,index=False)
            #print x.index


    # make a list for concating all the .csvs along axis one to be used for time series line plot 
    for_cat_list = []
    
    #update pull_requests_by_coin_folder_files list 
    pull_requests_by_coin_folder_files = [f for f in os.listdir(pull_requests_by_coin_folder) if f.endswith('.csv')]
    
    
    #prepare dfs and and them to concatted line plot of top 15 24 hour gainers
    # needs fix from losing its place when top_15_24hr_gainers_symbol_list changes
    for f in pull_requests_by_coin_folder_files:
        if f[0:-4] in top_15_24hr_gainers_symbol_list:
        
            merge_df = pd.read_csv(os.path.join(pull_requests_by_coin_folder,f))

            merge_df_slice =pd.DataFrame(merge_df, columns=['percent_change_24h','symbol','pull_request'] )
            merge_df_slice = merge_df_slice.set_index(pd.DatetimeIndex(merge_df_slice['pull_request']))
            merge_df_slice.columns = columns=["pc_24hr_" + f[0:-4] ,'symbol','pull_request']
            merge_df_slice.drop(labels=['symbol','pull_request'],axis=1,inplace=True)
            #print merge_df_slice.head(5)
            for_cat_list.append(merge_df_slice)
        else:
            pass
   
    
    
    #make time series line plot of top 15 24 hour gainers
    catted_df = pd.concat(for_cat_list,axis=1)
    print catted_df
    catted_df.to_csv(os.path.join(r'C:\crypto_day_trader', 'catted_df_test.csv'), sep=',', index=False)
    
    #make time series line plot of top 15 24 hour gainers
    catted_df.plot()
    
    
    
    plt.savefig(r'C:\crypto_day_trader\timer_test_24hr_test_.jpg', bbox_inches='tight')





for i in range(9999):
    try:
        coin_killer()
    except:
        print 'coin killer failed'
    time.sleep(900)







