import streamlit as st
import pandas as pd
import requests
import numpy as np

def display_API_calls(urls):
    st.write('#### UN Comtrade API Calls:')
    for u in urls: st.write(u)

def setup_request_A(token):
    """
    The UN Comtrade API is finicky about the max number of a parameters for a given call. So, if the class is too large, it is split into several smaller calls.
    """

    # Join reporter, partner, and commodity codes with the url recognized 'space' character ('%2C')
    reporter_codes = '%2C'.join(token['reporter_codes'])
    parter_codes = '%2C'.join(token['parter_codes'])
    commodity_codes = '%2C'.join(token['commodity_codes'])

    # Convert year selections into strings and join sets of five years together
    # Five years is the max number the API will accept, otherwise it must be split into multiple requests
    years_ = [str(i) for i in range(token['years'][0], token['years'][1])]
    years = []
    for i in range(1+len(years_)//5):
        years.append('%2C'.join(years_[i*5 : (i+1)*5]))

    # Create list of calls for the API
    urls = []
    for yr in years:
        url = f"""https://comtrade.un.org/api/get?max=10000&type=C&freq=A&px=HS&ps={yr}&r={reporter_codes}&p={parter_codes}&rg=all&cc={commodity_codes}"""
        urls.append(url)
    return urls

def make_batch_request(urls):
    df = pd.DataFrame()
    for url in urls:
        df_ = run_single_request(url)
        df = pd.concat([df,df_])
    df = calculate_net_exports(df)
    return df

def run_single_request(url):
    """
    Preforms a single request to the UN Comtrade API and returns the data if the request was successful.
    If the status_code is not 200, then an empty dataframe is returned. However, there can be issues
    even with a 200 code, in such case we print out the validation status for more information.
    """
    req = requests.get(url)
    if req.status_code == 200:
        dat = req.json();
        data = dat["dataset"]
        if data:
            df = pd.DataFrame(data[1:], columns = data[0]);
            df = df[['pfCode','yr','rgDesc','rtCode','rtTitle','ptCode','ptTitle','cmdCode','cmdDescE','TradeValue']]
            return df
        else:
            print(dat['validation']['status']['name'])
    return pd.DataFrame()



def calculate_net_exports(df):
    df = df.loc[(df.rgDesc == 'Export') | (df.rgDesc == 'Import')]
    df_ = df.copy(deep=True)
    for index, row in df_.iterrows():
        net_exports = np.nan
        counterpart = df_.loc[(df_.yr == row.yr) &
                             (df_.rgDesc != row.rgDesc) &
                             (df_.rtCode == row.rtCode) &
                             (df_.ptCode == row.ptCode) &
                             (df_.cmdCode == row.cmdCode)]

        if len(counterpart) == 1 and row.rgDesc == 'Export':
            net_exports = row.TradeValue - counterpart.iloc[0].TradeValue
            new_row = row.to_dict()
            new_row['rgDesc'] = 'Net Export'
            new_row['TradeValue'] = net_exports
            df = df.append(new_row, ignore_index = True)
    return df.reset_index()

def create_commodity_token(data, token, graphed_countries):
    coded_countries = data['countries']
    dat = coded_countries[coded_countries['country'].isin(graphed_countries[0:5])]
    reporter_codes = dat.code.values

    return {'reporter_codes' : reporter_codes,
            'parter_codes' : token['parter_codes'],
            'direction' : token['direction'],
            'years' : token['years'],
            'commodity_codes' : 'AG2'}


def setup_request_B(token_B):
    reporter_codes = '%2C'.join(token_B['reporter_codes'])
    parter_codes = '%2C'.join(token_B['parter_codes'])
    direction = token_B['direction']
    commodity_codes = 'AG2'
    yr = token_B['years'][1]
    df = pd.DataFrame()
    urls = []
    url = f"""https://comtrade.un.org/api/get?max=10000&type=C&freq=A&px=HS&ps={yr}&r={reporter_codes}&p={parter_codes}&rg=all&cc={commodity_codes}"""
    urls.append(url)
    return urls
