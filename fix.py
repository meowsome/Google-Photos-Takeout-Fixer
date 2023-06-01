from concurrent.futures import ThreadPoolExecutor, as_completed
from exiftool import ExifToolHelper
from exiftool.exceptions import ExifToolExecuteError
import json
from datetime import datetime
import shutil
import math
import os
from tqdm import tqdm
import re

# Empty or create relevant folders
for path in ["output", "failures"]:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)

if not os.path.exists("takeout_folders"):
    os.mkdir("takeout_folders")

failures = []

# https://stackoverflow.com/a/52371976/3675086
def deg_to_ref(deg, kind='lat'):
    decimals, number = math.modf(deg)
    d = int(number)
    compass = {
        'lat': ('N','S'),
        'lon': ('E','W')
    }
    return compass[kind][0 if d >= 0 else 1]

def attach_metadata(filepath):
    filename = filepath.split("/")[-1]
    # Attempt to find metadata for this file
    try:
        with open(f'{filepath}.json') as json_file:
            metadata = json.load(json_file)
    except FileNotFoundError:
        # If no metadata found, just raw copy to the output folder
        shutil.copyfile(filepath, f'output/{filename}')
    else:
        timestamp_raw = int(metadata['photoTakenTime']['timestamp'])
        timestamp = datetime.utcfromtimestamp(timestamp_raw).strftime("%Y:%m:%d %H:%M:%S")

        tags = {"DateTimeOriginal": timestamp}
        
        # Only add lat and lon to metadata if they are available from original photo 
        if metadata['geoData']['latitude'] != 0.0 and metadata['geoData']['longitude'] != 0.0:
            tags['GPSLatitude'] = metadata['geoData']['latitude']
            tags['GPSLatitudeRef'] = deg_to_ref(tags['GPSLatitude'])
            tags['GPSLongitude'] = metadata['geoData']['longitude']
            tags['GPSLongitudeRef'] = deg_to_ref(tags['GPSLongitude'], kind='lon')

        # Set all metadata tags and export
        try:
            with ExifToolHelper() as et:
                et.set_tags(
                    [filepath],
                    tags=tags,
                    params=["-o", f"output/{filename}"] # Specify output file 
                )
        except ExifToolExecuteError:
            shutil.copyfile(filepath, f'failures/{filename}')
        else:
            # Set last modified for file to correct date
            os.utime(f"output/{filename}", (timestamp_raw, timestamp_raw))
                
os.chdir("takeout_folders") # Start at this folder

all_files = []

# Iterate through each available folder 
for folder in os.listdir():
    backwards_traverse = "../"
    backup_folder = ""
    
    # Traverse down extra paths if necessary to get to year folders 
    if os.path.exists(f'{folder}/Takeout'):
        backup_folder = f"{folder}/Takeout/Google Photos"
        os.chdir(backup_folder)
        backwards_traverse = "../../../"

    # Fetch all exported photo folders
    photo_folders = [folders[1] for folders in os.walk("./")][0]
    
    for photo_folder in photo_folders:
        os.chdir(photo_folder) # Go to folder

        # Fetch all image/video types in this folder, ensure not to match .json 
        search_re = r'.*\.(jpg|jpeg|png|mov|mp4)$'
        all_files += [f"takeout_folders/{backup_folder}/{photo_folder}/{file}" for file in os.listdir() if re.search(search_re, file.lower(), re.IGNORECASE)]

        os.chdir("../") # Go up a folder to prepare for the next folder
    os.chdir(backwards_traverse) # Go up to the takeout_folders directory

os.chdir("../") # Go up to the project main directory

cores = os.cpu_count() / 3
with tqdm(total=len(all_files)) as pbar:
    with ThreadPoolExecutor(max_workers=cores) as ex:
        futures = [ex.submit(attach_metadata, file) for file in all_files]
        for future in as_completed(futures):
            result = future.result()
            pbar.update(1)

# TODO Why does this file fail IMG_2113.PNG 