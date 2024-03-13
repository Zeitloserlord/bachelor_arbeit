# -*- coding: utf-8 -*-
"""
Created on Tue May 30 17:12:18 2023

@author: jcosson

edited December 2023
by jwrage
"""
import os
import subprocess
import time
from concurrent import futures

from config import ADJOINT_PATH
from config import n, interval, sweep, FOLDER_NAME, MAX_CPU
from src import boundary_conditions as bc, pre_processing as pre, post_processing as post


#   ADJOINT SHOOTING
def adjoint_pimpledymfoam(folder_name, sweep_name, i):
    interval_name: str = interval.format(i)
    pimple_path: str = ADJOINT_PATH + folder_name + "/" + sweep_name + "/" + interval_name
    # Change to logfile path
    os.chdir(pimple_path)
    os.system('enhancedAdjointPimpleDyMFoam >adjoint_pimple.log 2>&1')
    print("Adjoint computation of " + interval_name + " is done. Writing into pimple.log ...")
    # return to main path
    os.chdir(ADJOINT_PATH)
    return 0


# Version V1 : Parallel call for all intervals within one sweep
def loop_adjoint_pimpledymfoam(folder_name, sweep_name, k):
    """

        :param folder_name: folder for results
        :param sweep_name: number of sweep
        :param k: number of sweep
        :return: results of enhancedAdjointPimPleDymFOAM solver for all sweeps
        """
    start_time = time.time()
    print("\nStarting shooting of " + sweep_name + "\n")
    print("Starting ADJ EXECUTOR ... \n")
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for i in range(n - k + 1, 0, -1):  # (n, k-1, -1)
            executor.submit(adjoint_pimpledymfoam, folder_name, sweep_name, i)
            print("Starting enhancedAdjointPimpleDyMFoam for interval " + str(i))
        print("\n\nAll simulations started. Waiting... \n")
    print("ADJ EXECUTOR adjointPimpleDyMFoam terminated.\n\n")
    elapsed_time = time.time() - start_time
    os.chdir(ADJOINT_PATH)
    bc.timer_and_write(ADJOINT_PATH, elapsed_time, "enhancedAdjointPimpleDyMFoam", sweep_name)
    post.prepare_adjoint_post_processing(ADJOINT_PATH, folder_name, sweep_name)
    post.compute_adjoint_pressure_drop_foam(ADJOINT_PATH, folder_name, sweep_name)


#       LINEARIZATION

def adjoint_linearised_pimpledymfoam(basepath, folder_name, sweep_name, i):
    # Executing linearisedPimpleDyMFoam for sweep k interval i
    interval_name = interval.format(i)
    lin_pimple_path = basepath + folder_name + "/" + sweep_name + "/" + interval_name
    os.chdir(lin_pimple_path)
    with open("adjoint_lin_logfile" + sweep_name + "_" + interval_name + ".txt", "w") as logfile:
        # TODO: try the function with underline
        subprocess.run(['linearisedAdjointPimpleDyMFoam'], stdout=logfile, stderr=subprocess.STDOUT)
        # subprocess.run(['linearisedPimpleDyMFoam'])
    print("Adjoint linearization of " + interval_name + " is done. Writing into lin_logfile ...")
    os.chdir(basepath)  # back to main path


# A TESTER SANS PARALEL
def loop_linearised_adjoint_pimpledymfoam(folder_name, sweep_name, k):
    """

        :param folder_name: folder for results
        :param sweep_name: number of sweep
        :param k: number of sweep
        :return: results of adjointLinearisedPimPleDymFOAM solver for all sweeps
        """
    print("\nStarting adjoint linearization of " + sweep_name + "\n")
    print("Starting LIN ADJ EXECUTOR ... \n")
    pre.prepare_next_adjoint_linearization(ADJOINT_PATH, folder_name, k)
    start_time = time.time()
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        # Todo put in (2, n - k + 1) for necessary calculations only, (2, n) for all calcs
        for i in range(2, n - k + 1):  # k.essayer 2, on ne lin pas dans 1, avant 1, n+1
            executor.submit(adjoint_linearised_pimpledymfoam, ADJOINT_PATH, folder_name, sweep_name, i)
            # adjointLinearisedPimpleDyMFoam(adjoint_path, folder_name, sweep_name, i)
            print("Starting adjointLinearisedPimpleDyMFoam for interval " + str(i))
        print("\n\nAll Adjoint linearizations started, Waiting... \n")
    print("LIN ADJ EXECUTOR terminated \n\n")
    elapsed_time = time.time() - start_time
    bc.timer_and_write(ADJOINT_PATH, elapsed_time, "adjointLinearisedPimpleDyMFoam", sweep_name)


# UPDATE AND DEFECT

