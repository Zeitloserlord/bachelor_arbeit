# -*- coding: utf-8 -*-
"""
Created on Mon Apr 17 17:40:10 2023

@author: jcosson

edited December 2023
by jwrage
"""
import fileinput
import os
import shutil
import sys
from concurrent import futures

from config import n, theta, deltaT, interval, sweep, FOLDER_NAME, MAX_CPU
from config import PRIMAL_PATH, REF_CASES_PATH, ADJOINT_PATH, CALCS_PATH
from src import boundary_conditions as bc, post_processing as post


#  PRIMAL PRIMITIVE PREPROCESSING
def copy_shoot_dirs(basepath, x, folder_name, previous_sweep_name, sweep_name):
    interval_name = interval.format(x)
    source_interval = basepath + folder_name + "/" + previous_sweep_name + "/" + interval_name
    destination_interval = basepath + folder_name + "/" + sweep_name
    shutil.copytree(source_interval, os.path.join(destination_interval, os.path.basename(source_interval)))


def prepare_next_sweep_starting_files(basepath, folder_name, previous_sweep_name, sweep_name, i):

    # paths and end time
    source = os.path.join(basepath, folder_name, previous_sweep_name, interval.format(i))
    destination = os.path.join(basepath, folder_name, sweep_name, interval.format(i))
    end_time = bc.decimal_analysis(theta + deltaT * (i - 1))

    # destination files
    destination_constant = os.path.join(destination, 'constant')
    destination_system = os.path.join(destination, 'system')
    destination_end_time = os.path.join(destination, str(end_time))

    # source files
    source_constant = os.path.join(source, 'constant')
    source_system = os.path.join(source, 'system')
    source_end_time = os.path.join(basepath, folder_name, previous_sweep_name, interval.format(i - 1), str(end_time))

    # copy data
    shutil.copytree(source_constant, destination_constant)
    shutil.copytree(source_system, destination_system)
    shutil.copytree(source_end_time, destination_end_time)
    print('Preparing for: ' + sweep_name + ' and ' + interval.format(i)
          + '. New start time, is the previous end time: ' + str(end_time))


def prepare_next_sweep(basepath, k, folder_name):
    # Prepare all shooting intervals of next sweep for computation
    sweep_name = sweep.format(k + 1)  # k+1
    previous_sweep_name = sweep.format(k)  # k
    os.path.join(folder_name, sweep_name)
    print("\nPreparing shooting of " + sweep_name + ". ")
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        # Copy Directories that were already shoot. Warning : put that after the computations
        for x in range(1, k + 1):  # k+1
            executor.submit(copy_shoot_dirs, basepath, x, folder_name, previous_sweep_name, sweep_name)
    # Preparing shooting directories from sweep1 data
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for i in range(k + 1, n + 1):  # will become k + 1, n + 1 because of first loop being put into the big loop
            executor.submit(prepare_next_sweep_starting_files, basepath, folder_name, previous_sweep_name, sweep_name,
                            i)


#  PRIMAL STEFFENSEN PREPROCESSING

