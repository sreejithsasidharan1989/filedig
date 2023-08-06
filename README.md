## FileDig
-----

##### What is FileDig
As the name implies, this Python script digs into various logs and finds out the log entries that correlate with the mtime of the given file. The script creates a time array for the inputted file that is within a +/- 10 seconds range, then it compares the logs with the array to check if there are any matches. Additionally, it creates a second array of mtimes for all files found in the same directory and its subdirectories and compares them to the mtime of the given file to see if any other files were modified simultaneously.

##### How to use the script
The script is currently configured to check for the following conditions:

1. The input must be at least a relative file path
2. The length of the "Current Working Directory" must be at least 4 because the path to its logs is determined using this value
3. The script uses several Python list to temporarily save the gathered data. If all of these lists are empty, it will not display any information other than the file stat info.

* **$ cd to the document root of the website**
```
cd /chroot/home/example/example.com/public_html
```
* **Find the file that you want to take a dig at and feed it to the script**
```
public_html]$ filedig index.php
```
* **If the target file is under one of the sub-directories, either cd to that location and run the script or use the relative path to that file**
```
public_html]$ filedig wp-includes/update.php
```

* **The script will print all available logs that correlate with the mtime of the file**
```
public_html]$ filedig wp-config.php

wp-config.php 

=================== FILE STAT ========================

File was last modified on:       2023-08-03T18:04:58

File was last accessed on:       2023-08-03T18:04:58

File inode was last modified on: 2023-08-03T18:04:58

Absolute File Path:              /chroot/home/example/example.com/public_html/wp-config.php

=================== LOG ENTRIES ===================

Below is a list of logs & files that correlate to the given file's mtime
Please be aware that the script only selects logs & files that are within
a +/-10 second range of the mtime value. Be sure to check other areas.

Logs from website's transfer log
================================

xx.xxx.xx.xxx -  [03/Aug/2023:18:05:00 +0000] "GET / HTTP/1.1" 200 57344 "-" "curl/7.68.0"

xx.xxx.xx.xxx -  [03/Aug/2023:18:05:00 +0000] "GET / HTTP/1.1" 200 57344 "-" "curl/7.68.0"

Files modified around the same time
====================================

 /chroot/home/example/example.com/public_html/wp-config.php
```
* **If try to run the script from an un-supposed location**
#
```
$ cd /chroot/home/example

$ filedig something.txt 

=================== FILE STAT ========================

File was last modified on:       2023-08-02T20:47:39

File was last accessed on:       2023-08-02T20:47:39

File inode was last modified on: 2023-08-02T20:47:39

Absolute File Path:              /chroot/home/example/something.txt

Something went wrong! Please re-run the script after cd 'ing to site's docroot!
```

* **If the argument is a non-existing file**
```
$ filedig fakefile.txt
=============== NOTICE ===============
Please make sure you've fed a relative filepath!!
```
