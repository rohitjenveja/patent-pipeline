#/usr/bin/python

import datetime
import logging
import MySQLdb
import os
import urllib2
import tarfile
from os.path import abspath, realpath, dirname, join as joinpath
from sys import stderr


"""Gather patent data from US Patent office dump.

- yum install MySQL-python
"""

PATENT_GRANTS_HOST = ("http://storage.googleapis.com/patents/"
	              "redbook/grants/")

PATENT_APPLICATIONS_HOST = ()
CONN=None

# Remove mysql password and hostname, once there is content.
# Use a secure password file instead.
MYSQL_HOSTNAME = ''
MYSQL_USER = ''
MYSQL_PW = ''
MYSQL_DATABASE = 'patents'


def RequiresConnection(func):
  def wrapper(*arg):
    global CONN
    if not CONN:
      CONN = MySQLdb.connect(
          MYSQL_HOSTNAME,
          MYSQL_USER,
          MYSQL_PW,
          MYSQL_DATABASE)
    return func(*arg)
  return wrapper


def badpath(path, base):
  resolved = lambda x: realpath(abspath(x))
  # joinpath will ignore base if path is absolute
  return not resolved(joinpath(base,path)).startswith(base)


def badlink(info, base):
  resolved = lambda x: realpath(abspath(x))
  # Links are interpreted relative to the directory containing the link
  tip = resolved(joinpath(base, dirname(info.name)))
  return badpath(info.linkname, base=tip)


def safemembers(members):
  resolved = lambda x: realpath(abspath(x))
  base = resolved(".")

  for finfo in members:
    if badpath(finfo.name, base):
      print >>stderr, finfo.name, "is blocked (illegal path)"
    elif finfo.issym() and badlink(finfo,base):
      print >>stderr, finfo.name, "is blocked: Hard link to", finfo.linkname
    elif finfo.islnk() and badlink(finfo,base):
      print >>stderr, finfo.name, "is blocked: Symlink to", finfo.linkname
    else:
      yield finfo


def GetPatentGrants(month, day, year, extension):
  """Gets the data dump from the patent grants site for the given week."""
  # Create the full url to the patent data. As an example,
  # http://storage.googleapis.com/patents/redbook/grants/2014/I20140107.tar

  day = "%02d" % (day,)  # adds a leading zero if under 10.
  month = "%02d" % (month,)
  format = 'I%(year)s%(month)s%(day)s.%(extension)s'
  filename =  format % {'year': year, 'day': day,
                        'month': month, 'extension': extension}
  patent_grants_url = os.path.join(PATENT_GRANTS_HOST, str(year), filename)
  logging.info("URL to contact: %s", patent_grants_url)
  local_path = os.path.join('/patent_dumps', filename)
  SaveToDisk(patent_grants_url, local_path)
  tar = tarfile.open(local_path)
  tar.extractall(path="./sandbox/%" % filename, members=safemembers(ar))
  tar.close()
  MarkAsSuccess(month, day, year)


@RequiresConnection
def MarkAsSuccess(month, day, year):
  mark_date = datetime.datetime(month=month, day=day, year=year)
  status = 'success'
  # need to have mark as success for different phases.
  insert = ("INSERT into run_status (data_date, run_status) "
            "VALUES('%(data_date)s', '%(status)s')" % {'data_date': str(mark_date),
                                                     'status': status})
  cursor = CONN.cursor()
  cursor.execute(insert)
  CONN.commit()


def SaveToDisk(url, local_path, conn=None):
  # Change to use S3 and put in unprocessed directory.
  # Add note to use amazon SQS
  if os.path.isfile(local_path):
    logging.warn("File already exists: %s", local_path)
    return
  req = urllib2.urlopen(url)
  CHUNK = 16 * 1024
  # add a file exists check here.

  with open(local_path, 'wb') as fp:
    while True:
      chunk = req.read(CHUNK)
      if not chunk: break
      fp.write(chunk)


def GetPatentApplications():
  """Gets the data dump for the patent application site for the given week."""
  pass


@RequiresConnection
def GetAllDatesForDataType(data_type, conn=None):
  """Queries the backend for a particular data type

  Returns a list of datetime.date objects
  """
  cursor = CONN.cursor()
  results = cursor.execute("SELECT * FROM run_status WHERE run_status='success'")
  rows = cursor.fetchall()
  for result in rows:
    yield result


def GetWeeks(data_type, format):
  """Queries the backend database to determine weeks of data we are missing.

  Args:
    data_type: The type of dataset we are evaluating (i.e. apps, grants etc.,)
    format: The type of date format needed for the particular source.
      For applications and grants, we need the week number. For full patent data,
      the week and date are required.

  Returns:
    A list of datetimes. [(2014, 01), (2014,02)]
  """
  if format == 'tuesday':
    end = datetime.date.today()
    start = end - datetime.timedelta(30)

    tuesdays = []

    while start <= end:
      if start.weekday() == 1:
        tuesdays.append(start)
      start = start + datetime.timedelta(1)

    completed = GetAllDatesForDataType(data_type)
    return [tuesday for tuesday in tuesdays
            if tuesday not in completed]


if __name__ == "__main__":
  func_map = {
              'grants': GetPatentGrants,
 	      # 'applications': GetPatentApplications,
             }
  for data_type, func in func_map.iteritems():
    weeks = GetWeeks(data_type, 'tuesday')
    for incomplete in GetWeeks(data_type, 'tuesday'):
      func(incomplete.month, incomplete.day, incomplete.year, 'tar')