def prepare_shooting_update(basepath, folder_name, sweep_name, k,
                            i):  # should start from sweep2, after interval2 is done

    # Copy Violet, Red, Blue, Green and Orange to prepare yellow (cf model)
    interval_name = interval.format(i - 1)
    next_interval = interval.format(i)
    next_sweep = sweep.format(k + 1)
    sweep_folder = os.path.join(basepath, folder_name, sweep_name)
    interval_folder = os.path.join(sweep_folder, interval_name)
    if not os.path.exists(os.path.join(sweep_folder, "preProcessing")):
        os.mkdir(os.path.join(sweep_folder, "preProcessing"))
        os.mkdir(os.path.join(sweep_folder, "preProcessing", "0"))
    zero_shooting_update = os.path.join(sweep_folder, "preProcessing", "0")

    # Copy codes, see master_script
    src_violet_folder = os.path.join(interval_folder, str(bc.decimal_analysis(theta + (i - 2) * deltaT)))
    shutil.copy(src_violet_folder + "p", zero_shooting_update + "pStart_left")
    shutil.copy(src_violet_folder + "U", zero_shooting_update + "UStart_left")
    shutil.copy(src_violet_folder + "Uf", zero_shooting_update + "UfStart_left")
    shutil.copy(src_violet_folder + "phi", zero_shooting_update + "phiStart_left")
    # print("Copy code VIOLET done.")

    src_red_folder = os.path.join(interval_folder, str(bc.decimal_analysis(theta + (i - 1) * deltaT)))
    shutil.copy(src_red_folder + "p", zero_shooting_update + "pEnd_left")
    shutil.copy(src_red_folder + "U", zero_shooting_update + "UEnd_left")
    shutil.copy(src_red_folder + "Uf", zero_shooting_update + "UfEnd_left")
    shutil.copy(src_red_folder + "phi", zero_shooting_update + "phiEnd_left")
    # print("Copy code RED done.")

    shutil.copy(src_red_folder + "linU", zero_shooting_update + "dUdu")
    shutil.copy(src_red_folder + "linP", zero_shooting_update + "dPdp")
    shutil.copy(src_red_folder + "linUf", zero_shooting_update + "dUduf")
    # print("Copy code BLUE done.")

    src_green_folder = basepath + folder_name + "/" + next_sweep + "/" + interval_name + "/" + str(
        bc.decimal_analysis(theta + (i - 2) * deltaT)) + "/"
    shutil.copy(src_green_folder + "p",
                zero_shooting_update + "shootingUpdateP_left")  # instead of shootingUpdateP_left
    shutil.copy(src_green_folder + "U", zero_shooting_update + "shootingUpdateU_left")
    shutil.copy(src_green_folder + "Uf", zero_shooting_update + "shootingUpdateUf_left")
    shutil.copy(src_green_folder + "phi", zero_shooting_update + "shootingUpdatePhi_left")
    # print("Copy code GREEN done.")

    src_orange_folder = basepath + folder_name + "/" + sweep_name + "/" + next_interval + "/" + str(
        bc.decimal_analysis(theta + (i - 1) * deltaT)) + "/"
    shutil.copy(src_orange_folder + "p", zero_shooting_update + "pStart_right")
    shutil.copy(src_orange_folder + "U", zero_shooting_update + "UStart_right")
    shutil.copy(src_orange_folder + "Uf", zero_shooting_update + "UfStart_right")
    shutil.copy(src_orange_folder + "phi", zero_shooting_update + "phiStart_right")
    # print("Copy code ORANGE done.")

    # New linU and linP (Defect Update)
    src_lin_u = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/linUDefect"
    src_lin_p = REF_CASES_PATH + "/boundaryConditions/linP0"
    dest_lin_u = basepath + folder_name + "/" + next_sweep + "/" + interval_name + "/" + str(
        bc.decimal_analysis(theta + (i - 2) * deltaT)) + "/linU"
    dest_lin_p = basepath + folder_name + "/" + next_sweep + "/" + interval_name + "/" + str(
        bc.decimal_analysis(theta + (i - 2) * deltaT)) + "/linP"
    shutil.copy(src_lin_u, dest_lin_u)
    shutil.copy(src_lin_p, dest_lin_p)

    # Copy of constant and system files
    if not os.path.exists(basepath + folder_name + "/" + sweep_name + "/preProcessing/constant/"):
        src_constant = basepath + folder_name + "/" + sweep_name + "/" + interval.format(i) + "/constant/"
        src_system = basepath + folder_name + "/" + sweep_name + "/" + interval.format(i) + "/system/"
        shutil.copytree(src_constant, basepath + folder_name + "/" + sweep_name + "/preProcessing/constant/")
        shutil.copytree(src_system, basepath + folder_name + "/" + sweep_name + "/preProcessing/system/")
    print(interval_name + " ready for copy code YELLOW")


