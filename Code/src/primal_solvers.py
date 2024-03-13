# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 10:27:15 2023

@author: jcosson

edited December 2023
by jwrage
"""
import os
import subprocess
import time
from concurrent import futures

from config import n, interval, sweep, FOLDER_NAME, MAX_CPU
from config import PRIMAL_PATH, ADJOINT_PATH
from src import boundary_conditions as bc, pre_processing as pre, adjoint_solvers as adsol, \
    post_processing as post


#   PRIMITIVE SHOOTING
def pimpledymfoam(basepath, folder_name, sweep_name, i):
    interval_name = interval.format(i)
    pimple_path = basepath + folder_name + "/" + sweep_name + "/" + interval_name
    os.chdir(pimple_path)  # Entering logfile path
    os.system('pimpleDyMFoam >pimple.log 2>&1')
    print("Computation of " + interval_name + " is done. Writing into pimple.log ...")
    os.chdir(basepath)  # back to main path
    return 0


def loop_pimpledymfoam(basepath, folder_name, sweep_name,
                       k):  # Version V1 : Parallel call for all intervals within one sweep
    """

    :param basepath: path of starting values
    :param folder_name: folder for results
    :param sweep_name: number of sweep
    :param k: number of sweep
    :return: results of PimPleDymFOAM solver for all sweeps
    """
    print("\nStarting shooting of " + sweep_name + "\n")
    print("Starting EXECUTOR ... \n")
    timer_pimpledymfoam = time.time()

    # ToDo: put in own function and track the time
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        # Todo reset 1 to k for only necessary calculations, (1, n + 1) for all
        for i in range(k, n + 1):
            executor.submit(pimpledymfoam, basepath, folder_name, sweep_name, i)
            print("Starting pimpleDyMFoam for interval " + str(i))
        print("\n\nAll simulations started. Waiting... \n")
    print("EXECUTOR pimpleDyMFoam terminated.\n\n")
    # own function until here

    os.chdir(basepath + folder_name + "/")
    with open("pressureDropvalues.txt", "a") as mapression:
        mapression.write("\n\nShooting of " + sweep_name + ":\n---------------------------------\n")
    mapression.close()

    # Stop Timer and write in logfile
    elapsed_time = time.time() - timer_pimpledymfoam
    # timer_pimple.append(elapsed_time)
    bc.timer_and_write(basepath, elapsed_time, "pimpleDyMFoam", sweep_name)

    post.prepare_post_processing(basepath, folder_name, sweep_name)
    post.compute_pressure_drop_foam(basepath, folder_name, sweep_name)

    if k < n:
        pre.prepare_next_sweep(basepath, k, folder_name)


#       LINEARIZATION

def linearised_pimpledymfoam(basepath, folder_name, sweep_name, i):
    """

    :param basepath: path of starting values
    :param folder_name: folder for results
    :param sweep_name: number of sweep
    :param i: number of sweep
    :return: results of linearisedPimPleDymFOAM solver for all sweeps
    """
    # Executing linearisedPimpleDyMFoam for sweep k interval i
    interval_name = interval.format(i)
    lin_pimple_path = basepath + folder_name + "/" + sweep_name + "/" + interval_name
    os.chdir(lin_pimple_path)
    with open("lin_logfile" + sweep_name + "_" + interval_name + ".txt", "w") as logfile:
        subprocess.run(['linearisedPimpleDyMFoam'], stdout=logfile, stderr=subprocess.STDOUT)
    print("Linearization of " + interval_name + " is done. Writing into lin_logfile ...")
    os.chdir(basepath)  # back to main path


def loop_linearised_pimpledymfoam(basepath, folder_name, sweep_name, k):
    # Version V1 : Parallel call for all intervals within one sweep
    lin_time = time.time()
    print("\nStarting linearization of " + sweep_name + "\n")
    print("Starting LIN EXECUTOR ... \n")

    # ToDO change to k +1 für only necessary calculations
    for i in range(k + 1, n + 1):
        pre.prepare_next_linearization(basepath, folder_name, k, i)
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        # ToDO change to k +1 für only necessary calculations
        for i in range(k + 1, n + 1):  # k.essayer 2, on ne lin pas dans 1
            executor.submit(linearised_pimpledymfoam, basepath, folder_name, sweep_name, i)
            print("Starting linearisedPimpleDyMFoam for interval " + str(i))

        print("\n\nAll linearizations started, Waiting... \n")
    os.chdir(basepath + folder_name + "/")
    # Stopping intermediate timer and writing into logfile
    elapsed_time = time.time() - lin_time
    bc.timer_and_write(basepath, elapsed_time, "linearisedPimpleDyMFoam", sweep_name)
    print("LIN EXECUTOR terminated \n\n")


#    UPDATE AND DEFECT

def compute_shooting_update(basepath, folder_name, g, i):
    sweep_name = sweep.format(g)
    interval_name = interval.format(i)

    # Calls compute shooting update from openfoam
    if not os.path.exists(basepath + folder_name + "/" + sweep_name + "/preProcessing/"):
        os.mkdir(basepath + folder_name + "/" + sweep_name + "/preProcessing/")
    os.chdir(basepath + folder_name + "/" + sweep_name + "/preProcessing/")
    with open("shooting_update_logfile" + sweep_name + "_" + interval_name + ".txt", "w") as logfile:
        subprocess.run(['computeShootingUpdate'], stdout=logfile, stderr=subprocess.STDOUT)


def compute_defect(basepath, sweep_name, k, i):
    interval_name = interval.format(i)
    previous_interval = interval.format(i - 1)
    pre.prepare_defect_computation(basepath, sweep_name, interval_name, previous_interval, i)
    os.chdir(basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect")
    with open("shooting_defect_logfile" + sweep_name + "_" + interval_name + ".txt", "w") as logfile:
        subprocess.run(['computeShootingDefect'], stdout=logfile, stderr=subprocess.STDOUT)


def loop_compute_defect(basepath, sweep_name, k):
    print("\nComputing Defect ...")
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for i in range(2, n + 1):  # 2, n+1
            executor.submit(compute_defect, basepath, sweep_name, k, i)
    os.chdir(basepath)


def compute_newton_update(basepath, sweep_name, i, k):
    interval_name = interval.format(i)
    pre.prepareNewtonUpdate(basepath, FOLDER_NAME, sweep_name, k, interval_name, i)
    os.chdir(basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name)
    with open("rel_newton_update_logfile" + sweep_name + "_" + interval_name + ".txt", "w") as logfile:
        os.chdir(basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingUpdate")
        subprocess.run(['relaxedComputeNewtonUpdate'], stdout=logfile,
                       stderr=subprocess.STDOUT)  # before : computeNewtonUpdate
    os.chdir(basepath)
    if i < n and k < n:
        post.prepare_next_newton(basepath, FOLDER_NAME, sweep_name, k, interval_name, i)


def loop_compute_newton_update(basepath, folder_name, sweep_name, k):
    """

    :param basepath: path of starting values
    :param folder_name: folder for results
    :param sweep_name: number of sweep
    :param k: number of sweep
    :return: results of Newton Updates for all sweeps and copying files for next sweep
    """
    print("\nComputing Newton Update...")
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for i in range(k + 1, n + 1):  # starting from 2
            executor.submit(compute_newton_update, basepath, sweep_name, i, k)


#   FUNCTIONS FOR MAIN EXECUTION

# THE BIG SOLVERs
def primal_shooting_stef_update(basepath, erasing, event):
    """

    :param basepath: path of starting values
    :param erasing: yes or no for erasing files that are not needed anymore
    :param event: not used
    :return: primal shooting for all sweeps
    """
    # Verify if folder_name exists, and offers to delete it if so
    bc.checking_existence(basepath, FOLDER_NAME)
    # Starting Timer for entire Process
    start_time_all = time.time()
    # Initialization for Sweep1
    bc.sweep_1_initialization(basepath, FOLDER_NAME)  # One sync version

    # STARTING MAIN LOOP
    for k in range(1, n + 1):

        # Intermediate counter start
        start_time = time.time()
        # Naming current sweep
        sweep_name = sweep.format(k)

        # Starting primitive Shooting in Sweep k over all subintervals AND creating the dirs for the next sweep
        loop_pimpledymfoam(basepath, FOLDER_NAME, sweep_name, k)  # One sync version

        # Newline for defect
        # TODO put k instead of 1 for only necessary calculations
        loop_compute_defect(basepath, sweep_name, k)

        if k == 2:
            print("Starting the adjoint ...\n")
            # event.set()

        # Starting linearization for Sweep k over all sub intervals
        # TODO in function
        loop_linearised_pimpledymfoam(basepath, FOLDER_NAME, sweep_name, k)  # One sync version

        # Starting Newton Update
        # TODO nothing to do because of small computing time
        loop_compute_newton_update(basepath, FOLDER_NAME, sweep_name, k)

        # Deleting calculated files and creating log files from sweep k-1 after Sweep k done, starting with sweep 2
        if erasing == "yes":
            if k >= 2:
                print("Deleting files...\n")
                post.erase_all_files(basepath, FOLDER_NAME, k - 1)
                print("The files for " + sweep.format(
                    k-1) + " in primal_path were successfully deleted. See exceptions above.")

        # Stopping intermediate timer and writing into logfile
        elapsed_time = time.time() - start_time
        bc.timer_and_write(basepath, elapsed_time, "subintervals", sweep_name)
    print("P and C's Method terminated. Sweep " + str(k) + " updated.")

    # Stopping timer and writing into logfile
    total_time = time.time() - start_time_all
    bc.timer_and_write(basepath, total_time, FOLDER_NAME, sweep_name)
    post.store_all_values(basepath, FOLDER_NAME)

# OPTIONS for later uses


# not used so far, program needs to be upgraded to use it
def the_new_shooting_manager(deleting, choice):
    if choice == 0:
        primal_shooting_stef_update(PRIMAL_PATH, deleting, "event")
        adsol.computeAdjoint(ADJOINT_PATH, deleting, deleting, "event")

    # PRIMAL
    if choice == 1:
        os.chdir(PRIMAL_PATH)
        primal_shooting_stef_update(PRIMAL_PATH, deleting, "event")
    # PRIMAL + NEWTON UPDATE
    if choice == 2:
        os.chdir(PRIMAL_PATH)
        primal_shooting_stef_update(PRIMAL_PATH, "no", "event")
        adsol.computeAdjoint(ADJOINT_PATH, deleting, "event")

    # ADJOINT
    if choice == 3:
        os.chdir(ADJOINT_PATH)
        adsol.computeAdjoint(ADJOINT_PATH, deleting, "event")

    # COUPLING
    if choice == 4:
        print("Warning: This option is not ready yet")
    if choice > 4:
        choice = input(
            "Enter of of the options displayed below:\n1 - Primal\n2 - Primal + Newton Update\n3 - "
            "Adjoint (Requires a full completed Primal Case with the same name)\n4 - Coupled Primal and Adjoint\n\n")
        the_new_shooting_manager(deleting, choice)
