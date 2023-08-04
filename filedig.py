#!/bin/python3
import sys
import zipfile
import tarfile
import os
from pathlib import Path
import lzma
import time
import posixpath
import re

#Global-variables
DOMAIN = ''
USER = ''
CWD=''
T_FORMAT = []
S_FORMAT = []
Z_FORMAT = []

##########
## T_FORMAT  --> For storing timestamp in dd/mm/yyyyThh:mm:ss format
## S_FORMAT  --> For storing timestamp in dd/MM/yyyy:hh:mm:ss format
## Z_FORMAT  --> For storing timestamp in dd/mm/yyy:hh:mm:ss format
## T_RANGE  --> Holds times within a rage of +/- 10 seconds of the given file's mtime timestamp
##########

def statFile(AB_FILE):
    print("")
    print("=================== FILE STAT ========================\n")
    MTIME=time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(os.stat(AB_FILE).st_mtime))
    ATIME=time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(os.stat(AB_FILE).st_atime))
    CTIME=time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(os.stat(AB_FILE).st_ctime))
    print("{:33}{}\n".format("File was last modified on:",MTIME))
    print("{:33}{}\n".format("File was last accessed on:",ATIME))
    print("{:3} {}\n".format("File inode was last modified on:",CTIME))
    print("{:33}{}\n".format("Absolute File Path:",AB_FILE))

def getTimeRange(AB_FILE):
    T_FORMAT=[]
    S_FORMAT=[]
    Z_FORMAT=[]
    T_RANGE= []
    
    TIME=os.path.getmtime(AB_FILE)
    T_ARRAY=time.localtime(TIME)
    year,month,day,hour,minute,second=time.localtime(TIME)[:-3]
    TIMESTAMP="%02d/%02d/%4d:%02d:%02d:%02d"%(day,month,year,hour,minute,second)
    T_LOW=time.mktime((year,month,day,hour,minute,second - 10,T_ARRAY.tm_wday,T_ARRAY.tm_yday,T_ARRAY.tm_isdst))
    T_MAX=time.mktime((year,month,day,hour,minute,second + 10,T_ARRAY.tm_wday,T_ARRAY.tm_yday,T_ARRAY.tm_isdst))
    
    C_TIME = T_LOW
    while C_TIME <= T_MAX:
        T_RANGE.append(C_TIME)
        C_TIME += 1
    
    for times in T_RANGE:
        T_S = time.localtime(times)
        T_FORMAT.append(time.strftime('%Y-%m-%dT%H:%M:%S', T_S))
        S_FORMAT.append(time.strftime('%d/%b/%Y:%H:%M:%S', T_S))
        Z_FORMAT.append(time.strftime('%d/%b/%Y:%H:%M:%S', T_S))
    return T_FORMAT,S_FORMAT,Z_FORMAT

def LogDigger(T_FORMAT,S_FORMAT,Z_FORMAT,PATH):
    LogArray= []
    TLogDig = []
    XLogDig = []
    SLogDig = []
    LogDig  = []
    F_PATH  =''
    LogPath = [PATH,"/var/log/","/var/log/proftpd/"]
    for path in LogPath:
        for Files in os.walk(path):
            curDir = Files[0]
            subDirs = Files[1]
            subFiles = Files[2]
            for files in subFiles:
                if "secure" in files or "xfer" in files or "transfer" in files:
                    F_PATH=posixpath.join(curDir,files)
                    LogArray.append(F_PATH)

    for log in LogArray:
        if 'xfer' in log:
            if '.xz' in log:
                R_OPEN=lzma.open(log,'rt', encoding='iso-8859-1')
            else:
                R_OPEN = open(log,'r')
            for lines in R_OPEN:
                match = re.search("\d{2}\/\w{3}\/\d{4}\:\d{2}\:\d{2}\:\d{2}", lines)
                if match is not None:
                    logLine = match.group()
                    if logLine in S_FORMAT:
                        XLogDig.append(lines)
                    
        if 'transfer' in log:
            if '.zip' in log:
                R_OPEN = zipfile.ZipFile(log, 'r')
                for name in R_OPEN.namelist():
                    F_OPEN = R_OPEN.open(name)
                    for line in F_OPEN:
                        decoded_line = line.decode('utf-8').strip()
                        match = re.search("\d{2}\/\d{2}\/\d{4}\:\d{2}\:\d{2}\:\d{2}", decoded_line)
                        if match is not None:
                            logLine = match.group()
                            if logLine in Z_FORMAT:
                                TLogDig.append(decoded_line)
     
            else:
                R_OPEN = open(log,'r')
                for lines in R_OPEN:
                    match = re.search(r"\d{2}\/\w{3}\/\d{4}\:\d{2}\:\d{2}\:\d{2}", lines)
                    if match is not None:
                        logLine = match.group()
                        if logLine in Z_FORMAT:
                            TLogDig.append(lines)
        
        if 'secure' in log:
            if '.xz' in log:
                R_OPEN=lzma.open(log,'rt')
            else:
                R_OPEN = open(log,'r')
            for lines in R_OPEN:
                match = re.search(r"\d{4}\-\d{2}\-\d{2}T\d{2}\:\d{2}\:\d{2}", lines)
                if match is not None:
                    logLine = match.group()
                    if logLine in T_FORMAT:
                        SLogDig.append(lines)
                        
    return XLogDig,TLogDig,SLogDig

