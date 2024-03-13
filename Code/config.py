# -*- coding: utf-8 -*-
"""
Created on Tue May  2 12:10:07 2023

@author: Julien

edited December 2023
by jwrage
"""
from sys import argv

# CONFIG FILE #
# Here, you can adapt the different paths to your structure.

# PRIMAL PATHS

# path for the results the primal computation
PRIMAL_PATH: str = '/nfs/servers/fourier/temp-1/wrage/primal/'
#PRIMAL_PATH: str = '/nfs/servers/fourier/temp-0/wrage/calcs/moderate_deformed/primal/init/'
# path for the results of the adjoint computation
ADJOINT_PATH: str = '/nfs/servers/fourier/temp-1/wrage/adjoint/'
#ADJOINT_PATH: str = '/nfs/servers/fourier/temp-0/wrage/calcs/moderate_deformed/adjoint/adjoint_newton/'

# CALCS PATHS
CALCS_UNDEFORMED_PATH: str = '/nfs/servers/fourier/temp-0/wrage/calcs/undeformed_turbulent/'
CALCS_PATH: str = '/nfs/servers/fourier/temp-0/wrage/calcs/'
# REFERENCE PATHS
REF_CASES_PATH: str = '/nfs/servers/fourier/temp-0/wrage/calcs/reference_cases/'
POST_PROCESSING_PATH: str = '/nfs/servers/fourier/temp-0/wrage/calcs/post_processing/'
REF_MOD_DEF_PATH: str = '/nfs/servers/fourier/temp-0/wrage/calcs/reference_cases/moderate_deformed_SDuct/'
# MY PROJECTS PATHS
PROJECT_PATH: str = '/nfs/servers/fourier/temp-0/wrage/sources/python_3rdParty/master_project/'
# CHOOSE YOUR BASE WORKING PATH
# basepath="/home/julien/workspace/master_project/"

# VARIABLES
# After testing is done, please uncomment the following
# n=int(input("Set the number of shooting intervals: "));
# theta=input("Define the starting time (example: 0.4): ");
try:
    amount = int(argv[2])
except IndexError:
    amount = 1
except ValueError:
    print("ERROR: Argument 2 is not a number. Amount of Sweeps needs to be a number. Exiting the program.")
    exit()
n: int = amount  # Amount of sweeps / shooting intervals
print('n ist ' + str(n))
# Folder Name can either be defined in config file or via argv
try:
    fol_name = str(n) + str(argv[1])
except IndexError:
    fol_name: str = str(n) + '_test_program_1'

FOLDER_NAME = fol_name
theta: float = 0.4  # Starting time in seconds
T: float = 0.1  # Length of one period
a: int = n  # Amount of sweeps in the first loop
deltaT: float = T / n
t: float = 0.001  # Sampling size for OpenFoam Computations
interval = 'interval{}'
sweep = 'sweep{}'
try:
    max_cpu = int(argv[3])
except IndexError:
    max_cpu = 1
except ValueError:
    print("ERROR: Argument 2 is not a number. Maximum of CPUs needs to be a number. Exiting the program.")
    exit()
MAX_CPU: int = max_cpu  # Gives the maximum amount of parallely working CPUs


# HEADINGS #
def headings():
    print('╔═════════════════════════════════════════════════════════════════╗')
    print("║                     .?77777777777777$.                          ║   \n"
          "║                   777..777777777777$+                           ║\n"
          "║                  .77    7777777777$$$                           ║\n"
          "║                  .777 .7777777777$$$$                           ║\n"
          "║                  .7777777777777$$$$$$                           ║\n"
          "║                  ..........:77$$$$$$$                           ║\n"
          "║             .77777777777777777$$$$$$$$$.=======.                ║\n"
          "║             777777777777777777$$$$$$$$$$.========               ║\n"
          "║             7777777777777777$$$$$$$$$$$$$.=========             ║\n"
          "║             77777777777777$$$$$$$$$$$$$$$.=========             ║\n"
          "║             777777777777$$$$$$$$$$$$$$$$ :========+.            ║\n"
          "║             77777777777$$$$$$$$$$$$$$+..=========++~            ║\n"
          "║             777777777$$..~=====================+++++            ║\n"
          "║             77777777$~.~~~~=~=================+++++.            ║\n"
          "║             777777$$$.~~~===================++++++.             ║\n"
          "║             77777$$$$.~~==================++++++++:             ║\n"
          "║             7$$$$$$$.==================++++++++++.              ║\n"
          "║             .,$$$$$$.================++++++++++~.               ║\n"
          "║                  .=========~.........                           ║\n"
          "║                  .=============++++++                           ║\n"
          "║                  .===========+++..+++                           ║\n"
          "║                  .==========+++.  .++                           ║\n"
          "║                   ,=======++++++,,++,                           ║\n"
          "║                   ..=====+++++++++=.                            ║\n"
          "║                              ..~+=...                           ║    ")
    print('║               Launching Python Shooting Manager!                ║')
    print('║       This program requires a working version of OpenFOAM       ║')
    print('╚═════════════════════════════════════════════════════════════════╝')
