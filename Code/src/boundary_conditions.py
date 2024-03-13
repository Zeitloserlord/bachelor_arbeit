# -*- coding: utf-8 -*-
"""
Created on Mon Apr 17 17:05:09 2023

@author: jcosson

edited December 2023
by jwrage
"""
import fileinput
import os
import shutil
import sys
from concurrent import futures

from config import CALCS_UNDEFORMED_PATH, REF_CASES_PATH, REF_MOD_DEF_PATH
from config import n, theta, deltaT, interval, sweep, FOLDER_NAME, MAX_CPU


# analysis of how many decimals my number has : 1, 2 ou 3 decimals
def decimal_analysis(number):
    if number * 10 % 10 == 0:
        return round(number, 2)
    else:
        return round(number, 3)


#  PRIMAL PRIMITIVE INITIALIZATIONS
def sweep_1_initialization(basepath, folder_name):
    # Fetch all the files from src directories and modify them for the specific case : constant,
    # system, start_time_dir, polyMesh, controlDict
    # k=1
    os.chdir(basepath)
    os.mkdir(folder_name)
    sweep_name = sweep.format(1)
    sweep_path = os.path.join(folder_name, sweep_name)
    os.mkdir(sweep_path)
    print("\nThe directory " + folder_name + " has been created at this place: \n" + basepath + "\n\n")
    with futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for i in range(1, n + 1):
            executor.submit(zero_sweep1_initialization, basepath, sweep_name, i)
    os.chdir(basepath + folder_name)
    with open("pressureDropvalues.txt", "w") as log_time:
        log_time.write(
            "\n\n=============================================================================\n\n"
            + "                         LOGFILE " + folder_name
            + "\n\n=============================================================================\n\n")
    log_time.close()
    print("Sweep 1 initialization is done.")
    os.chdir(basepath)


def loop_sweep1_initialization(basepath, sweep_name, i):  # Copy function for sweep1_initialization
    interval_name = interval.format(i)

    # Fetching Directory constant
    source_constant = CALCS_UNDEFORMED_PATH + 'constant'
    destination_constant = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name
    shutil.copytree(source_constant, os.path.join(destination_constant, os.path.basename(source_constant)))

    # Fetching Directory system
    source_system = CALCS_UNDEFORMED_PATH + 'system'
    destination_system = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name
    shutil.copytree(source_system, os.path.join(destination_system, os.path.basename(source_system)))

    # Fetching Directory with starting time
    startTime = decimal_analysis(theta + deltaT * (i - 1))
    endTime = decimal_analysis(theta + deltaT * i)
    source_start_time = CALCS_UNDEFORMED_PATH + str(startTime)
    destination_start_time = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name
    shutil.copytree(source_start_time, os.path.join(destination_start_time, os.path.basename(source_start_time)))

    # Deleting wrong polyMesh/points in the starting time directory
    poly_mesh_path = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + '/constant/polyMesh/points'
    os.remove(poly_mesh_path)
    file = destination_start_time + '/' + str(startTime) + '/polyMesh/points'
    if os.path.exists(file):
        shutil.rmtree(destination_start_time + '/' + str(startTime) + '/polyMesh')

    # Fetching the right polyMesh
    source_new_poly_mesh = REF_MOD_DEF_PATH + "constant/polyMesh/points"
    destination_new_poly_mesh = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + '/constant/polyMesh'
    shutil.copy(source_new_poly_mesh, destination_new_poly_mesh)

    # Modify the controlDict file to adjust startTime and endTime
    control_dict_path = FOLDER_NAME + '/' + sweep_name + '/' + interval_name + '/system/controlDict'
    for line in fileinput.input(control_dict_path, inplace=True):
        if line.startswith('startTime'):
            line = 'startTime       {};\n'.format(startTime)
        elif line.startswith('endTime'):
            line = 'endTime         {};\n'.format(endTime)
        print(line)


