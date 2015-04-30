from __future__ import print_function
from time       import sleep
import os, sys, re, base64, time
dirNm, execName = os.path.split(os.path.realpath(sys.argv[0]))
sys.path.append(os.path.realpath(dirNm))

import MySQLdb, ConfigParser, getpass
import warnings
warnings.filterwarnings("ignore", "Unknown table.*")

def convertToInt(s):
  """
  Convert to string to int.  Protect against bad input.
  @param s: Input string
  @return: integer value.  If bad return 0.
  """
  try:
    value = int(s)
  except ValueError:
    value = 0
  return value

class LMODdb(object):
  """
  This LMODdb class opens the Lmod database and is responsible for
  all the database interactions.
  """
  def __init__(self, confFn):
    """ Initialize the class and save the db config file. """
    self.__host   = None
    self.__user   = None
    self.__passwd = None
    self.__db     = None
    self.__conn   = None
    self.__confFn = confFn

  def __readFromUser(self):
    """ Ask user for database access info. (private) """

    self.__host   = raw_input("Database host:")
    self.__user   = raw_input("Database user:")
    self.__passwd = getpass.getpass("Database pass:")
    self.__db     = raw_input("Database name:")

  def __readConfig(self):
    """ Read database access info from config file. (private)"""
    confFn = self.__confFn
    try:
      config=ConfigParser.ConfigParser()
      config.read(confFn)
      self.__host    = config.get("MYSQL","HOST")
      self.__user    = config.get("MYSQL","USER")
      self.__passwd  = base64.b64decode(config.get("MYSQL","PASSWD"))
      self.__db      = config.get("MYSQL","DB")
    except ConfigParser.NoOptionError, err:
      sys.stderr.write("\nCannot parse the config file\n")
      sys.stderr.write("Switch to user input mode...\n\n")
      self.__readFromUser()

  def connect(self, databaseName = None):
    """
    Public interface to connect to DB.
    @param db:  If this exists it will be used.
    
    """
    if(os.path.exists(self.__confFn)):
      self.__readConfig()
    else:
      self.__readFromUser()

    n = 100
    for i in xrange(0,n+1):
      try:
        self.__conn = MySQLdb.connect (self.__host,self.__user,self.__passwd)
        if (databaseName):
          cursor = self.__conn.cursor()
          
          # If MySQL version < 4.1, comment out the line below
          cursor.execute("SET SQL_MODE=\"NO_AUTO_VALUE_ON_ZERO\"")
          cursor.execute("USE "+self.db())
        break


      except MySQLdb.Error, e:
        if (i < n):
          sleep(i*0.1)
          pass
        else:
          print ("LMODdb(%d): Error %d: %s" % (i, e.args[0], e.args[1]), file=sys.stderr)
          raise
    return self.__conn


  def db(self):
    """ Return name of db"""
    return self.__db


  def data_to_db(self, dataT):
    """
    Store data into database.
    @param dataT: The data table.
    """

    query = ""
    try:
      conn   = self.connect()
      query  = "USE "+self.db()
      conn.query(query)
      query  = "START TRANSACTION"
      conn.query(query)

      ##################################################################
      # Step 1: Find or insert user into userT table

      query  = "SELECT user_id from userT where user='%s' " % dataT['user']
      conn.query(query)
      result = conn.store_result()
      if (result.num_rows() == 0):
        #
        #  No user found, install user in userT table.
        query   = "INSERT into userT VALUES (NULL,'%s')" % dataT['user']
        conn.query(query)
        user_id = conn.insert_id()
      else:
        #
        # User already in userT, get user_id
        row     = result.fetch_row()
        user_id = int(row[0][0])

      ##################################################################
      # Step 2: Find or insert module name and fn into moduleT

      query = "SELECT mod_id from moduleT WHERE path='%s' and syshost='%s' " % (
        dataT['path'], dataT['syshost'])
      conn.query(query)
      result = conn.store_result()
      if (result.num_rows() > 0):
        row    = result.fetch_row()
        mod_id = int(row[0][0])
      else:
        query = "INSERT into moduleT VALUES (NULL, '%s', '%s', '%s') " % (
          dataT['path'], dataT['module'], dataT['syshost'])
        conn.query(query)
        mod_id = conn.insert_id()

      ##################################################################
      # Step 3: Insert new connection between user and module with a
      #         timestamp into the join_user_module table
      dateTm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(dataT['time'])))
      query  = "INSERT into join_user_module VALUES(NULL, '%s', '%s', '%s') " % (
        user_id, mod_id, dateTm)
      conn.query(query)

      ##################################################################
      # Step 4: Commit everything to db.

      query = "COMMIT"
      conn.query(query)
      conn.close()

    except Exception as e:
      print("data_to_db(): ",e)
      sys.exit(1)