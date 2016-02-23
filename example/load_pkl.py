import os
import matplotlib.pyplot as plt
import pickle as pl
import numpy as np
"""
This script demonstrates how a pickled plot file can be loaded from disk and displayed.
"""

# Load figure from disk and display
fig_handle = pl.load(open('example.pkl','rb'))
plt.show()
