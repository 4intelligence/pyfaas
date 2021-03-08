import pandas as pd 
import numpy as np
import datetime as dt
from typing import Dict
import urllib3
import requests
import json
import gzip
import zlib
import base64
from unidecode import unidecode
import time

def faas_api(data_list: Dict[str, pd.DataFrame], 
date_variable: str, date_format: str, 
model_spec: dict, project_id: str, 
user_email: str, access_key: str) -> str:
    '''
    This is the core function of PyFaaS, and it takes local data and sends it to 4intelligence's
    Forecast as a Service product.

    Args:
        data_list: dictionary of pandas datataframes and their respective keys to be sent to the API
        date_variable: name of the variable to be considered as the timesteps
        date_format: format of date_variable following datetime notation 
                    (See https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior) 
        model_spec: dictionary containing arguments required by the API
        project_id: name of the project defined by the user
        user_email: email address the results will be sent to
        access_key: token provided by 4intelligence for accessing the FaaS infrastructure
    
    Returns:
        If successfully received, returns the API's return code and email address to which the results 
        will be sent. If failed, return API's return code.
    '''

    # ------ Check for email formatting

    if '@' not in user_email:
        raise ValueError(f'{user_email} is not a valid email address')

    
    

    # ------ Check dataframes inside dictionary and turn them into dictionaries themselves

    for key in data_list.keys():
        
  
        # ----- cleaning column names
        data_list[key].rename(columns={date_variable: 'data_tidy'}, inplace=True)

        if data_list[key]['data_tidy'].dtype == np.datetime64:
            data_list[key]['data_tidy'] = data_list[key]['data_tidy'].astype(str)
        else:
            try:
                data_list[key]['data_tidy'] = pd.to_datetime(data_list[key]['data_tidy'], \
                format = date_format).astype(str)
            except:
                raise ValueError(f'date_format {date_format} not compatible with data_list. See: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior')


        if key not in data_list[key].columns:
            raise KeyError(f'Variable {key} not found in the dataset')
       

        # ------ order columns to make sure data_tidy and Y are the first columns
        ordered_columns = list(data_list[key].columns)
        ordered_columns.remove('data_tidy')
        ordered_columns.remove(key)

        ordered_columns = ['data_tidy', key] + ordered_columns

        data_list[key] = data_list[key][ordered_columns]

        # ------ remove accentuation ------
        data_list[key].columns = [unidecode(x) for x in data_list[key].columns]

        # converting dataframes into dictionaries
        data_list[key] = data_list[key].fillna('NA').T.to_dict()

        for inner_key in list(data_list[key]):
            for innerer_key in list(data_list[key][inner_key]):
                if data_list[key][inner_key][innerer_key] == 'NA':
                    del data_list[key][inner_key][innerer_key]



    # ------ Convert dict to list -----------------------------
    position = 1
    
    for key in list(data_list.keys()):
        data_list[key] = [x for x in data_list[key].values()]
        data_list[f'forecast_{position}_' + key] = data_list.pop(key)
        position += 1

    
    try:
        model_spec = {
        'log': [ model_spec['log'] ],
        'seas.d': [ model_spec['seas.d']  ],
        'n_steps': [ model_spec['n_steps']  ],
        'n_windows': [ model_spec['n_windows']  ],
        'n_best': [ model_spec['n_best']  ],
        'accuracy_crit': [model_spec['accuracy_crit'] ],
        'info_crit': [model_spec['info_crit']],
        'exclusions': model_spec['exclusions'],
        'golden_variables': model_spec['golden_variables'],
        'fill_forecast': [ model_spec['fill_forecast'] ],
        'cv_summary': [ model_spec['cv_summary']] ,
        'selection_methods': {
            'lasso' : [ model_spec['selection_methods']['lasso'] ],
            'rf' : [ model_spec['selection_methods']['rf'] ],
            'corr' : [ model_spec['selection_methods']['corr'] ],
            'apply.collinear' : ["corr","rf","lasso","no_reduction"]
        }   
        }
    except KeyError as ke:
        raise KeyError(f'Missing model_spec argument: {ke.args}')
    
    # ------ removing accentuation ------
    model_spec['golden_variables'] = [unidecode(i) for i  in model_spec['golden_variables']]
    model_spec['exclusions'] = [[unidecode(i) for i in j] for j in model_spec['exclusions']]

    # ------ Unite everything into a dictionary -----------------
    body = {'data_list': data_list,  
            'model_spec': model_spec,
            'user_email': [user_email],
            'project_id': [project_id]
            }

    
    # ----- Ship it to the API ----------------------------------
    
    url = "https://scalling-models-api-pixv2bua7q-uk.a.run.app/cluster"


    zipped_body = base64.b64encode(gzip.compress(json.dumps(body).encode('utf-8'))).decode('utf-8')

    headers = {'Content-Encoding': 'gzip', 
               'Authorization': access_key}
    
    
    def send_request():
        return requests.post(url, {'body': zipped_body}, headers=headers)

    for _ in range(5):
        r = send_request()
        if r.status_code != 500:
            break
        else:
            time.sleep(1)
    
    if r.status_code == 200:
        
        print(f"HTTP 200:\nRequest successfully received!\nResults will soon be available in your Projects module")
    
    else:
        raise Exception(f'Something went wrong!\nStatus code: {r.status_code}.')
    