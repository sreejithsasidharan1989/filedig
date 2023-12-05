#!/usr/bin/python3
import sys
import zipfile
import tarfile
import os
from pathlib import Path
import lzma
import time
import posixpath
import re
import shutil
import subprocess
import filecmp

#Global-variables
PATH = ''
DOMAIN = ''
USER = ''
CWD=''
IFLAG = 0
T_FORMAT = []
S_FORMAT = []
Z_FORMAT = []
POSTLOG  = []
NORMALOG = []

##########
## T_FORMAT  --> For storing timestamp in dd-mm-yyyyThh:mm:ss format 01-08-2023T19:30:45
## S_FORMAT  --> For storing timestamp in dd/MM/yyyy:hh:mm:ss format 01/Aug/2023:19:30:45
## Z_FORMAT  --> For storing timestamp in dd/mm/yyy:hh:mm:ss format  01/80/2023:19:30:45
## T_RANGE  --> Holds times within a rage of +/- 10 seconds of the given file's mtime timestamp
##########

def statFile(AB_FILE):
    try:
        print('\033[1m'+"=================== FILE STAT ========================\n"+'\033[0m')
        MTIME=time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(os.stat(AB_FILE).st_mtime))
        ATIME=time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(os.stat(AB_FILE).st_atime))
        CTIME=time.strftime('%Y-%m-%dT%H:%M:%S',time.localtime(os.stat(AB_FILE).st_ctime))
        print("{:33}{}\n".format("File was last modified on:",MTIME))
        print("{:33}{}\n".format("File was last accessed on:",ATIME))
        print("{:3} {}\n".format("File inode was last modified on:",CTIME))
        print("{:33}{}\n".format("Absolute File Path:",AB_FILE))
    except FileNotFoundError:
        pass

def getTimeRange(AB_FILE,IFLAG):
    T_FORMAT=[]
    S_FORMAT=[]
    Z_FORMAT=[]
    T_RANGE= []
    if IFLAG==1:
        TIME=os.path.getctime(AB_FILE)
    elif IFLAG==2:
        TIME=os.path.getatime(AB_FILE)
    else:
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
        Z_FORMAT.append(time.strftime('%d/%m/%Y:%H:%M:%S', T_S))
    return T_FORMAT,S_FORMAT,Z_FORMAT

def LogDigger(T_FORMAT,S_FORMAT,Z_FORMAT,PATH):
    User=PATH.split('/')[3]
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
                R_OPEN = lzma.open(log,'rt', encoding='iso-8859-1')
            else:
                R_OPEN = open(log,"r", errors='ignore')
            for xlines in R_OPEN:
                match = re.search("\d{2}\/\w{3}\/\d{4}\:\d{2}\:\d{2}\:\d{2}", xlines)
                if match is not None:
                    logLine = match.group()
                    if logLine in S_FORMAT:
                        XLogDig.append(xlines)
                    
        elif 'transfer' in log:
            if 'zip' in log:
                 R_OPEN = zipfile.ZipFile(log, 'r')
                 for name in R_OPEN.namelist():
                     F_OPEN = R_OPEN.open(name)
                     for Tline in F_OPEN:
                         decoded_line = Tline.decode('utf-8').strip()
                         match = re.search("\d{2}\/\w{3}\/\d{4}\:\d{2}\:\d{2}\:\d{2}", decoded_line)
                         if match is not None:
                             logLine = match.group()
                             if logLine in S_FORMAT:
                                 TLogDig.append(decoded_line)
     
            else:
                R_OPEN = open(log,'r', errors='ignore')
                for Tlines in R_OPEN:
                    match = re.search(r"\d{2}\/\w{3}\/\d{4}\:\d{2}\:\d{2}\:\d{2}", Tlines)
                    if match is not None:
                        logLine = match.group()
                        if logLine in S_FORMAT:
                            TLogDig.append(Tlines)
        
        elif 'secure' in log:
             if '.xz' in log:
                R_OPEN=lzma.open(log,'rt')
             else:
                 R_OPEN = open(log,'r', errors='ignore')
                 for Slines in R_OPEN:
                     match = re.search(r"\d{4}\-\d{2}\-\d{2}T\d{2}\:\d{2}\:\d{2}", Slines)
                     if match is not None:
                         logLine = match.group()
                         if logLine in T_FORMAT and User in Slines:
                             SLogDig.append(Slines)
                        
    return XLogDig,TLogDig,SLogDig

