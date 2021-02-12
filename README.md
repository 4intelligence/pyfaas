PyFaaS - FaaS API modeling with Python
================

![Python](https://img.shields.io/badge/python-3.6|3.7|3.8-blue.svg) ![License: MPL
2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)

**Repository for running scale modeling on FaaS from Python**


Repository under license [Mozilla Public
Version 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

The script ‘run\_examples.ipynb’ has all the necessary code to run both
examples covered in the tutorial below.

It is presented one case example for modeling one target variable (Y),
using one dataset, and another one with multiple target variables (Y),
which uses a list of datasets.

## Autentication

An **access key** is required in order to sucessfully send the request.
It will be granted to each user individually.

## I) How it works

The function is supported by **Python 3** and requires the following packages:

* numpy
* pandas
* requests
* unidecode



Then the function **faas\_api** to be used can be found in the "pyfaas" folder and once downloaded, can be imported directly into a python script (.py) or a Jupyter Notebook (.ipynb) as can be seen in the example.


### Optional: Installing dependencies

To install the required packages download the *requirements.txt* file and open a terminal in your code editor, or the Linux terminal if you are using it as your OS. 

**IMPORTANT**: Make sure the terminal is in the same folder as the *requirements.txt* file.

Then, run one of the following:

* Installing with an Anaconda environment:
```bash
conda install --file requirements.txt
```

* Installing using PIP:
```bash
pip install -r requirements.txt
```

* You can also install it directly from a Jupyter Notebook, just note that the .ipynb must be in the same folder as the requirements.txt
```bash
!pip install -r requirements.txt
```
#### Reading Excel files (.xlsx)
Note that an additional package is needed for reading .xlsx files, the **xlrd** package. It can be installed with one following:

* Installing in an Anaconda environment:
```bash
conda install -c anaconda xlrd 
```

* Installing using PIP:
```bash
pip install xlrd
```

* Inside a Jupyter Notebook:
```bash
!pip install xlrd
```
The package is required only if you are reading .xlsx files or want to follow the tutorial.

### Using PyFaaS

Now let's load the function:

``` python
from pyfaas.faas import faas_api
```

There are **7 basic arguments** to feed ‘faas\_api’ function.We are
going through all of them in this example and then will call the API.

#### 1\) Data List \[‘data\_list’\]

A list of datasets to perform modeling;

Since we are dealing with time-series, the dataset *must contain a date
column* (its name is not relevant, since we will automatically detect
it).

Here lie two major conventions to follow:

1)  There must be a date column in the data frame
2)  You must name every dictionary key after the Y variable name

Variables names (column names) that begin with numeric characters will
be renamed to avoid computational issues. For example, variables “32”,
“156\_y”, “3\_pim” will be displayed as “x32”, “x156\_y” and “x3\_pim”
at the end of the process. To avoid this correction, avoid beginning
columns names with numeric characters;

Let us see two examples of data list, one with 1 Y’s and the other with
multiple Y’s <br>

##### Example 1 data\_list \[single Y\]:

``` python

import pandas as pd

# ------ Load dataset -----------------------------------
df_example = pd.read_excel("./inputs/dataset_1.xlsx")

# ------ Declare the date variable and its format --------
date_variable = 'data_tidy'
date_format = '%Y-%m-%d'

# ------ Dataframes must be passed in a dictionary
data_list = {'fs_pim': df_example}
```

<br>

##### Example 2 data\_list \[multiple Ys\]:

``` python
# ------ Load datasets -----------------------------------

df_example1 = pd.read_excel("./inputs/dataset_1.xlsx")
df_example2 = pd.read_excel("./inputs/dataset_2.xlsx")
df_example3 = pd.read_excel("./inputs/dataset_3.xlsx")


# ------ Declare the date variable and its format --------

date_variable = 'data_tidy'
date_format = '%Y-%m-%d'

# ------ Dataframes must be passed in a dictionary
data_list = {'dataset_1': df_example1,
             'dataset_2': df_example2,
             'dataset_3': df_example3}
```

<br>



#### 2\) Date Variable \[date\_variable\]

The variable that has the dates to be used by the models.
```python
# The name of the columns which contains the dates
date_variable = 'data_tidy'
```


#### 3\) Date Format \[date\_format'\]

Which is the format that the date is represented (p.e 1993-05-06 would be %Y-%m-%d)
For reference see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

```python
date_format = '%Y-%m-%d'
```


#### 4\) **Model Specifications \[‘model\_spec’\]**