def prepare_defect_computation(basepath, sweep_name, interval_name, previous_interval, i):  # for computeDefect

    # Fetch shootingDefect from ref_Cases
    src_shooting_defect = REF_CASES_PATH + "shootingDefect/"
    dest_shooting_defect = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/"
    shutil.copytree(src_shooting_defect, dest_shooting_defect)

    starting_time = str(bc.decimal_analysis(theta + (i - 1) * deltaT))
    ending_time = str(bc.decimal_analysis(theta + (i - 1) * deltaT))

    # Fetch U, p, phi from current interval
    src_u = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/" + starting_time + "/U"
    src_p = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/" + starting_time + "/p"
    src_phi = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/" + starting_time + "/phi"

    dest_u = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/UInit_right"
    dest_p = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/pInit_right"
    dest_phi = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/phiInit_right"

    shutil.copyfile(src_u, dest_u)
    shutil.copyfile(src_p, dest_p)
    shutil.copyfile(src_phi, dest_phi)

    # Fetch U, p, phi from previous interval
    src_u = basepath + FOLDER_NAME + "/" + sweep_name + "/" + previous_interval + "/" + ending_time + "/U"
    src_p = basepath + FOLDER_NAME + "/" + sweep_name + "/" + previous_interval + "/" + ending_time + "/p"
    src_phi = basepath + FOLDER_NAME + "/" + sweep_name + "/" + previous_interval + "/" + ending_time + "/phi"

    dest_u = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/UShootEnd"
    dest_p = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/pShootEnd"
    dest_phi = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/phiShootEnd"

    shutil.copyfile(src_u, dest_u)
    shutil.copyfile(src_p, dest_p)
    shutil.copyfile(src_phi, dest_phi)

    # U and p defect
    #    src_linUDefect=basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/LinUDefect"


#    src_linUDefect=ref_cases + "boundaryConditions/linUDefect"
#    src_linPDefect=ref_cases + "boundaryConditions/linPDefect"
#    dest_linUDefect=basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + startingTime +"/LinUDefect"
#    dest_linPDefect=basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + startingTime +"/linPDefect"
#    
#    shutil.copyfile(src_linUDefect, dest_linUDefect)
#    shutil.copyfile(src_linPDefect, dest_linPDefect)


#  PRIMAL LINEARIZATION PREPROCESSING
def initialize_linearization(basepath, folder_name, sweep_name):
    # IS ONLY THOUGHT FOR SWEEP1
    # Copy files to prepare linearisedPimpleDyMFoam
    if not os.path.exists(folder_name):
        print("ERROR: No such file or directory. Exiting Shooting Manager")
        sys.exit()

    # Paths for lin and fv files
    linP_path = REF_CASES_PATH + "/boundaryConditions/linP"
    linU_path = REF_CASES_PATH + "/boundaryConditions/linU"
    fv_schemes_path = REF_CASES_PATH + "/controlBib/fvSchemes"
    fv_solution_path = REF_CASES_PATH + "/controlBib/fvSolution"
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for i in range(1, n + 1):  # will become k + 1, n + 1 because of first loop being put into the big loop
            executor.submit(copy_linearization, folder_name, sweep_name, i, linP_path, linU_path, fv_schemes_path,
                            fv_solution_path)


