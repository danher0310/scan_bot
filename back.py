from distutils.command.config import config
from importlib.resources import path
import os 
from sys import argv
from configparser import ConfigParser
from datetime import datetime, date, timedelta 
import mysql.connector 

config = ConfigParser()
configfile = 'bot.conf'
#In case the script received an argument, use that argument as name for the config file
#example: python testmarvin.py testmarvin.conf
if len(argv)> 1:
    configfile=argv[1]
config.read(f"./{configfile}")
settings = config['SETTINGS']
path = format(settings['path'])


def get_first_element(listOfTuples):
    return list(map(lambda x: x[0], listOfTuples))

def process_unexistent_files(mydb,path,filesInFolder):
    myCursor = mydb.cursor()
    myCursor.execute("SELECT filename FROM scans WHERE filepath = %s AND processed_date IS NULL",(path,))
    filesNotProcessed=[x[0] for x in myCursor.fetchall()]
    filesThatWereProcessed =list(filter(lambda x: not_inside_list(x,filesInFolder),filesNotProcessed))
    now=datetime.now()
    filesThatWereProcessed= list(map(lambda x:(now,path,x),filesThatWereProcessed))
    if len(filesThatWereProcessed) > 0 :
        myCursor.executemany("UPDATE scans SET processed_date = %s WHERE filepath = %s AND filename = %s",filesThatWereProcessed)
        mydb.commit()
    
def add_files(mydb,filepath, filenames,agent,owner):
    myCursor = mydb.cursor()
    queryString="INSERT INTO scans (filepath,filename,agentname,owner,created_date) VALUES (%s,%s,%s,%s,%s)"
    now=datetime.now()
    filenames=list(map(lambda x: (filepath,x,agent,owner,now),filenames))
    myCursor.executemany(queryString,filenames)
    mydb.commit()

def filter_system_files(x,path):
    system_files=["Thumbs.db"]
    valid = True
    valid= valid and (x not in system_files)
    valid= valid and (x.find(".lnk") < 0)
    foldersToSkip= settings['folders_to_skip'].split(',')
    item_path = path + os.sep + x
    valid= valid and not (os.path.isdir(item_path) and x in foldersToSkip)
    return valid

def not_inside_list(x,list):
    return x not in list


def Count_folder(mydb,path,agent_name=None,owner=None,level=None):
    result=""
    total = 0
    try:
        myCursor =mydb.cursor(buffered=True)
        lista = os.listdir(path)
        lista= list(filter(lambda x: filter_system_files(x,path),lista))
        #print(owner,lista)
        process_unexistent_files(mydb,path,lista)
        dateOldestFile=None
        number_files=0
        fileNameList=[]
        for item in lista:
            item_path = path + os.sep + item
            if os.path.isdir(item_path):
                (files, count) = Count_folder(mydb,item_path,agent_name,owner)
                result += files
                total += count
            else:
                number_files +=1
                fileNameList.append(item)
        myCursor.execute("SELECT filename FROM scans WHERE filepath = %s AND processed_date IS NULL",(path,))
        filesInFolder=[x[0] for x in myCursor.fetchall()]
        fileNameList= list(filter(lambda x: not_inside_list(x,filesInFolder) ,fileNameList))
        if len(fileNameList) > 0:
            add_files(mydb,path,fileNameList,agent_name,owner)
        myCursor.execute("SELECT MIN(created_date) FROM scans WHERE filepath = %s AND processed_date IS NULL",(path,))
        dateOldestFile=myCursor.fetchone()[0]
        print(owner,path,dateOldestFile)
        name = path.split(os.sep).pop()
        Pre_path = path.split(os.sep)[-2]
        root = path.split('_')[0]
        if  name.__contains__('Scans_'):
            result += f"Root: {str(number_files)} "
        elif (Pre_path == 'Rejected'):
            result += "Rejected by "+ name + ": " + str(number_files)
        else:
            result += f"{name} : {str(number_files)} "
        if dateOldestFile is not None:
            dateOldestFile=dateOldestFile.strftime('%m/%d/%y')
            result += "(oldest: "+dateOldestFile+")"
        result+="\n"
        total += number_files
        if level:
            result += "Total: "+str(total)+"\n"
        return (result,total)    
    except OSError:
        return OSError

def check_config():
    result =""
    try:
        mydb = mysql.connector.connect(
            host=settings['dbhost'],
            user=settings['dbuser'],
            password=settings['dbpassword'],
            database=settings['dbname'],
            auth_plugin="mysql_native_password"
        )
        total = 0
        for section in config.sections():
            if section.format([''])[0:6] == "FOLDER":
                full_path = path + os.sep + config.get(section,'folder')
                agent_name = config.get(section,'agent_name')
                owner = config.get(section,'owner')
                if owner != agent_name:
                    result +=  "Scanner: "+ owner + "\n"
                else: 
                    result += "Scanner: " + agent_name + "\n"
                (files,count)=Count_folder(mydb,full_path,agent_name,owner,1)
                result += files
                result+= '----------------------------'+"\n"
                total += count
        result += "Total files in folders: "+str(total)+"\n"
        result+= '----------------------------'+"\n"
        mydb.close()

    except OSError:
        return OSError
    return result

