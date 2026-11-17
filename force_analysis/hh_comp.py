'''Compares hand hardness with force from each instrument'''

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
from sklearn.linear_model import LinearRegression, HuberRegressor

project_dir = Path(__file__).resolve().parent.parent
cache_dir = project_dir / 'data' / 'cache'