def copy_linearization(basepath, folder_name, sweep_name, i, linP_path, linU_path, fvSchemes_path, fvSolution_path):
    interval_name = interval.format(i)
    start_time_dest = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        bc.decimal_analysis(theta + (i - 1) * deltaT))

    # Copy lin files
    shutil.copy2(linP_path, start_time_dest + "/linP")
    shutil.copy2(linU_path, start_time_dest + "/linU")

    # Copy fv files
    shutil.copy(fvSchemes_path, basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/system")
    shutil.copy(fvSolution_path, basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/system")

    bc.check_existence(REF_CASES_PATH + "/boundaryConditions/", "linU")


def prepare_next_linearization(basepath, folder_name, k, i):
    interval_name = interval.format(i)
    if not os.path.exists(folder_name):
        print("ERROR: No such file or directory. Exiting Shooting Manager")
        sys.exit()
        # if k<=n:
    sweep_name = sweep.format(k)

    # Paths for lin and fv files, OLD paths without Newton Update
    #   linP_path=ref_cases + "/boundaryConditions/linP"
    #   linU_path=ref_cases + "/boundaryConditions/linU"
    fvSchemes_path = REF_CASES_PATH + "/controlBib/fvSchemes"
    fvSolution_path = REF_CASES_PATH + "/controlBib/fvSolution"

    # New Paths for linP and linU, taking the Newton Update into account:
    linP_path = REF_CASES_PATH + "/boundaryConditions/linP0"
    linU_path = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/shootingDefect/0/linUDefect"

    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for i in range(1 + 1, n + 1):  # avant c'était
            executor.submit(copy_linearization, basepath, folder_name, sweep_name, i, linP_path, linU_path,
                            fvSchemes_path, fvSolution_path)


def prepareNewtonUpdate(basepath, folder_name, sweep_name, k, interval_name, i):  # on st int2 et on prepare int3
    # Fetch shooting Update folder from postPro cases
    src_shootUpdate = REF_CASES_PATH + "shootingDefect/"
    dest_shootUpdate = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/shootingUpdate/"
    if os.path.exists(dest_shootUpdate):
        print("Replacing file")
        post.erase_files(dest_shootUpdate)
    shutil.copytree(src_shootUpdate, dest_shootUpdate)

    # Fetch data from EndTime folder
    src_data = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        bc.decimal_analysis(theta + (i) * deltaT))
    src_data_start = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        bc.decimal_analysis(theta + (i - 1) * deltaT))
    print("The time for linUf to copy: " + src_data_start)
    # Copy to shootingUpdate
    dest_data = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/shootingUpdate/0/"
    shutil.copy(src_data + "/linU", dest_data + "dUdu")
    shutil.copy(src_data + "/linUf", dest_data + "dUduf")
    shutil.copy(src_data + "/linP", dest_data + "dPdp")
    shutil.copy(src_data + "/U", dest_data + "UEnd_left")
    shutil.copy(src_data + "/p", dest_data + "pEnd_left")
    shutil.copy(src_data + "/phi", dest_data + "phiEnd_left")
    shutil.copy(src_data + "/Uf", dest_data + "UfEnd_left")
    shutil.copy(src_data + "/U", dest_data + "shootingUpdateU")
    shutil.copy(src_data + "/p", dest_data + "shootingUpdateP")
    shutil.copy(src_data + "/phi", dest_data + "shootingUpdatePhi")
    shutil.copy(src_data + "/Uf", dest_data + "shootingUpdateUf")

    # Fetching data for limitor
    shutil.copy(src_data_start + "/linU", dest_data + "dUdu_Init")
    # shutil.copy(src_data_start+"/linUf", dest_data+"dUduf_Init")
    shutil.copy(src_data_start + "/linP", dest_data + "dPdp_Init")


#       ADJOINT PREPROCESSING

def initialize_adjoint(folder_name, sweep_name):
    for i in range(1, n + 1):
        interval_name = interval.format(i)
        src_case = PRIMAL_PATH + folder_name + "/" + "sweep" + str(
            n) + "/" + interval_name  # Solution from very last sweep (the more precise) is taken

        dest_case = ADJOINT_PATH + folder_name + "/" + sweep_name + "/" + interval_name

        shutil.copytree(src_case + "/system/", dest_case + "/system/")
        shutil.copytree(src_case + "/constant/", dest_case + "/constant/")
        # Copy fv files
        fvSchemes_path = REF_CASES_PATH + "/controlBib/fvSchemes"
        fvSolution_path = REF_CASES_PATH + "/controlBib/fvSolution"
        shutil.copy(fvSchemes_path, ADJOINT_PATH + folder_name + "/" + sweep_name + "/" + interval_name + "/system")
        shutil.copy(fvSolution_path, ADJOINT_PATH + folder_name + "/" + sweep_name + "/" + interval_name + "/system")

        controlDict_path = ADJOINT_PATH + folder_name + '/' + sweep_name + '/' + interval_name + '/system/controlDict'
        startTime = bc.decimal_analysis(theta + deltaT * (i - 1))
        endTime = bc.decimal_analysis(theta + deltaT * i)

        for line in fileinput.input(controlDict_path, inplace=True):
            if line.startswith('startTime'):
                line = 'startTime       {};'.format(-endTime)
            elif line.startswith('endTime'):
                line = 'endTime         {};'.format(-startTime)  # {};\n'
            print(line)
        print('startTime       {};'.format(-endTime))

        for filename in os.listdir(src_case):
            if filename.startswith('0.'):
                try:
                    shutil.copytree(src_case + "/" + filename + "/", dest_case + "/-" + filename + "/")
                except Exception as e1:
                    print(e1)

                    # Preparing next interval (i-1)    #Current Sweep current interval
        src_adjoint_undeformed_var = CALCS_PATH + "adjoint_undeformed/" + str(-endTime) + "/"
        dest_adjoint_undeformed_var = ADJOINT_PATH + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
            -endTime) + "/"
        shutil.copyfile(src_adjoint_undeformed_var + "pa", dest_adjoint_undeformed_var + "pa")
        shutil.copyfile(src_adjoint_undeformed_var + "Ua", dest_adjoint_undeformed_var + "Ua")

        shutil.copyfile(src_adjoint_undeformed_var + "Uaf", dest_adjoint_undeformed_var + "Uaf")
        shutil.copyfile(src_adjoint_undeformed_var + "phia", dest_adjoint_undeformed_var + "phia")

        os.chdir(ADJOINT_PATH + folder_name)
        with open("pressureDropvalues.txt", "w") as time:
            time.write(
                "\n\n=============================================================================\n\n"
                + "                         LOGFILE " + folder_name
                + "\n\n=============================================================================\n\n")
        time.close()
        os.chdir(ADJOINT_PATH)


