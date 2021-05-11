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



def _get_url(extension:str) -> str:
        '''
        Defines the endpoint for the data to be sent

        Args:
            extension: Wheter to call the validation of modeling API

        Returns:
            An url in the for of a string
        '''
        return ("https://scalling-models-api-pixv2bua7q-uk.a.run.app/" + extension)



def _build_call(data_list: Dict[str, pd.DataFrame], 
date_variable: str, date_format: str, 
model_spec: dict, project_id: str, user_email: str, 
access_key: str, skip_validation: bool, extension:str) -> str:

    '''
    This is the core function of PyFaaS, and it takes local data and sends it to 4intelligence's
    Forecast as a Service product for validation and modelling.

    Args:
        data_list: dictionary of pandas datataframes and their respective keys to be sent to the API
        date_variable: name of the variable to be considered as the timesteps
        date_format: format of date_variable following datetime notation 
                    (See https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior) 
        model_spec: dictionary containing arguments required by the API
        project_id: name of the project defined by the user
        user_email: email address the results will be sent to
        access_key: token provided by 4intelligence for accessing the FaaS infrastructure
        skip_validation: if the validation step should be bypassed
        extension: Wheter to call the validation of modeling API
    
    Returns:
        A response from the called API
    '''

    # ------ Check for email formatting

    if '@' not in user_email:
        raise ValueError(f'{user_email} is not a valid email address')


    # ------ Check dataframes inside dictionary and turn them into dictionaries themselves

    for key in data_list.keys():
        
        # ----- cleaning column names
        data_list[key][date_variable] = data_list[key][date_variable].astype(str)
        

       
        if key not in data_list[key].columns:
            raise KeyError(f'Variable {key} not found in the dataset')

    
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
        data_list[f'forecast_{position}_' + unidecode(key)] = data_list.pop(key)
        position += 1

    # ------ removing accentuation ------
    try:
        model_spec['golden_variables'] = [unidecode(i) for i  in model_spec['golden_variables']]
        model_spec['exclusions'] = [[unidecode(i) for i in j] for j in model_spec['exclusions']]
    except:
        pass

    # ----- Change model_spec to be R compatible
    for key in model_spec.keys():
        if key == 'selection_methods':
            for method in model_spec[key].keys():
                if method != 'apply.collinear':
                    model_spec[key][method] = [model_spec[key][method]]
        elif key not in ['exclusions', 'golden_variables']:
                model_spec[key] = [model_spec[key]]
    
    # ------ Unite everything into a dictionary -----------------
    body = {'data_list': data_list,  
            'model_spec': model_spec,
            'user_email': [user_email],
            'project_id': [project_id],
            'date_variable': [date_variable],
            'date_format': [date_format]
            }
    
    # ----- Get the designated url ----------------------------------
    
    url = _get_url(extension) 

    zipped_body = base64.b64encode(gzip.compress(json.dumps(body).encode('utf-8'))).decode('utf-8')

    headers = {'Content-Encoding': 'gzip', 
               'Authorization': access_key}
    
    
    def send_request(extension):
        if extension == 'validate':

            return requests.post(url, {'body': zipped_body}, headers=headers, timeout=1200) 
        else:
                
                return requests.post(url, {'body': zipped_body, 'skip_validation': skip_validation}, headers=headers, timeout=1200) 

    for _ in range(5):
        r = send_request(extension)
        if r.status_code != 500:
            break
        else:
            time.sleep(1)
    
    
    return r



def validate_request(data_list: Dict[str, pd.DataFrame], 
date_variable: str, date_format: str, 
model_spec: dict, project_id: str, 
user_email: str, access_key: str, skip_validation: bool = False):
    '''

    This function directs the _build_call function to the validation API

     Args:
        data_list: dictionary of pandas datataframes and their respective keys to be sent to the API
        date_variable: name of the variable to be considered as the timesteps
        date_format: format of date_variable following datetime notation 
                    (See https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior) 
        model_spec: dictionary containing arguments required by the API
        project_id: name of the project defined by the user
        user_email: email address the results will be sent to
        access_key: token provided by 4intelligence for accessing the FaaS infrastructure
        skip_validation: if the validation step should be bypassed
    
    Returns:
        If successfully received, returns the API's return code and email address to which the results 
        will be sent. If failed, return API's return code.

    '''


    req = _build_call(data_list, date_variable, date_format, model_spec, project_id, 
    user_email, access_key, skip_validation, 'validate')
    api_response = json.loads(req.text)

    if req.status_code in [200, 201, 202]:
        print(f"Request successfully received and validated!\nNow you can call the faas_api function to run your model.\n{json.dumps(api_response, indent=2)}")
    
    else:
        raise Exception(f'Something went wrong!\nStatus code: {req.status_code}.\n{json.dumps(api_response, indent=2)}')



def faas_api(data_list: Dict[str, pd.DataFrame], 
date_variable: str, date_format: str, 
model_spec: dict, project_id: str, 
user_email: str, access_key: str, skip_validation: bool = False) -> str:
    '''

    This function directs the _build_call function to the modeling API

     Args:
        data_list: dictionary of pandas datataframes and their respective keys to be sent to the API
        date_variable: name of the variable to be considered as the timesteps
        date_format: format of date_variable following datetime notation 
                    (See https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior) 
        model_spec: dictionary containing arguments required by the API
        project_id: name of the project defined by the user
        user_email: email address the results will be sent to
        access_key: token provided by 4intelligence for accessing the FaaS infrastructure
        skip_validation: if the validation step should be bypassed
    
    Returns:
        If successfully received, returns the API's return code and email address to which the results 
        will be sent. If failed, return API's return code.
        
    '''
    req = _build_call(data_list, date_variable, date_format, model_spec, project_id, 
    user_email, access_key, skip_validation, 'cluster')
    api_responde = json.loads(req.text)
    if req.status_code in [200, 201, 202]:

        print(f"HTTP: {req.status_code}: Request successfully received!\nResults will soon be available in your Projects module")
        
        if api_response['status'] == 'Warnings':
            print(api_response['info']['warning_list'])    

    else:
        raise Exception(f'Something went wrong!\nStatus code: {req.status_code}.\n{json.dumps(api_response, indent=2)}')
    
