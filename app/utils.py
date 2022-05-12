import logging
import typing
import sys

import pandas as pd

from pprint import pprint


def csv_to_dict(file):
    df = pd.read_csv(file)
    return df.to_dict(orient='records')