def oldest(mydb, owner):
    result =""
    try:
        myCursor = mydb.cursor(buffered=True)
        myCursor.execute("SELECT min(created_date), filename, filepath owner from im_scans.scans where owner = '{}' and processed_date is NULL;".format(owner))
        data = myCursor.fetchall()
        for item in data:
            if item[0] is not None and item [1] is not None and item[2] is not None:
                result += "OLDEST FILE: " + owner +"\n"
                result += "FILE: " + item[1] +"\n"
                result += "DATE: (" + item[0].strftime('%m/%d/%y') + ")\n" 
                result += "----------------------------\n"
        
    except OSError:
        return OSError
    return result

def check_oldest(limit = 1):
    limit = int(limit)
    result = ""
    try: 
        mydb = mysql.connector.connect(
            host=settings['dbhost'],
            user=settings['dbuser'],
            password=settings['dbpassword'],
            database=settings['dbname'],
            auth_plugin="mysql_native_password"
        )
        myCursor = mydb.cursor(buffered=True)
        myCursor.execute("SELECT created_date, filename, filepath, owner from im_scans.scans where processed_date IS NULL order by created_date asc limit {};".format(limit))
        myresult = myCursor.fetchall()
        for item in myresult:
            name = item[2][12:]      
            result += "OLDEST FILE: " + name +"\n"
            result += "FILE: " + item[1] +"\n"
            result += "DATE: " + item[0].strftime('%m/%d/%y') + "\n"
            result += '------------------------------------------- \n'
        mydb.close()
        return result

    except OSError:
        return OSError 
    
def check_oldest_by_user():
    result = ""
    try:
        mydb = mysql.connector.connect(
            host=settings['dbhost'],
            user=settings['dbuser'],
            password=settings['dbpassword'],
            database=settings['dbname'],
            auth_plugin="mysql_native_password"
            )
        for section in config.sections():
            if section.format([''])[0:6] == "FOLDER":
                owner = config.get(section,'owner')
                (oldests) = oldest(mydb,owner)
                result += oldests
        mydb.close()
    except OSError:
        return OSError
    return result

def oldest_day(mydb, owner, days, day):
    result = ""
    try:
        myCursor = mydb.cursor(buffered=True)
        myCursor.execute("SELECT created_date, filename, owner from im_scans.scans where  created_date between '{} 00:00:00' and '{} 23:59:59' and processed_date is NULL ;".format(owner, days))
        data = myCursor.fetchall()
        if len(data) == 0:
            result += "Owner: {} ".format(owner) + "\n"
            result += "No files found for the last {} days".format(day) + "\n"
            result += '-------------------------------------'+"\n"
        else:
            result += "Owner: {} ".format(owner) + "\n"
            for item in data:
                result += "FILE: " + item[1] +"\n"
                result += "DATE: " + item[0].strftime('%m/%d/%y') + "\n"
                result += '-------------------------------------'+"\n"    
        myCursor.close()                
    except OSError:
        return OSError
    return result

def check_oldest_by_day(days = 10):
    cantDays= days
    result=""
    days = int(days)
    days = date.today() - timedelta(days=days)
    try:
        mydb = mysql.connector.connect(
            host=settings['dbhost'],
            user=settings['dbuser'],
            password=settings['dbpassword'],
            database=settings['dbname'],
            auth_plugin="mysql_native_password"
        )
        myCursor = mydb.cursor(buffered=True)
        myCursor.execute("SELECT created_date, filename, owner from im_scans.scans where  created_date between '{} 00:00:00' and '{} 23:59:59' and processed_date is NULL ;".format(days, days))
        myresult = myCursor.fetchall()
        if len(myresult) == 0:
            result = None
        else:
            result += "Documents from: {}".format(cantDays) + " days ago\n"
            owner = myresult[0][2]
            result += "-------------------------------------" + "\n"
            result += "Owner: " + owner + "\n"
            for item in myresult:
                result   += "FILE: " + item[1] +"\n" 
                if item[2] != owner:
                    owner = item[2]
                    result += "----------------------------------\n"
                    result += "Owner: " + owner + "\n"
                    result += "FILE: " + item[1] +"\n"                
                else:                    
                    result += "FILE: " + item[1] +"\n"
        myCursor.close()        

    except OSError:
        return OSError
    return result

def checkUserDaysDelay(days):
    days = int(days)
    days = date.today() - timedelta(days=days)
    result = ""
    try: 
        mydb = mysql.connector.connect(
            host=settings['dbhost'],
            user=settings['dbuser'],
            password=settings['dbpassword'],
            database=settings['dbname'],
            auth_plugin="mysql_native_password"
        )
        myCursor = mydb.cursor(buffered=True)
        myCursor.execute("SELECT  owner from im_scans.scans where  created_date between '{} 00:00:00' and '{} 23:59:59' and processed_date is NULL ;".format(days, days))
        myresult = myCursor.fetchall()
        if len(myresult) == 0:
            result = None
        else:
            owner = myresult[0][0]
            result += "Owner: " + owner + "\n"
            for item in myresult:
                if item[0] != owner:
                    owner = item[0]
                    result += "----------------------------------\n"
                    result += "Owner: " + owner + "\n"
        myCursor.close()
    except OSError:
        return OSError
    return result
#test