def LogPathResolver(AB_FILE):
    length = 0
    PATHS=''
    try:
        if len(AB_FILE.parts) >= 4:
            DOMAIN = AB_FILE.parts[4]
            USER = AB_FILE.parts[3]
        else:
            print("Please re-run the script after cd 'ing to site's docroot!")
            exit()

        items = AB_FILE.parts
        length = len(items)
        if length >= 3:
            PATHS = '/'.join(items[1:4])
        else:
            PATHS = '/'.join(items)
    except:
        print("Something went wrong! Please re-run the script after cd 'ing to site's docroot!")
    sys.stderr = object
    return f"/{PATHS}/var/{DOMAIN}/logs/",f"/{PATHS}/{DOMAIN}"

def FileChainer(CWD,Z_FORMAT):
    TIMESTAMP = ''
    FileDict = {}
    M_ARRAY = []
    subCount = 0
    for files in os.walk(CWD):
        curDir = files[0]
        subDir = files[1]
        subFiles = files[2]
        for subFile in subFiles:
            absPath = posixpath.join(curDir,subFile)
            TIME = os.path.getmtime(absPath)
            year,month,day,hour,minute,second=time.localtime(TIME)[:-3]
            TIMESTAMP="%02d/%02d/%4d:%02d:%02d:%02d"%(day,month,year,hour,minute,second)
            if subFile not in FileDict:
                FileDict[subFile] = [TIMESTAMP,absPath]
            else:
                FileDict[subFile + str(subCount)] = [TIMESTAMP,absPath]
                subCount += 1
    for Ditem in FileDict:
        if FileDict[Ditem][0] in Z_FORMAT:
            M_ARRAY.append(FileDict[Ditem][1])

    return M_ARRAY

def LogPrinter(TLogDig,SLogDig,XLogDig):
    if len(TLogDig) > 0 or len(SLogDig) > 0 or len(XLogDig) > 0:
        print('\033[1m'+"=================== LOG ENTRIES ===================\n")
        print("Below is a list of logs & files that correlate to the given file's mtime")
        print("Please be aware that the script only selects logs & files that are within")
        print("a +/-10 second range of the mtime value. Be sure to check other areas.\n"+'\033[0m')
        if len(TLogDig) > 0:
            print("====================================")
            print("║ "+'\033[1m'+"Logs from website's transfer log"+'\033[0m'+" ║")
            print("====================================\n")
            for lines in TLogDig:
                if 'POST' in lines:
                    POSTLOG.append(lines)
                else:
                    NORMALOG.append(lines)

            if len(POSTLOG) > 0:
                print("Log entries with "+'\033[1;31m'+"POST "+'\033[0m'+"request")
                print("=============================\n")
                for item in POSTLOG:
                    print(item)
                print("\n================================\n")
            for item in NORMALOG:
                print(item)

        if len(SLogDig) > 0:
            print("Entries from SFTP log")
            print("=====================\n")
            for lines in SLogDig:
                print(f"{lines}\n")

        if len(XLogDig) > 0:
            print("Entries from FTP log")
            print("====================\n")
            for lines in XLogDig:
                print(f"{lines}\n")

    else:
        print('\033[1m'+"=================== NO RELEVANT LOGS FOUND! ===================\n"+'\033[0m')

