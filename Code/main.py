# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 09:42:28 2023

@author: jcosson

edited December 2023
by jwrage
"""
import os

import config as c
from config import PRIMAL_PATH, ADJOINT_PATH, FOLDER_NAME, n
from src import primal_solvers as sol, post_processing as post, adjoint_solvers as adsol

c.headings()
#          CHOICE OF COMPUTATION

# initialises bash program that is necessary for the usage of Openfoam solver PimpleDyMFoam
os.system('source /nfs/software-ubuntu-20.04/openfoam-2.3.1-with-openmpi-1.10.7/openfoam-2.3.1/etc/bashrc')

# sol.the_new_shooting_manager("no", 0)
# try to edit

# start primal shooting
sol.primal_shooting_stef_update(PRIMAL_PATH, "yes", "event")
# start adjoint shooting
adsol.computeAdjoint(ADJOINT_PATH, "yes", "event")

# creating logs and erases the calculated sweep files of the last sweep of primal shooting
# calculated files are used as basic data for adjoint computing
post.erase_all_files(PRIMAL_PATH, FOLDER_NAME, n)
post.erase_all_adjoint_files(ADJOINT_PATH, FOLDER_NAME, n)