def copy_adjoint_shoot_directories(basepath, i, folder_name, previous_sweep_name, sweep_name):
    interval_name = interval.format(i)
    source_interval = basepath + folder_name + "/" + previous_sweep_name + "/" + interval_name + "/"
    destination_interval = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/"
    shutil.copytree(source_interval, destination_interval)


def prepare_next_adjoint_sweep_starting_files(basepath, folder_name, previous_sweep_name, sweep_name, i):
    interval_name = interval.format(i)
    destination_constant = basepath + folder_name + "/" + sweep_name + "/" + interval_name
    destination_system = basepath + folder_name + "/" + sweep_name + "/" + interval_name
    previous_interval_name = interval.format(i + 1)

    endTime = -bc.decimal_analysis(theta + deltaT * i)  # I AVANT
    startTime = -bc.decimal_analysis(theta + deltaT * i)  # I-1 AVANT
    new_endTime = -bc.decimal_analysis(theta + deltaT * (i - 1))
    print("previous interval with previous endtime: " + previous_interval_name + "   " + str(endTime))

    source_constant = basepath + folder_name + "/" + previous_sweep_name + "/" + interval_name + '/constant'
    source_system = basepath + folder_name + "/" + previous_sweep_name + "/" + interval_name + '/system'
    source_endTime = basepath + folder_name + "/" + previous_sweep_name + "/" + previous_interval_name + '/' + str(
        endTime)

    print("Previous Sweep, previous interval ending time for new starting time : " + source_endTime)
    destination_endTime = basepath + folder_name + "/" + sweep_name + "/" + interval_name
    try:
        shutil.copytree(source_constant, os.path.join(destination_constant, os.path.basename(source_constant)))
    except Exception as e:
        print(e)
    try:
        shutil.copytree(source_system, os.path.join(destination_system, os.path.basename(source_system)))
    except Exception as e:
        print(e)
    if os.path.exists(destination_endTime + "/" + str(endTime)):
        shutil.rmtree(destination_endTime + "/" + str(endTime))
    shutil.copytree(source_endTime, destination_endTime + "/" + str(endTime))
    print(
        "\n\n\n\nPREPARING for: " + sweep_name + " and " + interval_name + ". Previous end time, that is new start time: " + str(
            endTime))
    control_dict_path = ADJOINT_PATH + folder_name + '/' + sweep_name + '/' + interval_name + '/system/controlDict'
    # print(control_dict_path)
    for line in fileinput.input(control_dict_path, inplace=True):
        if line.startswith('startTime'):
            line = 'startTime       {};'.format(startTime)
        elif line.startswith('endTime'):
            line = 'endTime         {};'.format(new_endTime)  # {};\n'
        print(line)
    print('startTime       {};'.format(endTime))