def __update():
   local_filedig=os.path.realpath(__file__)
   os.chdir(Path.home())
   subprocess.run(["git", "clone", "https://github.com/sreejithsasidharan1989/filedig","Filedig"],stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
   clone_filedig=posixpath.join(Path.home(),'Filedig/filedig.py')
   if filecmp.cmp(local_filedig, clone_filedig, shallow=False):
       shutil.rmtree('Filedig')
   else:
       print('\033[42m'+"Note: This script may have a new update!"+'\33[0m')
       shutil.rmtree('Filedig')

def __helper():

    print('\033[1m'+"\n=================== HELP!  ===================\n")
    print("Feed a relative file path to the script as an argument to")
    print("view logs that align with the file's Modification timestamp\n")
    print("Example"+'\33[0m')
    print("========\n")
    print("{:30}".format("~/filedig wp-content/plugins/hello/index.php"))
    print("This will print any logs that correlates with the mtime of wp-content/plugins/hello/index.php")
    print("\n")
    print("To view other files that share a similar mtime, add -stat to to the above command\n")
    print('\33[1m'+"Example"+'\33[0m')
    print("========\n")
    print("{:30}".format("~/filedig wp-content/plugins/hello/index.php -stat"))
    print("This will print list of files that correlate with the mtime of wp-content/plugins/hello/index.php\n")
    print("{:30}".format("~/filedig wp-content/plugins/hello/index.php -C"))
    print("This will match the C-Time of the given file against the logs rather than using its M-Time\n")
    print("{:30}".format("~/filedig wp-content/plugins/hello/index.php -A"))
    print("This will match the A-Time of the given file against the logs rather than using its M-Time\n")
    exit()

try:
    args = sys.argv[1:]
    PATH = Path(args[0])

except:
    print("Something Went Wrong! Try again!")
    __helper()

AB_FILE = PATH.resolve()
    
__update()

if len(args) == 1:
    if '-h' in args[0] and len(args[0]) == 1:
        __helper()
    if AB_FILE.is_file() == 0 and '-h' not in args:
        print('\033[1m'+"\n=============== NOTICE ==============="+'\033[0m')
        print("Please make sure you're using a relative filepath!!\n")
        exit()
    statFile(AB_FILE)
    T_FORMAT,S_FORMAT,Z_FORMAT = getTimeRange(AB_FILE,IFLAG)
    L_PATH,CWD = LogPathResolver(AB_FILE)
    XLogDig,TLogDig,SLogDig = LogDigger(T_FORMAT,S_FORMAT,Z_FORMAT,L_PATH)
    LogPrinter(TLogDig,SLogDig,XLogDig)

elif len(args) == 2:
    if '-stat' in args[1]:
         statFile(AB_FILE)
         T_FORMAT,S_FORMAT,Z_FORMAT = getTimeRange(AB_FILE,IFLAG)
         L_PATH,CWD = LogPathResolver(AB_FILE)
         FC_ARRAY = FileChainer(CWD,Z_FORMAT)
         if len(FC_ARRAY) > 0:
            print('\033[1m'+"Files modified around the same time")
            print("====================================\n"+'\033[0m')
            for items in FC_ARRAY:
                print(items+"\n")
    elif '-C' in args[1]:
        if AB_FILE.is_file() == 0:
            print('\033[1;31m'+"Invalid File Path!"+'\033[0m')
            exit()
        IFLAG=1
        statFile(AB_FILE)
        T_FORMAT,S_FORMAT,Z_FORMAT = getTimeRange(AB_FILE,IFLAG)
        L_PATH,CWD = LogPathResolver(AB_FILE)
        XLogDig,TLogDig,SLogDig = LogDigger(T_FORMAT,S_FORMAT,Z_FORMAT,L_PATH)
        LogPrinter(TLogDig,SLogDig,XLogDig)
    elif '-A' in args[1]:
        if AB_FILE.is_file() == 0:
            print('\033[1;31m'+"Invalid File Path!"+'\033[0m')
            exit()
        IFLAG=2
        statFile(AB_FILE)
        T_FORMAT,S_FORMAT,Z_FORMAT = getTimeRange(AB_FILE,IFLAG)
        L_PATH,CWD = LogPathResolver(AB_FILE)
        XLogDig,TLogDig,SLogDig = LogDigger(T_FORMAT,S_FORMAT,Z_FORMAT,L_PATH)
        LogPrinter(TLogDig,SLogDig,XLogDig)

FC_ARRAY = None
XLogDig = None
TLogDig = None
SLogDig = None
FileDict = None
