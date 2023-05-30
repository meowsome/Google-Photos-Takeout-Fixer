# Google Photos Takeout Fixer

## The Problem
Google Takeout exports photos from Google Photos with the metadata separated. When trying to view these photos using photo viewing software, the metadata, such as location, time, and camera information, are not shown on the photo.

## The Solution
This script goes through each folder and searches for the metadata for each photo that has been separated. The tool then adds the data back to the file and sends it to the output folder.

1. Visit [https://takeout.google.com](takeout.google.com)
2. Deselect everything except Google Photos
3. Within the Google Photos dropdown, filter by which photos you want downloaded
4. Download the zips and unzip them
5. Drop all unzipped takeout folders into the folder takeout_folders (should be named takeout-xxxx)
6. Run fix.py

Supports file extensions: jpg, jpeg, png, mov, mp4

If a file has no available metadata, nothing will be changed to the file, but it still still be processed to the output folder. 