def compute_adjoint_defect(basepath, sweep_name, k):
    print("\nComputing Adjoint Defect ...")
    for i in range(n, 1, -1):  # avant n-1
        interval_name = interval.format(i - 1)
        previous_interval = interval.format(i)
        pre.prepare_adjoint_defect_computation(ADJOINT_PATH, sweep_name, interval_name, previous_interval, i)
        os.chdir(ADJOINT_PATH + FOLDER_NAME + "/" + sweep_name + "/" + interval_name)
        with open("adjoint_shooting_defect_logfile" + sweep_name + "_" + interval_name + ".txt", "w") as logfile:
            os.chdir(ADJOINT_PATH + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/")
            subprocess.run(['computeAdjointShootingDefect'], stdout=logfile, stderr=subprocess.STDOUT)
    os.chdir(basepath)


def computeAdjointNewtonUpdate(basepath, sweep_name, i, k):
    interval_name = interval.format(i)
    pre.prepare_adjoint_newton_update(basepath, FOLDER_NAME, sweep_name, k, interval_name, i)
    os.chdir(basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name)
    with open("rel_adj_newton_update_logfile" + sweep_name + "_" + interval_name + ".txt", "w") as logfile:
        os.chdir(basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingUpdate")
        subprocess.run(['adjointRelaxedComputeNewtonUpdate'], stdout=logfile,
                       stderr=subprocess.STDOUT)  # before : computeNewtonUpdate
    os.chdir(basepath)


def loop_computeAdjointNewtonUpdate(basepath, folder_name, sweep_name, k):
    """

        :param basepath: path of starting values
        :param folder_name: folder for results
        :param sweep_name: number of sweep
        :param k: number of sweep
        :return: results of adjoint Newton Updates for all sweeps and copying files for next sweep
        """
    start_time_ad_pimple = time.time()
    print("\nComputing Adjoint Newton Update...")
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        # ToDo keep it this way to calculate correct
        for i in range(n-k, 1, -1):
            executor.submit(computeAdjointNewtonUpdate, basepath, sweep_name, i, k)
    #            #        computeAdjointNewtonUpdate(basepath, sweep_name, i, k)
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        if k < n:
            for i in range(n, 0, -1):
                interval_name = interval.format(i)
                # Dynamic Solution
                # post.prepareNextAdjointNewton(basepath, folder_name, sweep_name, k, interval_name, i)
                #executor.submit(post.prepare_adjoint_fixed_primal, basepath, folder_name, sweep_name, k, interval_name,
                #                i)  # Fixed solution
                post.prepare_adjoint_fixed_primal(basepath, folder_name, sweep_name, k, interval_name, i)
    # ToDo put in range(n - k + 1, 1, -1) for only necessary calculations, range(n, 1, -1) for all calcs
    if k < n:
        for i in range(n - k + 1, 1, -1):
            interval_name = interval.format(i)
            post.copy_adjoint_variables(basepath, folder_name, sweep_name, k, interval_name, i)
    # Intermediate Timer
    elapsed_time = time.time() - start_time_ad_pimple
    bc.timer_and_write(basepath, elapsed_time, sweep_name, "adjoint folder")


#     FUNCTIONS FOR MAIN EXECUTION

def computeAdjoint(basepath, erasing, event):
    """

    param basepath: path of starting values
    :param erasing: yes or no for erasing files that are not needed anymore
    :param event: not used
    :return: adjoint shooting for all sweeps
    """
    # Wait for the signal from the first function
    # event.wait()

    # Verify if folder_name exists, and offers to delete it if so
    bc.checking_existence(basepath, FOLDER_NAME)
    # Starting Timer for entire Process
    start_time_all = time.time()

    # Preparing files for adjoint computation
    print("Preparing files for adjoint computation...\n")
    pre.initialize_adjoint(FOLDER_NAME, "sweep1")
    print("done")

    # Initialization loop over all Sweeps
    for k in range(1, n + 1):  # (1, n+1)
        start_time = time.time()
        sweep_name = sweep.format(k)

        # Computing Adjoint Pimple
        # TODO put k instead of 1 for only necessary calculations
        loop_adjoint_pimpledymfoam(FOLDER_NAME, sweep_name, k)

        # Computing Adjoint Defect
        print("\nADJOINT DEFECT...\n")
        # TODO put k instead of 1 for only necessary calculations
        compute_adjoint_defect(ADJOINT_PATH, sweep_name, k)

        # Computing Adjoint Linearization
        print("\nADJOINT LINEARIZATION...\n")
        # TODO in Loop
        loop_linearised_adjoint_pimpledymfoam(FOLDER_NAME, sweep_name, k)

        # Starting Adjoint Newton Update AND PREPARING NEXT SWEEP
        # TODO in loop
        loop_computeAdjointNewtonUpdate(ADJOINT_PATH, FOLDER_NAME, sweep_name, k)

        # Deleting Files after Sweep k Done
        if erasing == "yes":
            if k >= 2:
                print("Deleting files...\n")
                # post.erase_primal_adjoint_files(primal_path, adjoint_path, folder_name, k)
                # post.erase_all_files(primal_path, folder_name, k)
                post.erase_all_adjoint_files(ADJOINT_PATH, FOLDER_NAME, k - 1)
                print("The files for " + sweep.format(
                    k-1) + " in primal_path were successfully deleted. See exceptions above.")

        # Stopping intermediate timer and writing into logfile
        elapsed_time = time.time() - start_time
        bc.timer_and_write(basepath, elapsed_time, "adjoint_subintervals", sweep_name)
        os.chdir(basepath + FOLDER_NAME + "/")
        with open("pressureDropvalues.txt", "a") as mapression:
            mapression.write("\n\nAdjoint shooting of " + sweep_name + ":\n---------------------------------\n")
        mapression.close()

        # Final Timer
    elapsed_time = time.time() - start_time_all
    bc.timer_and_write(basepath, elapsed_time, "adjoint_computation", FOLDER_NAME)
    post.store_all_adjoint_values(basepath, FOLDER_NAME)