def prepare_next_adjoint_sweep(basepath, k, folder_name):
    # Prepare all shooting intervals of next sweep for computation
    sweep_name = sweep.format(k + 1)  # k+1
    previous_sweep_name = sweep.format(k)  # k
    print("previous sweep: " + previous_sweep_name)
    os.path.join(folder_name, sweep_name)
    print("\nPreparing shooting of " + sweep_name + ". ")
    # with futures.ProcessPoolExecutor(max_workers=maxCPU) as executor:
    # Copy Directories that were already shoot. Warning : put that after the computations
    for i in range(n, n - k, -1):  # k+1
        # executor.submit(copyShootDirs, basepath, x, folder_name, previous_sweep_name, sweep_name)
        try:
            copy_adjoint_shoot_directories(basepath, i, folder_name, previous_sweep_name, sweep_name)
        except Exception as e:
            print("copyAdjointShootdir problem:  " + str(e))
    # Preparing shooting directories from sweep1 data
    # with futures.ProcessPoolExecutor(max_workers=maxCPU) as executor:
    for i in range(n - k, 0, -1):  # (using i+1, we can only go to n)
        # #will become k + 1, n + 1 because of first loop being put into the big loop
        prepare_next_adjoint_sweep_starting_files(basepath, folder_name, previous_sweep_name, sweep_name, i)
        print("Test for " + "Previous sweep: " + previous_sweep_name + " and current sweep: " + sweep_name)
    sweep_name = sweep.format(k)


def prepare_time_folders(folder_name, sweep_name, k):
    for i in range(n - k, 0, -1):
        interval_name = interval.format(i)
        src_case = PRIMAL_PATH + folder_name + "/" + sweep_name + "/" + interval_name
        dest_case = ADJOINT_PATH + folder_name + "/" + sweep_name + "/" + interval_name
        for filename in os.listdir(src_case):
            if filename.startswith('0.'):
                try:
                    shutil.copytree(src_case + "/" + filename + "/", dest_case + "/-" + filename + "/")
                except Exception as e1:
                    print(e1)
            # if filename.startswith
        for filename in os.listdir(src_case):
            if not filename.startswith('0.'):
                if os.path.isdir(src_case + "/" + filename):
                    try:
                        shutil.copytree(src_case + "/" + filename + "/", dest_case + "/" + filename + "/")
                    except Exception as e1:
                        print(e1)
                else:
                    try:
                        shutil.copyfile(src_case + "/" + filename, dest_case + "/" + filename)
                    except Exception as e1:
                        print(e1)


def prepare_adjoint_defect_computation(basepath, sweep_name, interval_name, previous_interval, i):  # for computeDefect

    # Fetch shootingDefect from ref_Cases
    src_shooting_defect = REF_CASES_PATH + "shootingDefect/"
    dest_shooting_defect = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/"
    if os.path.exists(dest_shooting_defect):
        post.erase_adjoint_shooting_defect(ADJOINT_PATH, sweep_name, interval_name, i)
        try:
            shutil.rmtree(dest_shooting_defect)
        except Exception as e:
            print(str(e))

    shutil.copytree(src_shooting_defect, dest_shooting_defect)
    adjoint_starting_time = str(bc.decimal_analysis(-(theta + (i - 1) * deltaT)))
    adjoint_ending_time = str(bc.decimal_analysis(-(theta + (i - 1) * deltaT)))  # avant i

    # Fetch U, p, phi from current interval, Ua Starts with -0.5
    src_U = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/" + adjoint_starting_time + "/Ua"
    src_p = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/" + adjoint_starting_time + "/pa"
    src_phi = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/" + adjoint_starting_time + "/phia"

    dest_U = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/0/UaInit_right"
    dest_p = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/0/paInit_right"
    dest_phi = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/0/phiaInit_right"

    shutil.copyfile(src_U, dest_U)
    shutil.copyfile(src_p, dest_p)
    shutil.copyfile(src_phi, dest_phi)

    # Fetch U, p, phi from previous interval  (interval5)
    src_U = basepath + FOLDER_NAME + "/" + sweep_name + "/" + previous_interval + "/" + adjoint_ending_time + "/Ua"  # modif
    src_p = basepath + FOLDER_NAME + "/" + sweep_name + "/" + previous_interval + "/" + adjoint_ending_time + "/pa"  # modif
    src_phi = basepath + FOLDER_NAME + "/" + sweep_name + "/" + previous_interval + "/" + adjoint_ending_time + "/phia"  # modif

    dest_U = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/0/UaShootEnd"  # modif
    dest_p = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/0/paShootEnd"  # modif
    dest_phi = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/0/phiaShootEnd"  # modif

    shutil.copyfile(src_U, dest_U)  # same
    shutil.copyfile(src_p, dest_p)  # same
    shutil.copyfile(src_phi, dest_phi)  # same


