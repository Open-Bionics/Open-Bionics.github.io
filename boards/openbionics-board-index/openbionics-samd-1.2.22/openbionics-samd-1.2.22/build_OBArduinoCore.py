import fileinput
import hashlib
import json
import os
import re
from shutil import copytree, ignore_patterns, make_archive

##
# This script will copy the 'OB_arduino_core_samd' files to the 'GitHub.io' repo, package
# them in a zip folder with the version number and update the 'package_openbionics_index.json'
# file with the correct information.
#
# This script uses absolute paths, however this should be portable so long as you change
# the 'git_path' to point to your local GitHub directory. This directory must contain the
# following Open Bionics repo's:
#   - OB_arduino_core_samd          (https://github.com/Open-Bionics/OB_arduino_core_samd)
#   - Open-Bionics.github.io        (https://github.com/Open-Bionics/Open-Bionics.github.io)
##

# File Dir
git_path = "F:\\GitHub\\"                                           # path of the local GitHub directory
src_path = git_path + "OB_arduino_core_samd\\"                      # path of the ob-samd-core to be packaged
ver_path = src_path + "version.txt"                                 # path of txt file containing version string
io_path = git_path + "Open-Bionics.github.io\\"                     # path of the GitHub.io repo to store package
zip_dst_path = io_path + "boards\\"                                 # path to store the zip file
dst_path = zip_dst_path + "openbionics-board-index\\"               # path to store a copy of the ob-samd-core
json_path = io_path + "package_openbionics_index.json"              # path of the arduino package json

# Regex Patterns
ver_patt = re.compile("^(\d+)\.(\d+).(\d+)$")                       # regex pattern of the version string


# Get the version string from a version.txt file
def get_version(src):
    major = 0
    minor = 0
    patch = 0
    f = open(src, "r")
    for line in f:
            match = ver_patt.match(line)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                patch = int(match.group(3))
    f.close()
    return major, minor, patch


# Get the SHA256 of a file
def get_hash(src):
    sha256_hash = hashlib.sha256()
    with open(src,"rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    f.close()
    return sha256_hash.hexdigest()


# Generate the package JSON string with correct formatting/indent
def get_json_str(maj, min, pat, fname, hash, size):
    json_obj = {
        "name": "Open Bionics Boards",
        "architecture": "samd",
        "version": str(maj) + "." + str(min) + "." + str(pat),
        "category": "Contributed",
        "url": "https://open-bionics.github.io/boards/" + fname,
        "archiveFileName": fname,
        "checksum": "SHA-256:" + hash.upper(),
        "size": str(size),
        "boards": [
            {"name": "Chestnut"},
            {"name": "OB1 Hand Controller"},
            {"name": "OB1 Hand Controller - Shifted"}
        ],
        "toolsDependencies": [
                        {
              "packager": "arduino",
              "name": "arm-none-eabi-gcc",
              "version": "4.8.3-2014q1"
            },
            {
              "packager": "arduino",
              "name": "bossac",
              "version": "1.7.0"
            },
            {
              "packager": "arduino",
              "name": "openocd",
              "version": "0.9.0-arduino6-static"
            },
            {
              "packager": "arduino",
              "name": "CMSIS",
              "version": "4.5.0"
            },
            {
              "packager": "arduino",
              "name": "CMSIS-Atmel",
              "version": "1.1.0"
            },
            {
              "packager": "arduino",
              "name": "arduinoOTA",
              "version": "1.2.0"
            }
        ]
    }

    json_str = json.dumps(json_obj, indent=4)
    json_str = re.sub("^", "\t\t", json_str, flags=re.M)

    return json_str


print("Started")

# get version number
ver_major, ver_minor, ver_patch = get_version(ver_path)
print("Package Version: V" + str(ver_major) + "." + str(ver_minor) + "." + str(ver_patch))

# generate new folder using version number
folder_name = "openbionics-samd-" + str(ver_major) + "." + str(ver_minor) + "." + str(ver_patch)
dst_path = dst_path + folder_name

# If the folder already exists, throw error and stop
if os.path.isdir(dst_path) and os.path.exists(dst_path):
    print("ERROR - Folder '" + folder_name + "' already exists at '" + dst_path + "'")
else:

    # Copy from src to destination folder with version number (do not copy src .git dir)
    # Make nested subfolders of same name due to Arduino package standard
    print("Copying to '" + folder_name + "'...", end="")
    copytree(src_path, dst_path + "\\" + folder_name + "\\", ignore=ignore_patterns('.git'))
    print("Complete")

    # Zip the folder
    print("Zipping file...", end="")
    make_archive(zip_dst_path + folder_name, 'zip', dst_path)
    zip_name = folder_name + ".zip"
    zip_path = zip_dst_path + zip_name
    print("Complete")

    # Compute size and hash of the zip file
    size = os.path.getsize(zip_path)
    file_hash = get_hash(zip_path)

    # Generate the JSON string to be inserted into the package JSON file
    json_str = get_json_str(ver_major, ver_minor, ver_patch, zip_name, file_hash, size)

    # Insert the JSON string into the package JSON file
    print("Modifying JSON package...", end="")
    for line in fileinput.FileInput(json_path, inplace=1):
        if "\"platforms\": [\n" in line:
            line = line.replace(line, line + "\n" + json_str + ",\n")
        print(line, end="")
    print("Complete")

print("Finished")
input("\nPress enter to exit...")

quit()