def LogPathResolver():
    length = 0
    PATH=''
    CWD = str(Path.cwd())
    try:
        if len(Path.cwd().parts) >= 4:
            DOMAIN = Path.cwd().parts[4]
            USER = Path.cwd().parts[3]
        else:
            print("Please re-run the script after cd 'ing to site's docroot!")
            exit()

        items = Path.cwd().parts
        length = len(items)
        if length >= 3:
            PATH = '/'.join(items[1:4])
        else:
            PATH = '/'.join(items)
    except:
        print("Something went wrong! Please re-run the script after cd 'ing to site's docroot!")
    sys.stderr = object
    return f"/{PATH}/var/{DOMAIN}/logs/"

def FileChainer():
    
    TIMESTAMP = ''
    FileDict = {}
    M_ARRAY = []
    
    for files in os.walk(CWD):
        curDir = files[0]
        subDir = files[1]
        subFiles = files[2] 
        for subFile in subFiles:
            absPath = posixpath.join(curDir,subFile)
            if absPath.endswith(".php") or absPath.endswith(".js"):
                TIME = os.path.getmtime(absPath)
                year,month,day,hour,minute,second=time.localtime(TIME)[:-3]
                TIMESTAMP="%02d/%02d/%4d:%02d:%02d:%02d"%(day,month,year,hour,minute,second)
                if subFile not in FileDict:
                    FileDict[subFile] = [TIMESTAMP,absPath]

    for item in FileDict:
        if FileDict[item][0] in Z_FORMAT:
            M_ARRAY.append(FileDict[item][1])
        
    return M_ARRAY

args = sys.argv[1:]

if len(args) == 1:
    PATH = Path(args[0])
    if PATH.is_file() == 0:
        print("=============== NOTICE ===============\n")
        print("Please make sure you've fed a relative filepath!!")
        exit()
        
    AB_FILE = PATH.resolve()
    statFile(AB_FILE)
    TLogDig,SLogDig,ZLogDig = getTimeRange(AB_FILE)
    L_PATH = LogPathResolver()
    XLogDig,TLogDig,SLogDig = LogDigger(T_FORMAT,S_FORMAT,Z_FORMAT,L_PATH)
    
    print("=================== LOG ENTRIES ===================\n")
    print("Below is a list of logs that correlate to the given file's mtime")
    print("Please be aware that this script only selects logs that are within")
    print("a +/-10 second range of the mtime value.\n")
    
    if len(TLogDig) > 0:
        print("Logs from website's transfer log")
        print("================================\n")
        for lines in TLogDig:
            print(f"{lines}\n")
            
    elif len(SLogDig) > 0:
        print("Entries from SFTP log")
        print("=====================\n")
        for lines in XLogDig:
            print(f"{lines}\n")
            
    elif len(ZLogDig) > 0:
        print("Entries from FTP log")
        print("====================\n")
        for lines in SLogDig:
            print(f"{lines}\n")
            
    FC_ARRAY = FileChainer()
    if len(FC_ARRAY) > 0:
        
            