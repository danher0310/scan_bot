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


mydb = mysql.connector.connect(
    host=settings['dbhost'],
    user=settings['dbuser'],
    password=settings['dbpassword'],
    database=settings['dbname'],
    auth_plugin="mysql_native_password"

)

myCursor = mydb.cursor()
myCursor.execute("SELECT * FROM scans")
result = myCursor.fetchall()
for item in result:
    print(item)