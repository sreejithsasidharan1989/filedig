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

#Global-variables
DOMAIN = ''
USER = ''
CWD=''
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
    print("")
    print('\033[1m'+"=================== FILE STAT ========================\n"+'\033[0m')
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
    return f"/{PATH}/var/{DOMAIN}/logs/",CWD

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
    exit()

try:
    args = sys.argv[1:]
    PATH = Path(args[0])

except:
    print("Something Went Wrong! Try again!")
    __helper()

if len(args) == 1:
    if '-h' in args[0]:
        __helper()
    if PATH.is_file() == 0 and '-h' not in args:
        print('\033[1m'+"\n=============== NOTICE ==============="+'\033[0m')
        print("Please make sure you're using a relative filepath!!\n")
        exit()
        
    AB_FILE = PATH.resolve()
    statFile(AB_FILE)
    T_FORMAT,S_FORMAT,Z_FORMAT = getTimeRange(AB_FILE)
    L_PATH,CWD = LogPathResolver()
    XLogDig,TLogDig,SLogDig = LogDigger(T_FORMAT,S_FORMAT,Z_FORMAT,L_PATH)

    if len(TLogDig) > 0 or len(SLogDig) > 0 or len(XLogDig) > 0:
    
        print('\033[1m'+"=================== LOG ENTRIES ===================\n")
        print("Below is a list of logs & files that correlate to the given file's mtime")
        print("Please be aware that the script only selects logs & files that are within")
        print("a +/-10 second range of the mtime value. Be sure to check other areas.\n"+'\033[0m')
    
        if len(TLogDig) > 0:
            print('\033[1m'+"Logs from website's transfer log"+'\033[0m')
            print("================================\n")
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

elif len(args) == 2:
    if '-stat' in args[1]:
         AB_FILE = PATH.resolve()
         statFile(AB_FILE)
         T_FORMAT,S_FORMAT,Z_FORMAT = getTimeRange(AB_FILE)
         L_PATH,CWD = LogPathResolver()
         FC_ARRAY = FileChainer(CWD,Z_FORMAT)
         if len(FC_ARRAY) > 0:
            print('\033[1m'+"Files modified around the same time")
            print("====================================\n"+'\033[0m')
            for items in FC_ARRAY:
                print(items+"\n")

#else:
#    __helper()

FC_ARRAY = None
XLogDig = None
TLogDig = None
SLogDig = None
FileDict = None