def zero_sweep1_initialization(basepath, sweep_name, i):  # Copy function for sweep1_initialization
    interval_name = interval.format(i)

    # Fetching Directory constant
    source_constant = CALCS_UNDEFORMED_PATH + 'constant'
    destination_constant = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name
    shutil.copytree(source_constant, os.path.join(destination_constant, os.path.basename(source_constant)))

    # Fetching Directory system
    source_system = CALCS_UNDEFORMED_PATH + 'system'
    destination_system = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name
    shutil.copytree(source_system, os.path.join(destination_system, os.path.basename(source_system)))

    # Fetching Directory with starting time
    startTime = decimal_analysis(theta + deltaT * (i - 1))
    endTime = decimal_analysis(theta + deltaT * i)
    source_start_time = CALCS_UNDEFORMED_PATH + str(startTime)
    destination_start_time = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name
    shutil.copytree(source_start_time, os.path.join(destination_start_time, os.path.basename(source_start_time)))
    if i > 1:
        shutil.copy(REF_CASES_PATH + "moderate_deformed_SDuct/0/U",
                    os.path.join(destination_start_time, os.path.basename(source_start_time)))
        shutil.copy(REF_CASES_PATH + "moderate_deformed_SDuct/0/p",
                    os.path.join(destination_start_time, os.path.basename(source_start_time)))

        # Deleting wrong polyMesh/points in the starting time directory
    poly_mesh_path = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + '/constant/polyMesh/points'
    os.remove(poly_mesh_path)
    file = destination_start_time + '/' + str(startTime) + '/polyMesh/points'
    if os.path.exists(file):
        shutil.rmtree(destination_start_time + '/' + str(startTime) + '/polyMesh')

    # Fetching the right polyMesh
    source_new_poly_mesh = REF_MOD_DEF_PATH + "constant/polyMesh/points"
    destination_new_poly_mesh = basepath + FOLDER_NAME + "/" + sweep_name + "/" + interval_name + '/constant/polyMesh'
    shutil.copy(source_new_poly_mesh, destination_new_poly_mesh)

    # Modify the controlDict file to adjust startTime and endTime
    control_dict_path = FOLDER_NAME + '/' + sweep_name + '/' + interval_name + '/system/controlDict'
    for line in fileinput.input(control_dict_path, inplace=True):
        if line.startswith('startTime'):
            line = 'startTime       {};\n'.format(startTime)
        elif line.startswith('endTime'):
            line = 'endTime         {};\n'.format(endTime)
        print(line)


#  SOME RANDOM USEFUL FUNCTIONS
def copytree(src, dst, symlinks=False, ignore=None):
    """
    This is an improved version of shutil.copytree which allows writing to
    existing folders and does not overwrite existing files but instead appends
    a ~1 to the file name and adds it to the destination path.
    """

    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)
        shutil.copystat(src, dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        i = 1
        while os.path.exists(dstname) and not os.path.isdir(dstname):
            parts = name.split('.')
            file_name = ''
            file_extension = parts[-1]
            # make a new file name inserting ~1 between name and extension
            for j in range(len(parts) - 1):
                file_name += parts[j]
                if j < len(parts) - 2:
                    file_name += '.'
            suffix = file_name + '~' + str(i) + '.' + file_extension
            dstname = os.path.join(dst, suffix)
            i += 1
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except BaseException as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise BaseException(errors)


def check_existence(parent_directory, parameter):
    # Get a list of all directories within the parent directory
    subdirectories = [folder for folder in os.listdir(parent_directory) if
                      os.path.isdir(os.path.join(parent_directory, folder))]

    # Iterate over each subdirectory that starts with "0."
    for subdirectory in subdirectories:
        if subdirectory.startswith("0."):
            # Construct the file path within the subdirectory
            file_path = os.path.join(parent_directory, subdirectory, parameter)

            # Check if the file exists
            if os.path.isfile(file_path):
                print("The file '" + parameter + "' exists in the folder " + subdirectory + ".")
            else:
                print("The file '" + parameter + "' does not exist in the folder " + subdirectory + ".")


def checking_existence(basepath, folder_name):
    if os.path.exists(basepath + folder_name):
        ans = input(
            "WARNING: Directory " + basepath + folder_name
            + " already exists. Do you want to replace it ? (Y/N)     \n   \n")
        if ans == "Y" or ans == "y":
            print("Deleting files...\n")
            for g in range(1, n + 1):
                if os.path.exists("sweep" + str(g)):
                    shutil.rmtree("sweep" + str(g))
            shutil.rmtree(basepath + folder_name)

        else:
            sys.exit()
    return folder_name


def timer_and_write(basepath, elapsed_time, function, sweep_name):
    num_minutes = int(elapsed_time / 60)
    num_seconds = elapsed_time % 60
    time = []
    # Function write_time        
    os.chdir(basepath + FOLDER_NAME)
    with open("pressureDropvalues.txt", "a") as write_time:
        time_pimple = "\nElapsed time for " + function + " in " + sweep_name + ": " + str(
            round(num_minutes, 2)) + " minutes and " + str(round(num_seconds, 3)) + " seconds.\n"
        write_time.write(time_pimple)
        print(time_pimple)
    write_time.close()

    with open(function + "_times.txt", "a") as timelog:
        # writer = csv.writer(timelog)
        time = time.append(elapsed_time)
        timelog.write(str(elapsed_time) + "\n")
        # writer.writerows(time)
    timelog.close()
    os.chdir(basepath)  # back to main path
