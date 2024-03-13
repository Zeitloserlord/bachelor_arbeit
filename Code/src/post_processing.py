# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 10:30:18 2023

@author: jcosson

edited December 2023
by jwrage
"""
import csv
import os
import re
import shutil
import subprocess
from concurrent import futures

from config import n, theta, deltaT, interval, sweep, FOLDER_NAME, MAX_CPU
from config import PRIMAL_PATH, REF_MOD_DEF_PATH, ADJOINT_PATH
from src import pre_processing as pre, boundary_conditions as bc


#  PRIMAL PRIMITIVE POSTPROCESSING
def post_processing_copy_files(i, destination_file, post_pro_destination):
    """

    :param i: interval
    :param destination_file: destination
    :param post_pro_destination:
    :return: copies all the files of interval i for primal
    """
    interval_name = interval.format(i)
    for filename in os.listdir(destination_file + interval_name):
        if filename.startswith('0.') or filename.startswith(str(theta)) or filename.startswith(str(theta + deltaT * n)):
            # os.path.join(destination_file + interval_name + "/" + filename, postPro_destination)
            bc.copytree(destination_file + interval_name + "/" + filename,
                        post_pro_destination + "/" + filename + "/")  # avant bc.copytree


def prepare_post_processing(basepath, folder_name, sweep_name):
    destination_file = basepath + folder_name + '/' + sweep_name + '/'
    post_pro_destination = destination_file + "postProcessing"
    os.chdir(destination_file)
    shutil.copytree(REF_MOD_DEF_PATH + "constant/", post_pro_destination + "/constant/")
    shutil.copytree(REF_MOD_DEF_PATH + "system/", post_pro_destination + "/system/")
    # with futures.ProcessPoolExecutor(max_workers=maxCPU) as executor:
    for i in range(1, n + 1):
        # print("copyfile in loop" + str(i))
        # executor.submit(postProcessingCopyfiles, i, destination_file, post_pro_destination)
        post_processing_copy_files(i, destination_file, post_pro_destination)
    print("ready for postProcessing of " + sweep_name + "...\n")


def compute_pressure_drop_foam(basepath, folder_name, sweep_name):
    os.chdir(basepath + folder_name + '/' + sweep_name + "/postProcessing/")
    # Open a log file for pressureDrop and timers
    with open("pressureDrop.txt", "w"):
        result = os.system('computePressureDropFoam start end > pressureDrop.txt')
        print("\nComputation of Pressure Drop for " + sweep_name + " is done.\nWriting into pressureDrop.txt ...")

    # Writing the pressureDrop line into txt file
    with open("pressureDrop.txt", "r") as f:
        os.chdir(basepath + folder_name)
        with open("pressureDropvalues.txt", "a") as mapression:
            # mapression.write("\n\nShooting of " + sweep_name + ":\n---------------------------------\n" )
            for line in f:
                if "pressureDrop" in line:
                    pressure = mapression.write("\n" + str(line))  # avant : juste line
                    print(line)
        mapression.close()
    f.close()
    os.chdir(basepath)  # back to main path
    print("Done.\n")
    return pressure


def shootingUpdateP(basepath, folder_name, sweep_name, interval_name, k, i):
    startingTime = str(bc.decimal_analysis(theta + (i - 2) * deltaT))
    src_shootP = basepath + folder_name + "/" + sweep_name + "/preProcessing/0/shootingUpdateP"
    dest_shootP = basepath + folder_name + "/" + sweep.format(k + 1) + "/" + interval_name + "/" + startingTime
    if os.path.exists(src_shootP):
        shutil.copy(src_shootP, dest_shootP)


def prepare_next_newton(basepath, folder_name, sweep_name, k, interval_name, i):
    next_sweep = sweep.format(k + 1)
    next_interval = interval.format(i + 1)
    src_upfiles = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/shootingUpdate/0/"
    src_p = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        bc.decimal_analysis(theta + (i) * deltaT)) + "/p"  # correction de i-1
    dest_upfiles = basepath + folder_name + "/" + next_sweep + "/" + next_interval + "/" + str(
        bc.decimal_analysis(theta + (i) * deltaT))
    # print(str(bc.decimal_analysis(theta + (i-1)*deltaT)))
    shutil.copy(src_upfiles + "shootingUpdateU", dest_upfiles + "/U")
    shutil.copy(src_upfiles + "shootingUpdatePhi", dest_upfiles + "/phi")
    shutil.copy(src_upfiles + "shootingUpdateUf", dest_upfiles + "/Uf")
    shutil.copy(src_p, dest_upfiles)


# ADJOINT POSTPROCESSING
def prepare_adjoint_fixed_primal(basepath, folder_name, sweep_name, k, interval_name, i):
    # print("START prepare_adjoint_fixed_primal")
    next_sweep = sweep.format(k + 1)

    src_sweep = ADJOINT_PATH + folder_name + "/" + sweep_name + "/" + interval_name + "/"
    dest_sweep = ADJOINT_PATH + folder_name + "/" + next_sweep + "/" + interval_name + "/"
    shutil.copytree(src_sweep, dest_sweep)


def copy_adjoint_variables(basepath, folder_name, sweep_name, k, interval_name, i):
    next_sweep = sweep.format(k + 1)
    next_interval = interval.format(i - 1)

    dest_upfiles = basepath + folder_name + "/" + next_sweep + "/" + next_interval + "/" + str(
        -bc.decimal_analysis(theta + (i - 1) * deltaT)) + "/"
    src_pa = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        -bc.decimal_analysis(theta + (i - 1) * deltaT)) + "/"
    shutil.copy(src_pa + "pa", dest_upfiles + "pa")
    shutil.copy(src_pa + "Ua", dest_upfiles + "Ua")
    shutil.copy(src_pa + "phia", dest_upfiles + "phia")
    shutil.copy(src_pa + "Uaf", dest_upfiles + "Uaf")

    # if i>1:
    #    src_upfiles=basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/adjointShootingUpdate/0/"
    #    shutil.copy(src_upfiles + "shootingUpdateUa", dest_upfiles + "Ua")
    #    shutil.copy(src_upfiles + "shootingUpdatePhia", dest_upfiles + "phia")
    #    shutil.copy(src_upfiles + "shootingUpdateUaf", dest_upfiles + "Uaf")


def prepare_next_adjoint_newton(basepath, folder_name, sweep_name, k, interval_name, i):
    next_sweep = sweep.format(k + 1)
    next_interval = interval.format(i - 1)
    src_upfiles = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/adjointShootingUpdate/0/"
    src_p = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        -bc.decimal_analysis(theta + (i - 1) * deltaT)) + "/pa"  # correction de i-1
    dest_upfiles = basepath + folder_name + "/" + next_sweep + "/" + next_interval + "/" + str(
        -bc.decimal_analysis(theta + (i - 1) * deltaT))
    # print(str(bc.decimal_analysis(theta + (i-1)*deltaT)))

    if k < n:
        pre.prepare_next_adjoint_sweep(basepath, k, folder_name)

        # Renaming Time folder with "-"
        pre.prepare_time_folders(folder_name, next_sweep, k)

    shutil.copy(src_upfiles + "shootingUpdateUa", dest_upfiles + "/Ua")
    shutil.copy(src_upfiles + "shootingUpdatePhia", dest_upfiles + "/phia")
    shutil.copy(src_upfiles + "shootingUpdateUaf", dest_upfiles + "/Uaf")
    shutil.copy(src_p, dest_upfiles)


def compute_adjoint_pressure_drop_foam(basepath, folder_name, sweep_name):
    os.chdir(basepath + folder_name + '/' + sweep_name + "/adjoint_postProcessing/")
    # Open a log file for pressureDrop and timers
    with open("adjointPressureDrop.txt", "w"):
        os.system('computeAdjointPressureDropFoam start end > "adjointPressureDrop.txt"')
        print(
            "\nComputation of Pressure Drop for " + sweep_name + " is done.\nWriting into adjoint_pressureDrop.txt ...")

    # Writing the pressureDrop line into txt file
    with open("adjointPressureDrop.txt", "r") as f:
        os.chdir(basepath + folder_name)
        with open("pressureDropvalues.txt", "a") as mapression:
            # mapression.write("\n\nShooting of " + sweep_name + ":\n---------------------------------\n" )
            for line in f:
                if "adjointPressureDrop" in line:
                    mapression.write(line)
                    print(line)
        mapression.close()
    f.close()
    os.chdir(basepath)  # back to main path
    print("Done.\n")


def adjoint_post_processing_copyfiles(i, destination_file, postPro_destination):
    interval_name = interval.format(i)
    for filename in os.listdir(destination_file + interval_name):
        if filename.startswith('-0.') or filename.startswith(str(-theta)) or filename.startswith(
                str(-(theta + deltaT * n))):
            # os.path.join(destination_file + interval_name + "/" + filename, postPro_destination)
            bc.copytree(destination_file + interval_name + "/" + filename, postPro_destination + "/" + filename + "/")


def prepare_adjoint_post_processing(basepath, folder_name, sweep_name):
    destination_file = basepath + folder_name + '/' + sweep_name + '/'
    postPro_destination = destination_file + "adjoint_postProcessing"
    os.chdir(destination_file)
    shutil.copytree(REF_MOD_DEF_PATH + "constant/", postPro_destination + "/constant/")
    shutil.copytree(REF_MOD_DEF_PATH + "system/", postPro_destination + "/system/")

    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for i in range(1, n + 1):
            # print("copyfile in loop" + str(i))
            # executor.submit(adjointPostProcessingCopyfiles, i, destination_file, postPro_destination)
            adjoint_post_processing_copyfiles(i, destination_file, postPro_destination)
    print("ready for postProcessing of " + sweep_name + "...\n")


#   ERASING FUNCTIONS

def erase_system(path_files):
    for filename in os.listdir(path_files):
        os.remove(os.path.join(path_files, filename))
    os.rmdir(path_files)


def erase_0(path_files):
    for filename in os.listdir(path_files):
        path = os.path.join(path_files, filename)
        shutil.rmtree(path_files)
    try:
        os.remove(path)
    except Exception as e2:
        print("Error while deleting file: " + str(e2))


def erase_constant(path_files):
    try:
        shutil.rmtree(path_files + "/polyMesh/sets")
    except Exception as sets:
        print("sets deleting problem: " + str(sets))
    try:
        shutil.rmtree(path_files + "/polyMesh")
    except Exception as polyMesh:
        print('problem deleting polyMesh' + str(polyMesh))
    for filename in os.listdir(path_files):
        try:
            os.remove(os.path.join(path_files, filename))
        except:
            print("error in erase_constant line 89: os.remove(" + filename + ")")


# erases the files for the time steeps of the sweep, if there are subdirectories they will be erased too
def erase_time_files(path_files):
    for filename in os.listdir(path_files):
        if filename.startswith('0.'):
            try:
                shutil.rmtree(os.path.join(path_files, filename))
            except Exception as e1:
                try:
                    os.remove(os.path.join(path_files, filename))
                except Exception as e1:
                    print("Error while deleting directory: " + str(e1))


def erase_adjoint_time_files(path_files):
    for filename in os.listdir(path_files):
        if filename.startswith('-0.'):
            try:
                shutil.rmtree(os.path.join(path_files, filename))
            except Exception as e1:
                try:
                    os.remove(os.path.join(path_files, filename))
                except Exception as e1:
                    print("Error while deleting directory: " + str(e1))


def erase_files(path_files):
    for filename in os.listdir(path_files):
        path = os.path.join(path_files, filename)
        try:
            os.remove(path)
        except:
            try:
                shutil.rmtree(path)
            except:
                print("Failed to erase")
    if os.path.exists(path_files):
        try:
            os.removedirs(path)
        except Exception as e:
            print(e)


# deletes shootingDefect files and moves new shooting defectFile to destination
def erase_shooting_defect(basepath, sweep_name, interval_name, i):
    # starting at 2 because interval has the correct starting value and so no shooting defect
    if i != 1:
        src_shoot_file = (basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name
                          + "/shootingDefect/shooting_defect_logfile" + sweep_name + "_" + interval_name + ".txt")
        dest_shoot_file = (basepath + FOLDER_NAME + "/" + sweep_name
                           + "/logfiles/shootingDefect/shooting_defect_logfile"
                           + sweep_name + "_" + interval_name + ".txt")
        if os.path.exists(dest_shoot_file):
            os.remove(dest_shoot_file)
        if os.path.exists(src_shoot_file):
            shutil.move(src_shoot_file, dest_shoot_file)


def erase_adjoint_shooting_defect(basepath, sweep_name, interval_name, i):
    # if i!=n:
    src_shoot_file = (basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name
                      + "/adjointShootingDefect/shooting_defect_logfile" + sweep_name + "_" + interval_name + ".txt")
    dest_shoot_file = (basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/"
                       + "/logfiles/adjointShootingDefect/shooting_defect_logfile"
                       + sweep_name + "_" + interval_name + ".txt")
    if os.path.exists(dest_shoot_file):
        os.remove(dest_shoot_file)
    if os.path.exists(src_shoot_file):
        shutil.move(src_shoot_file, dest_shoot_file)


# erases all data files and safes all log files in logfile directories
def erase_all_files(basepath, folder_name, k):
    # parallelization possible
    sweep_name = sweep.format(k)
    # Interval time files
    if not os.path.exists(basepath + folder_name + "/" + sweep_name + "/logfiles/"):
        os.makedirs(basepath + folder_name + "/" + sweep_name + "/logfiles")
    for i in range(1, n + 1):
        interval_name = interval.format(i)
        interval_path_files = basepath + folder_name + "/" + sweep_name + "/" + interval_name

        # moves ShootingDefect Files to logfile directory of the sweep
        src_shoot = (
                    interval_path_files + "/shootingDefect/shooting_defect_logfile" + sweep_name + "_" + interval_name + ".txt")
        dest_shoot = (basepath + folder_name + "/" + sweep_name + "/logfiles/shooting_defect_logfile"
                      + sweep_name + "_" + interval_name + ".txt")
        if os.path.exists(src_shoot):
            shutil.move(src_shoot, dest_shoot)

        # moves log from linearised FOAM Solver to logfiles directory of the sweep
        src_log = interval_path_files + "/lin_logfilesweep" + str(
            k) + "_" + interval_name + ".txt"
        dest_log = basepath + folder_name + "/" + sweep_name + "/logfiles/lin_logfile_" + interval_name + ".txt"
        if os.path.exists(src_log):
            shutil.move(src_log, dest_log)

        # moves log from pimple FOAM solver to logfiles directory of the sweep
        src_log = interval_path_files + "/pimple.log"
        dest_log = basepath + folder_name + "/" + sweep_name + "/logfiles/pimple_" + interval_name + ".log"
        if os.path.exists(src_log):
            shutil.move(src_log, dest_log)

        # deleting all existing directories, constants, system files from all intervals of the sweep
        if os.path.exists(interval_path_files):
            erase_time_files(interval_path_files)
        if os.path.exists(interval_path_files + "/constant"):
            erase_constant(interval_path_files + "/constant")
        if os.path.exists(interval_path_files + "/system"):
            erase_system(interval_path_files + "/system")

        erase_shooting_defect(basepath, sweep_name, interval_name, i)

        if os.path.exists(interval_path_files):
            shutil.rmtree(interval_path_files)
    # moves PostProcessing log files
    src_log = basepath + folder_name + "/" + sweep_name + "/postProcessing/"
    dest_log = basepath + folder_name + "/" + sweep_name + "/"

    if os.path.exists(src_log + "pressureDrop.txt"):
        shutil.move(src_log + "pressureDrop.txt", dest_log + "/logfiles/pressureDrop" + str(k) + ".txt")

    if os.path.exists(src_log):
        shutil.rmtree(src_log)

    # Preprocessing files
    src_log = basepath + folder_name + "/" + sweep_name + "/preProcessing/shooting_update_logfilesweep" + str(
        k) + "_" + interval_name + ".txt"
    dest_log = basepath + folder_name + "/" + sweep_name + "/logfiles/shooting_update_logfilesweep" + str(
        k) + "_" + interval_name + ".txt"
    if os.path.exists(src_log):
        shutil.move(src_log, dest_log)
    if os.path.exists(basepath + folder_name + "/" + sweep_name + "/preProcessing/"):
        shutil.rmtree(basepath + folder_name + "/" + sweep_name + "/preProcessing/")


def erase_all_adjoint_files(basepath, folder_name, k):
    # parallelization possible, but the used time is not too high
    sweep_name = sweep.format(k)
    # Interval time files
    if not os.path.exists(basepath + folder_name + "/" + sweep_name + "/logfiles/"):
        os.makedirs(basepath + folder_name + "/" + sweep_name + "/logfiles/")
    for i in range(1, n + 1):
        interval_name = interval.format(i)
        interval_path_files = basepath + folder_name + "/" + sweep_name + "/" + interval_name

        # moves adjoint ShootingDefect Files to logfile directory of the sweep
        src_log = (interval_path_files + "/adjoint_shooting_defect_logfilesweep" + str(
            k) + "_" + interval_name + ".txt")
        dest_log = (basepath + folder_name + "/" + sweep_name + "/logfiles/adjoint_shooting_defect_logfilesweep"
                    + str(k) + "_" + interval_name + ".txt")
        if os.path.exists(src_log):
            shutil.move(src_log, dest_log)

        # moves log from adjoint linearised FOAM Solver to logfiles directory of the sweep
        src_log = (interval_path_files + "/adjoint_lin_logfilesweep"
                   + str(k) + "_" + interval_name + ".txt")
        dest_log = (basepath + folder_name + "/" + sweep_name + "/logfiles/adjoint_lin_logfilesweep"
                    + str(k) + "_" + interval_name + ".txt")
        if os.path.exists(src_log):
            shutil.move(src_log, dest_log)

        # moves log from adjoint pimple FOAM solver to logfiles directory of the sweep
        src_log = interval_path_files + "/adjoint_pimple.log"
        dest_log = basepath + folder_name + "/" + sweep_name + "/logfiles/pimple_" + interval_name + ".log"
        if os.path.exists(src_log):
            shutil.move(src_log, dest_log)

        # deleting all existing directories, constants, system files from all intervals of the sweep
        if os.path.exists(interval_path_files):
            erase_adjoint_time_files(interval_path_files)
        if os.path.exists(interval_path_files + "/constant"):
            erase_constant(interval_path_files + "/constant")
        if os.path.exists(interval_path_files + "/system"):
            erase_system(interval_path_files + "/system")

        erase_adjoint_shooting_defect(basepath, sweep_name, interval_name, i)

        if os.path.exists(interval_path_files):
            shutil.rmtree(interval_path_files)
    # moves adjoint PostProcessing log files
    src_log = basepath + folder_name + "/" + sweep_name + "/adjoint_postProcessing/"
    dest_log = basepath + folder_name + "/" + sweep_name + "/"
    # try:
    #    shutil.move(src_log+"pimple.log", dest_log+"/logfiles/postPro_log.log")
    # except Exception as epost:
    #    print("Error while moving postProlog: " + str(epost))
    if os.path.exists(src_log + "adjointPressureDrop.txt"):
        shutil.move(src_log + "adjointPressureDrop.txt", dest_log + "/logfiles/adjointPressureDrop" + str(k) + ".txt")
    if os.path.exists(src_log):
        shutil.rmtree(src_log)

    # Preprocessing files


#    src_log=basepath+folder_name+"/"+sweep_name+"/preProcessing/shooting_update_logfilesweep"+str(k)+"_"+interval_name+".txt"
#    dest_log=basepath+folder_name+"/"+sweep_name+"/logfiles/shooting_update_logfilesweep"+str(k)+"_"+interval_name+".txt"
#    if os.path.exists(src_log):    
#        shutil.move(src_log, dest_log)
#    if os.path.exists(basepath+folder_name+"/"+sweep_name+"/preProcessing/"):     
#        shutil.rmtree(basepath+folder_name+"/"+sweep_name+"/preProcessing/")

def erase_sweeps_res_logs(basepath, folder_name, k):
    os.chdir(basepath)
    if os.path.exists(basepath + folder_name + "/sweep" + str(k) + "_times.txt"):
        os.remove(basepath + folder_name + "/sweep" + str(k) + "_times.txt")
    if os.path.exists(basepath + folder_name + "/adjointcomputation_times.txt"):
        os.remove(basepath + folder_name + "/adjointcomputation_times.txt")
    if os.path.exists(basepath + folder_name + "/" + folder_name + "_times.txt"):
        os.remove(basepath + folder_name + "/" + folder_name + "_times.txt")


#  LOGTABLE FUNCTIONS


def store_for_plot_defect(basepath, sweep_name, interval_name, file):
    table = []
    # Partie Defect :
    _, flux_value = fetch_values_defect(basepath, file, sweep_name, interval_name)
    velocity_value, _ = fetch_values_defect(basepath, file, sweep_name, interval_name)
    # with open("logtable.csv", 'a', newline='') as tab:
    # writer = csv.writer(tab)
    # Store the variables in a table or data structure of your choice
    table_defect = table.append((velocity_value, flux_value))
    # Write the row to the CSV file
    # writer.writerow([velocity_value, flux_value])
    return table_defect


def store_all_values(basepath, folder_name):
    os.chdir(basepath + folder_name)
    print("All value will be stored in a CSV file as follows:\n")
    print(
        "Row number = Sweep Number, pressureDrop, velocity defect, continuity defect (flux), primalWallTime, "
        "SweepWallTime, AccumulatedTime\n")
    print("Writing into logtable in  " + basepath + folder_name + "\n")
    table = []
    primalWallTime = []
    acc_time = 0.0
    os.chdir(basepath + folder_name)
    with open("logtable" + str(n) + ".csv", 'a', newline='') as tab:
        writer = csv.writer(tab)
        for k in range(1, n + 1):
            sweep_name = sweep.format(k)
            velocity = 0.0
            flux = 0.0

            # Fetch pressureDrop
            pressure_drop = fetch_pressure_drop(basepath, sweep_name, k)

            for i in range(2, n + 1):
                if not k == 1:
                    interval_name = interval.format(i)
                    try:
                        _, flux_value = fetch_values_defect(basepath, sweep_name, interval_name,
                                                            "shooting_defect_logfile" + sweep_name + "_"
                                                            + interval_name + ".txt")
                    except Exception as e:
                        print("ERROR with Flux Value. Defining to -1..." + str(e))
                        flux_value = -1.0
                    try:
                        velocity_value, _ = fetch_values_defect(basepath, sweep_name, interval_name,
                                                                "shooting_defect_logfile" + sweep_name + "_"
                                                                + interval_name + ".txt")
                    except Exception:
                        print("ERROR with Velocity Value. Defining to -1...")
                        velocity_value = -1
                    velocity = velocity + float(velocity_value)
                    flux = flux + float(flux_value)

            os.chdir(basepath + folder_name)
            with open("pimpleDyMFoam_times.txt", "r") as timefile:
                for y in timefile:
                    y = y.strip()
                    primalWallTime.append(float(y))
            timefile.close()
            with open("subintervals_times.txt", "r") as timefile:
                for index, y in enumerate(timefile):
                    if index == k - 1:  # Read the line corresponding to the current round (k)
                        y = y.strip()
                        acc_time += float(y)
                        # print(y)
                        break

            # Store the variables in a table or data structure of your choice
            table.append([str(k) + "    " + str(pressure_drop) + "    " + str(round(velocity, 3)) + "    " + str(
                round(flux, 3)) + "    " + str(round(primalWallTime[k - 1], 3)) + "    " + str(round(acc_time, 3))])

        # Write the row to the CSV file
        writer.writerows(table)
        erase_sweeps_res_logs(basepath, folder_name, k)
        print("Done.\n\n\n")


def store_all_adjoint_values(basepath, folder_name):
    os.chdir(basepath + folder_name)
    print("All value will be stored in a CSV file as follows:\n")
    print(
        "Row number = Sweep Number, pressureDrop, velocity defect, continuity defect (flux), primalWallTime, "
        "SweepWallTime, AccumulatedTime\n")
    print("Writing into logtable in  " + basepath + folder_name + "\n")
    table = []
    primalWallTime = []
    acc_time = 0.0
    os.chdir(basepath + folder_name)
    with open("adjointlogtable" + str(n) + ".csv", 'a', newline='') as tab:
        writer = csv.writer(tab)
        for k in range(1, n + 1):
            sweep_name = sweep.format(k)
            velocity = 0.0
            flux = 0.0

            # Fetch pressureDrop
            pressure_drop = fetch_adjoint_pressure_drop(basepath, sweep_name, k)

            for i in range(1, n):
                interval_name = interval.format(i)
                if i == k:
                    flux_value = 0
                    velocity_value = 0
                else:
                    try:
                        _, flux_value = fetch_adjoint_values_defect(basepath, sweep_name, interval_name,
                                                                    "adjoint_shooting_defect_logfile" + sweep_name
                                                                    + "_" + interval_name + ".txt")
                    except Exception as e:
                        print("flux value problem")
                    try:
                        velocity_value, _ = fetch_adjoint_values_defect(basepath, sweep_name, interval_name,
                                                                        "adjoint_shooting_defect_logfile" + sweep_name
                                                                        + "_" + interval_name + ".txt")
                    except Exception as e:
                        print("velocity value problem ")
                        print(e)
                    try:
                        velocity = velocity + float(velocity_value)
                        flux = flux + float(flux_value)
                    except Exception as e:
                        print("summing problem")
                        print(e)
            os.chdir(basepath + folder_name)
            with open("enhancedAdjointPimpleDyMFoam_times.txt", "r") as timefile:
                for y in timefile:
                    y = y.strip()
                    primalWallTime.append(float(y))
            timefile.close()
            with open("adjoint_subintervals_times.txt", "r") as timefile:
                for index, y in enumerate(timefile):
                    if index == k - 1:  # Read the line corresponding to the current round (k)
                        y = y.strip()
                        acc_time += float(y)
                        # print(y)
                        break

            # Store the variables in a table or data structure of your choice
            table.append([str(k) + "    " + str(pressure_drop) + "    " + str(round(velocity, 3)) + "    " + str(
                round(flux, 3)) + "    " + str(round(primalWallTime[k - 1], 3)) + "    " + str(round(acc_time, 3))])

        # Write the row to the CSV file
        writer.writerows(table)
        erase_sweeps_res_logs(basepath, folder_name, k)
        print("Done.\n\n\n")


def fetch_pressure_drop(basepath, sweep_name, k):
    # print(basepath + folder_name + "/" + sweep_name + "/adjointPostProcessing/")
    if os.path.exists(basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/"):
        pressure_path = basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/pressureDrop" + str(k) + ".txt"
        pressure_drop = fetch_values(basepath, pressure_path, "pressureDrop is")
    elif os.path.exists(basepath + FOLDER_NAME + "/" + sweep_name + "/postProcessing/"):
        pressure_path = basepath + FOLDER_NAME + "/" + sweep_name + "/postProcessing/pressureDrop.txt"
        pressure_drop = fetch_values(basepath, pressure_path, "pressureDrop is")
    else:
        print("Pressure Drop not found ")
        pressure_drop = 0
    return pressure_drop


def fetch_adjoint_pressure_drop(basepath, sweep_name, k):
    if os.path.exists(basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/"):
        pressure_path = basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/adjointPressureDrop" + str(k) + ".txt"
        pressure_drop = fetch_values(basepath, pressure_path, "adjointPressureDrop is")
    elif os.path.exists(basepath + FOLDER_NAME + "/" + sweep_name + "/adjoint_postProcessing/"):
        pressure_path = basepath + FOLDER_NAME + "/" + sweep_name + "/adjoint_postProcessing/adjointPressureDrop.txt"
        pressure_drop = fetch_values(basepath, pressure_path, "adjointPressureDrop is")
    else:
        print("Pressure Drop not found ")
        pressure_drop = 0
    return pressure_drop


def fetch_values_defect(basepath, sweep_name, interval_name, file):
    # Regular expression pattern to capture the value
    velocity = r"defects \(velocity\): sum local = ([\d.e+-]+)"
    fluxes = r"defects \(fluxes\): sum local = ([\d.e+-]+)"
    # print(primal_path + folder_name + "/" + sweep_name + "/" + interval_name +  "/shootingDefect/")
    if os.path.exists(PRIMAL_PATH + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/"):
        path_file = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/"
        # os.chdir(path_file)
    # path_file = #shooting_defect_logfile" + sweep_name + "_" + interval_name + ".txt"
    elif os.path.exists(basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/"):
        path_file = basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/"

    with open(path_file + file, "r") as read_file:
        text = read_file.read()
        # Search for the pattern in each line
        for line in text.split('\n'):
            velocity_match = re.search(velocity, line)
            flux_match = re.search(fluxes, line)
            if velocity_match:
                velocity_defect = velocity_match.group(1)
                # print("defects (velocity): sum local:", velocity_defect)
            if flux_match:
                flux_defect = flux_match.group(1)
                # print("defects (fluxes): sum local:", flux_defect)
    return velocity_defect, flux_defect


def fetch_adjoint_values_defect(basepath, sweep_name, interval_name, file):
    # Regular expression pattern to capture the value
    velocity = r"defects \(adjoint velocity\): sum local = [-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"  ### r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"      ([\d.e+-]+)
    fluxes = r"defects \(adjoint fluxes\): sum local = [-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"  # ([\d.e+-]+)"
    if os.path.exists(basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/"):
        path_file = basepath + FOLDER_NAME + "/" + sweep_name + "/logfiles/"
        os.chdir(path_file)
    elif os.path.exists(basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/"):
        path_file = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/"
        os.chdir(path_file)
    if os.path.exists(path_file + file):
        with open(file, "r") as read_file:
            text = read_file.read()
            # Search for the pattern in each line
            for line in text.split('\n'):
                velocity_match = re.search(velocity, line)
                flux_match = re.search(fluxes, line)
                if velocity_match:
                    velocity_defect = velocity_match.group(1)
                    # print("defects (adjoint velocity): sum local:", velocity_defect)
                if flux_match:
                    flux_defect = flux_match.group(1)
                    # print("defects (adjoint fluxes): sum local:", flux_defect)
                    return float(velocity_defect), float(flux_defect)


def fetch_values(basepath, path_file, line_to_find):
    value = None

    with open(path_file, "r") as file:
        for line in file:
            if line_to_find in line:
                value = line.split()[-1]
                return (value)
                break

    if value is not None:
        print("Extracted value:", value)
    else:
        print("Value not found in the file.")


#    PLOT FUNCTIONS

def plot_my_data(basepath, filename, x_axis, y_axis, new_folder, k):
    os.chdir(basepath + new_folder + "/")
    print(basepath + new_folder)
    # Read the first and last lines of logtable.csv
    with open("logtable" + str(k) + ".csv", 'r') as file:
        first_line = file.readline().strip().split('    ')
        last_line = file.readlines()[-1].strip().split('    ')

    # Get the column values based on x_axis and y_axis
    num_columns = len(first_line)
    x_min = float(first_line[min(x_axis - 1, num_columns - 1)])
    x_max = float(last_line[min(x_axis - 1, num_columns - 1)])
    y_min = float(first_line[min(y_axis - 1, num_columns - 1)])
    y_max = float(last_line[min(y_axis - 1, num_columns - 1)])
    axis_labels = {
        1: "Sweep [-]",
        2: "Pressure Drop [Nm, E-7]",
        3: "Impuls Defect [kg.m.s⁻¹]",
        4: "Continuity Defect [kg.m.s⁻¹]",
        5: "Wall Time Primal [s]",
        6: "Total Accumulated Time [s]"
    }
    xrange_values = {
        1: "[{}:{}]\n".format(0, k + 1),
        2: "[{}:{}]\n".format(0, x_max),
        3: "[{}:{}]\n".format(0, x_max),
        4: "[{}:{}]\n".format(0, x_max),
        5: "[{}:{}]\n".format(0, x_max),
        6: "[{}:{}]\n".format(0, x_max),
    }
    yrange_values = {
        1: "[0:{}]\n".format(k + 1),
        2: "[0:1.5]\n",
        3: "[{}:{}]\n".format(y_max, y_min),
        4: "[{}:{}]\n".format(y_max, y_min),
        5: "[{}:{}]\n".format(0, y_max + 50),
        6: "[{}:{}]\n".format(0, y_max),
    }

    with open(filename, 'r') as file:
        lines = file.readlines()

    modified_lines = []
    for line in lines:
        if line.startswith('set title'):
            # new_title="Plot for " + str(n) + " subintervals"
            new_title = "Plot for {} subintervals".format(k)
            modified_lines.append("set title '" + new_title + "'\n")
        elif line.startswith("set xlabel"):
            modified_lines.append("set xlabel '" + axis_labels[x_axis] + "'\n")
        elif line.startswith("set ylabel"):
            modified_lines.append("set ylabel '" + axis_labels[y_axis] + "'\n")
        elif line.startswith("set xrange"):
            modified_lines.append("set xrange " + xrange_values[x_axis])
        elif line.startswith("set yrange"):
            modified_lines.append("set yrange " + yrange_values[y_axis])
        elif line.startswith("plot 'logtable" + str(k) + ".csv'"):
            parts = line.split("using ")
            parts[1] = str(x_axis) + ":" + str(y_axis)
            if y_axis == 2:
                parts[1] = str(x_axis) + ":(${}*10e6)".format(y_axis)
            modified_lines.append("using ".join(parts) + " with linespoints ls 1 title 'Primal Shooting',")
        elif line.startswith("set output "):

            # Construct the plot filename based on the given options
            #plot_filename = "plot_{}_{}_{}.eps".format(x_axis, y_axis, title)
            plot_filename = "plot_{}_{}_{}_intervals.eps".format(x_axis, y_axis, k)
            modified_lines.append("set output '" + plot_filename + "'\n")
        else:
            modified_lines.append(line)

    with open(filename, 'w') as file:
        file.writelines(modified_lines)

    # Execute the bash command to generate the plot
    subprocess.run(["gnuplot", filename])
    # # Example usage:
    # filename = 'path/to/file'
    # modify_plot_code_in_file(filename, 6, 2, "Custom Plot Title")


def all_plots_new(basepath):
    bash_path = "/nfs/servers/fourier/temp-1/wrage/primal/plots/shootingManagerOutput.plot"
        #"/home/jcosson/workspace/henersj_shootingdata/scripts/gnuplot/shootingManagerOutput.plot"
    intervals = [2, 4, 5, 20]
    for intervals in intervals:
        new_folder = str(intervals) + "_timeparallel_1"
        dest_bash = basepath + new_folder + "/shootingManagerOutput.plot"
        shutil.copyfile(bash_path, dest_bash)
        print("Plotting in " + basepath + new_folder + " ...\n")
        os.chdir(basepath + new_folder + "/")
        plot_my_data(basepath, "shootingManagerOutput.plot", 6, 2, new_folder, intervals)
        plot_my_data(basepath, "shootingManagerOutput.plot", 6, 1, new_folder, intervals)
        plot_my_data(basepath, "shootingManagerOutput.plot", 1, 2, new_folder, intervals)
        plot_my_data(basepath, "shootingManagerOutput.plot", 1, 3, new_folder, intervals)
        plot_my_data(basepath, "shootingManagerOutput.plot", 1, 4, new_folder, intervals)
        plot_my_data(basepath, "shootingManagerOutput.plot", 1, 5, new_folder, intervals)
    print("Data has been plotted.")


def multiple_plots(basepath, filename, x_axis, y_axis, intervals):
    os.chdir(basepath)
    bash_path = "/nfs/servers/fourier/temp-1/wrage/primal/plots/shootingManagerOutput.plot"\
                # "/home/jcosson/workspace/henersj_shootingdata/scripts/gnuplot/multiplePlotShooting.plot"
    dest_bash = basepath + "/multiplePlotShooting" + str(x_axis) + str(y_axis) + ".plot"
    shutil.copyfile(bash_path, dest_bash)
    filename = "multiplePlotShooting" + str(x_axis) + str(y_axis) + ".plot"
    print("Plotting in " + basepath + " ...\n")
    for interval in intervals:
        with open(str(interval) + "_timeparallel_1" + "/logtable" + str(interval) + ".csv", 'r') as file:
            first_line = file.readline().strip().split('    ')
            last_line = file.readlines()[-1].strip().split('    ')

        # Get the column values based on x_axis and y_axis
        num_columns = len(first_line)
        x_min = float(first_line[min(x_axis - 1, num_columns - 1)])
        x_max = float(last_line[min(x_axis - 1, num_columns - 1)])
        y_min = float(first_line[min(y_axis - 1, num_columns - 1)])
        y_max = float(last_line[min(y_axis - 1, num_columns - 1)])

        axis_labels = {
            1: "Sweep [-]",
            2: "Pressure Drop [Nm, E-7]",
            3: "Impuls Defect [kg.m.s⁻¹]",
            4: "Continuity Defect [kg.m.s⁻¹]",
            5: "Wall Time Primal [s]",
            6: "Total Accumulated Time [s]"
        }
        xrange_values = {
            1: "[{}:{}]\n".format(0, interval),
            2: "[{}:{}]\n".format(0, x_max * 10e5),
            3: "[{}:{}]\n".format(x_max, x_min),
            4: "[{}:{}]\n".format(0, x_max),
            5: "[{}:{}]\n".format(0, x_max),
            6: "[{}:{}]\n".format(0, x_max),
        }
        yrange_values = {
            1: "[0:{}]\n".format(interval),
            2: "[0:{}]\n".format(y_max, 10e-5),
            3: "[{}:{}]\n".format(y_max, y_min),
            4: "[{}:{}]\n".format(y_max, y_min),
            5: "[{}:{}]\n".format(0, y_max + 50),
            6: "[{}:{}]\n".format(0, y_max),
        }
    with open(filename, 'r') as file:
        lines = file.readlines()
    modified_lines = []
    num = 1
    for line in lines:
        if line.startswith('set title'):
            new_title = "Plot Comparison over {} subintervals".format(intervals)
            modified_lines.append("set title '" + new_title + "'\n")
        elif line.startswith("set xlabel"):
            modified_lines.append("set xlabel '" + axis_labels[x_axis] + "'\n")
        elif line.startswith("set ylabel"):
            modified_lines.append("set ylabel '" + axis_labels[y_axis] + "'\n")
        elif line.startswith("set xrange"):
            modified_lines.append("set xrange " + xrange_values[x_axis])
        elif line.startswith("set yrange"):
            modified_lines.append("set yrange " + yrange_values[y_axis])
        elif line.startswith("set output "):
            plot_filename = "plot_{}_{}_{}_intervals.eps".format(x_axis, y_axis, "Comparison")
            plot_filename_png = "plot_{}_{}_{}_intervals.png".format(x_axis, y_axis, "Comparison")
            modified_lines.append("set output '" + plot_filename + "'\n" + "set output '" + plot_filename_png + "'\n")

        elif line.endswith("' , \\\n"):
            print(line)
            # Delete existing lines
            del lines[num - 1]
        else:
            modified_lines.append(line)
        num += 1
        print(line)

    plot_commands = []
    for interval in intervals:
        plot_command = ("'{}_timeparallel_1/logtable{}.csv' using {}:{} with linespoints title '{} intervals' "
                        .format(interval, interval, x_axis, y_axis, interval))
        plot_commands.append(plot_command)

    # Join the plot commands using a comma and a line continuation character \
    plot_command_string = ", \\\n".join(plot_commands)

    # Final plot command
    final_plot_command = "plot " + plot_command_string

    # Append the final_plot_command to modified_lines
    modified_lines.append(final_plot_command)

    with open(filename, 'w') as file:
        file.writelines(modified_lines)

    # Execute the bash command to generate the plot
    subprocess.run(["gnuplot", filename])