#   ADJOINT LINEARIZATION PREPROCESSING

def copy_adjoint_linearization(basepath, folder_name, sweep_name, i, fvSchemes_path, fvSolution_path):
    interval_name = interval.format(i)
    # New Paths for linP and linU, taking the Newton Update into account:
    interval_name = interval.format(i)
    lin_p_path = REF_CASES_PATH + "/boundaryConditions/linPa0"
    lin_u_path = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/adjointShootingDefect/0/linUaDefect"

    start_time_dest = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        -(bc.decimal_analysis(theta + i * deltaT)))
    # print("Start for LIN COPY:" + str(start_time_dest))
    # Copy lin files
    shutil.copy2(lin_p_path, start_time_dest + "/linPa")
    shutil.copy2(lin_u_path, start_time_dest + "/linUa")

    # Copy fv files
    shutil.copy(fvSchemes_path, basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/system")
    shutil.copy(fvSolution_path, basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/system")

    # bc.check_existence(ref_cases + "/boundaryConditions/", "linU")


def prepare_next_adjoint_linearization(basepath, folder_name, k):
    if not os.path.exists(folder_name):
        print("ERROR: No such file or directory. Exiting Shooting Manager")
        sys.exit()
        # if k<=n:
    sweep_name = sweep.format(k)

    # Paths for lin and fv files, OLD paths without Newton Update
    fvSchemes_path = REF_CASES_PATH + "/controlBib/fvSchemes"
    fvSolution_path = REF_CASES_PATH + "/controlBib/fvSolution"

    # with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
    for i in range(n - 1, 0, -1):  # avant n-1
        #    executor.submit(copy_adjoint_linearization, basepath, folder_name, sweep_name, i, fvSchemes_path,
        #                    fvSolution_path)
        copy_adjoint_linearization(basepath, folder_name, sweep_name, i, fvSchemes_path, fvSolution_path)


def prepare_adjoint_newton_update(basepath, folder_name, sweep_name, k, interval_name, i):
    # Fetch shooting Update folder from postPro cases
    src_shoot_update = REF_CASES_PATH + "shootingDefect/"
    dest_shoot_update = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/adjointShootingUpdate/"
    if os.path.exists(dest_shoot_update):
        print("Replacing file")
        try:
            shutil.rmtree(dest_shoot_update)
        except Exception as e:
            print(e)
        try:
            post.erase_files(dest_shoot_update)
            os.rmdir(dest_shoot_update)
        except Exception as e:
            print(e)
    shutil.copytree(src_shoot_update, dest_shoot_update)

    # Fetch data from EndTime folder
    src_data = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        -(bc.decimal_analysis(theta + (i - 1) * deltaT)))
    print("EndTime Folder for " + interval_name + ":    " + str(-(bc.decimal_analysis(theta + (i - 1) * deltaT))))
    src_data_start = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/" + str(
        -(bc.decimal_analysis(theta + i * deltaT)))

    # Copy to shootingUpdate
    dest_data = basepath + folder_name + "/" + sweep_name + "/" + interval_name + "/adjointShootingUpdate/0/"
    shutil.copy(src_data + "/linUa", dest_data + "dUadua")
    shutil.copy(src_data + "/linUaf", dest_data + "dUaduaf")
    shutil.copy(src_data + "/linPa", dest_data + "dPadpa")
    shutil.copy(src_data + "/Ua", dest_data + "UaEnd_left")
    shutil.copy(src_data + "/pa", dest_data + "paEnd_left")
    shutil.copy(src_data + "/phia", dest_data + "phiaEnd_left")
    shutil.copy(src_data + "/Uaf", dest_data + "UafEnd_left")
    shutil.copy(src_data + "/Ua", dest_data + "shootingUpdateUa")
    shutil.copy(src_data + "/pa", dest_data + "shootingUpdatePa")
    shutil.copy(src_data + "/phia", dest_data + "shootingUpdatePhia")
    shutil.copy(src_data + "/Uaf", dest_data + "shootingUpdateUaf")

    # Fetching data for limitor
    shutil.copy(src_data_start + "/linUa", dest_data + "dUadua_Init")
    shutil.copy(src_data_start + "/linPa", dest_data + "dPadpa_Init")