Regardless of whether you are modeling one or multiple Ys, the model
spec follows the same logic. A list of desired modeling specification by
the user:

  - **n\_steps**: forecast horizon that will be used in the
    cross-validation (if 3, 3 months ahead; if 12, 12 months ahead,
    etc.);

  - **n\_windows**: how many windows the size of ‘Forecast Horizon’ will
    be evaluated during cross-validation (CV);

  - **seas.d**: if TRUE, it includes seasonal dummies in every
    estimation.

  - **log**: if TRUE apply log transformation to the data;

  - **accuracy\_crit**: which criterion to measure the accuracy of the
    forecast during the Cross-Validation (can be MPE, MAPE, WMAPE or RMSE);

  - **exclusions**: restrictions on features that should not be in the same model;

  - **golden_variables**: features that must be included in, at least, one model (separate or together).
<br>

The critical input we expect from users is the CV settings (n\_steps and
n\_windows). In this example, we set our modeling algorithm to perform a
CV, which will evaluate forecasts 1 step ahead (‘n\_steps’), 12 times
(‘n\_windows’).

In this example, we keep other specifications at their default values.
The accuracy criteria used to select the best models will be “MAPE”.
We’ll be using data with log transformation, and proper seasonal
dummies will be used in every estimation. Moreover, we avoid
multicollinearity issues in linear models and apply three distinct
methods of feature selection. In the last section of this file, we
present more advanced settings examples.

``` python
## EXAMPLE 1
model_spec = {
              'log': True,
              'seas.d': True,
              'n_steps': 3,
              'n_windows': 6,
              'n_best': 25,
              'accuracy_crit': 'MAPE',
              'info_crit': 'AIC',
              'exclusions': [],
              'golden_variables': [],
              'selection_methods': {
                  'lasso' : True,
                  'rf' : True,
                  'corr' : True,
                  'apply.collinear' : ["corr","rf","lasso","no_reduction"]
                  }      
              }
```

<br>


#### 5\) Project ID \[‘project\_id’\]

Define a project name. It accepts character and numeric inputs. Special
characters will be removed.

``` python
project_id = 'project_example'
```


#### 6\) User Email \[‘user\_mail’\]

Set the user email. We are going to use this let you know when the
modeling is over.

```python
user_email = 'user@domain.com'
```

#### 7\) Access Key \[‘access\__key’\]

The access key provided by 4intelligence

```python
access_key = "User access key"
```

#### 8\) Send job request

Everything looks nice? Great\! Now you just have to send **FaaS API**
request:

``` python
faas_api(data_list, date_variable, date_format, model_spec, project_id, user_email, access_key)
```

If everything went fine you should see the following message:


"HTTP 200:

Request successfully received!

Results will soon be available in your Projects module"



## II) Advanced Options

In this section, we change some the default values of the
**model\_spec**. *Only advanced users should edit them: make sure you
understand the implications before changing them.*

The accuracy criteria used to select the best models will be “RMSE”.
We’re not applying log transformation on data. Moreover, we also make
use of the **‘exclusions’** and **golden\_variables** options:

``` python
## EXAMPLE 2
model_spec = {
    'log': False,
    'seas.d': True,
    'n_steps': 3,
    'n_windows': 6,
    'n_best': 25,
    'accuracy_crit': 'RMSE',
    'info_crit': 'AIC',
    'exclusions': [["fs_massa_real", "fs_rend_medio"],
                  ["fs_pop_ea", "fs_pop_des", "fs_pop_ocu"]],
    'golden_variables': ["fs_pmc", "fs_ici"],
    'selection_methods': {
                          'lasso' : False,
                          'rf' : True,
                          'corr' : True,
                          'apply.collinear' : []
                         }   
    }
```

<br>

By setting **exclusions** this way, we add the restriction where the
features/variables in a group can not appear together in the same model.
Pay attention to the following lines:

``` python
'exclusions': [["fs_massa_real", "fs_rend_medio"],
              ["fs_pop_ea", "fs_pop_des", "fs_pop_ocu"]]
```

This list implies that we will never see “fs\_massa\_real” and
“fs\_rend\_medio” in the same model. The same is true for the second
restriction group: we will never estimate models that simultaneously
include “fs\_pop\_ea”, with either “fs\_pop\_des” and “fs\_pop\_ocu”,
and so on.

<br>

With the **golden\_variables** argument, we can guarantee that at least
some of best models contain one or both of the ‘golden’ ones:

``` python
'golden_variables': ["fs_pmc", "fs_ici"]
```

<br>

The **selection\_methods** determine feature selection algorithms that
will be used when it comes to big datasets (one with a large number of
explanatory features). More precisely, if the number of features in the
dataset exceeds 14, feature selection methods will reduce
dimensionality, guaranteeing the best results in a much more efficient
way. In this example, we turn off the Lasso method and work only with
Random Forests and the correlation approach.

``` python
'selection_methods': {
                      'lasso' : False,
                      'rf' : True,
                      'corr' : True,
                      'apply.collinear' : []
                      }  
```

<br>
