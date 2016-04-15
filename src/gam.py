#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GAM
#
# Copyright 2015, LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

u"""GAM is a command line tool which allows Administrators to control their Google Apps domain and accounts.

With GAM you can programatically create users, turn on/off services for users like POP and Forwarding and much more.
For more information, see http://git.io/gam

"""

__author__ = u'Jay Lee <jay0lee@gmail.com>'
__version__ = u'3.66'
__license__ = u'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

import sys, os, time, datetime, random, socket, csv, platform, re, calendar, base64, string, codecs, StringIO, subprocess

import json
import httplib2
import googleapiclient
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import oauth2client.client
import oauth2client.service_account
import oauth2client.file
import oauth2client.tools
import mimetypes
import ntpath

GAM_URL = u'http://git.io/gam'
GAM_INFO = u'GAM {0} - {1} / {2} / Python {3}.{4}.{5} {6} / {7} {8} /'.format(__version__, GAM_URL,
                                                                              __author__,
                                                                              sys.version_info[0], sys.version_info[1], sys.version_info[2],
                                                                              sys.version_info[3],
                                                                              platform.platform(), platform.machine())
GAM_RELEASES = u'https://github.com/jay0lee/GAM/releases'
GAM_WIKI = u'https://github.com/jay0lee/GAM/wiki'
GAM_WIKI_CREATE_CLIENT_SECRETS = GAM_WIKI+u'/CreatingClientSecretsFile#creating-your-own-oauth2servicejson'
GAM_APPSPOT = u'https://gam-update.appspot.com'
GAM_APPSPOT_LATEST_VERSION = GAM_APPSPOT+u'/latest-version.txt?v='+__version__
GAM_APPSPOT_LATEST_VERSION_ANNOUNCEMENT = GAM_APPSPOT+u'/latest-version-announcement.txt?v='+__version__

TRUE = u'true'
FALSE = u'false'
true_values = [u'on', u'yes', u'enabled', u'true', u'1']
false_values = [u'off', u'no', u'disabled', u'false', u'0']
usergroup_types = [u'user', u'users', u'group', u'ou', u'org',
                   u'ou_and_children', u'ou_and_child', u'query',
                   u'license', u'licenses', u'licence', u'licences', u'file', u'csv', u'all',
                   u'cros']
ERROR = u'ERROR'
ERROR_PREFIX = ERROR+u': '
WARNING = u'WARNING'
WARNING_PREFIX = WARNING+u': '
FN_CLIENT_SECRETS_JSON = u'client_secrets.json'
FN_EXTRA_ARGS_TXT = u'extra-args.txt'
FN_LAST_UPDATE_CHECK_TXT = u'lastupdatecheck.txt'
FN_OAUTH2SERVICE_JSON = u'oauth2service.json'
FN_OAUTH2_TXT = u'oauth2.txt'
MY_CUSTOMER = u'my_customer'
UNKNOWN = u'Unknown'
#
# Global variables
#
# The following GM_XXX constants are arbitrary but must be unique
# Most errors print a message and bail out with a return code
# Some commands want to set a non-zero return code but not bail
GM_SYSEXITRC = u'sxrc'
# Path to gam
GM_GAM_PATH = u'gpth'
# Are we on Windows?
GM_WINDOWS = u'wndo'
# Encodings
GM_SYS_ENCODING = u'syen'
# Shared by batch_worker and run_batch
GM_BATCH_QUEUE = u'batq'
# Extra arguments to pass to GAPI functions
GM_EXTRA_ARGS_DICT = u'exad'
# Values retrieved from oauth2service.json
GM_OAUTH2SERVICE_JSON_DATA = u'oajd'
GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID = u'oaci'
# File containing time of last GAM update check
GM_LAST_UPDATE_CHECK_TXT = u'lupc'
# Dictionary mapping OrgUnit ID to Name
GM_MAP_ORGUNIT_ID_TO_NAME = u'oi2n'
# Dictionary mapping Role ID to Name
GM_MAP_ROLE_ID_TO_NAME = u'ri2n'
# Dictionary mapping Role Name to ID
GM_MAP_ROLE_NAME_TO_ID = u'rn2i'
# Dictionary mapping User ID to Name
GM_MAP_USER_ID_TO_NAME = u'ui2n'
#
GM_Globals = {
  GM_SYSEXITRC: 0,
  GM_GAM_PATH: os.path.dirname(os.path.realpath(__file__)) if not getattr(sys, u'frozen', False) else os.path.dirname(sys.executable),
  GM_WINDOWS: os.name == u'nt',
  GM_SYS_ENCODING: sys.getfilesystemencoding() if os.name == u'nt' else u'utf-8',
  GM_BATCH_QUEUE: None,
  GM_EXTRA_ARGS_DICT:  {u'prettyPrint': False},
  GM_OAUTH2SERVICE_JSON_DATA: None,
  GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID: None,
  GM_LAST_UPDATE_CHECK_TXT: u'',
  GM_MAP_ORGUNIT_ID_TO_NAME: None,
  GM_MAP_ROLE_ID_TO_NAME: None,
  GM_MAP_ROLE_NAME_TO_ID: None,
  GM_MAP_USER_ID_TO_NAME: None,
  }
#
# Global variables defined by environment variables/signal files
#
# When retrieving lists of Google Drive activities from API, how many should be retrieved in each chunk
GC_ACTIVITY_MAX_RESULTS = u'activity_max_results'
# Automatically generate gam batch command if number of users specified in gam users xxx command exceeds this number
# Default: 0, don't automatically generate gam batch commands
GC_AUTO_BATCH_MIN = u'auto_batch_min'
# GAM cache directory. If no_cache is specified, this variable will be set to None
GC_CACHE_DIR = u'cache_dir'
# Character set of batch, csv, data files
GC_CHARSET = u'charset'
# Path to client_secrets.json
GC_CLIENT_SECRETS_JSON = u'client_secrets_json'
# GAM config directory containing client_secrets.json, oauth2.txt, oauth2service.json, extra_args.txt
GC_CONFIG_DIR = u'config_dir'
# custmerId from gam.cfg or retrieved from Google
GC_CUSTOMER_ID = u'customer_id'
# If debug_level > 0: extra_args[u'prettyPrint'] = True, httplib2.debuglevel = gam_debug_level, appsObj.debug = True
GC_DEBUG_LEVEL = u'debug_level'
# When retrieving lists of ChromeOS/Mobile devices from API, how many should be retrieved in each chunk
GC_DEVICE_MAX_RESULTS = u'device_max_results'
# Domain obtained from gam.cfg or oauth2.txt
GC_DOMAIN = u'domain'
# Google Drive download directory
GC_DRIVE_DIR = u'drive_dir'
# When retrieving lists of Drive files/folders from API, how many should be retrieved in each chunk
GC_DRIVE_MAX_RESULTS = u'drive_max_results'
# If no_browser is False, writeCSVfile won't open a browser when todrive is set
# and doRequestOAuth prints a link and waits for the verification code when oauth2.txt is being created
GC_NO_BROWSER = u'no_browser'
# Disable GAM API caching
GC_NO_CACHE = u'no_cache'
# Disable GAM update check
GC_NO_UPDATE_CHECK = u'no_update_check'
# Disable SSL certificate validation
GC_NO_VERIFY_SSL = u'no_verify_ssl'
# Number of threads for gam batch
GC_NUM_THREADS = u'num_threads'
# Path to oauth2.txt
GC_OAUTH2_TXT = u'oauth2_txt'
# Path to oauth2service.json
GC_OAUTH2SERVICE_JSON = u'oauth2service_json'
# Default section to use for processing
GC_SECTION = u'section'
# Add (n/m) to end of messages if number of items to be processed exceeds this number
GC_SHOW_COUNTS_MIN = u'show_counts_min'
# Enable/disable "Getting ... " messages
GC_SHOW_GETTINGS = u'show_gettings'
# GAM config directory containing admin-settings-v1.json, cloudprint-v2.json
GC_SITE_DIR = u'site_dir'
# When adding Users to Groups/Org Units, how many should be processed in each batch
GC_USER_BATCH_SIZE = u'user_batch_size'
# When retrieving lists of Users from API, how many should be retrieved in each chunk
GC_USER_MAX_RESULTS = u'user_max_results'

GC_Defaults = {
  GC_ACTIVITY_MAX_RESULTS: 100,
  GC_AUTO_BATCH_MIN: 0,
  GC_CACHE_DIR: u'',
  GC_CHARSET: u'utf-8',
  GC_CLIENT_SECRETS_JSON: FN_CLIENT_SECRETS_JSON,
  GC_CONFIG_DIR: u'',
  GC_CUSTOMER_ID: u'',
  GC_DEBUG_LEVEL: 0,
  GC_DEVICE_MAX_RESULTS: 500,
  GC_DOMAIN: u'',
  GC_DRIVE_DIR: u'',
  GC_DRIVE_MAX_RESULTS: 1000,
  GC_NO_BROWSER: FALSE,
  GC_NO_CACHE: FALSE,
  GC_NO_UPDATE_CHECK: FALSE,
  GC_NO_VERIFY_SSL: FALSE,
  GC_NUM_THREADS: 5,
  GC_OAUTH2_TXT: FN_OAUTH2_TXT,
  GC_OAUTH2SERVICE_JSON: FN_OAUTH2SERVICE_JSON,
  GC_SECTION: u'',
  GC_SHOW_COUNTS_MIN: 1,
  GC_SHOW_GETTINGS: TRUE,
  GC_SITE_DIR: u'',
  GC_USER_BATCH_SIZE: 50,
  GC_USER_MAX_RESULTS: 500,
  }

GC_Values = {}

GC_TYPE_BOOLEAN = u'bool'
GC_TYPE_CHOICE = u'choi'
GC_TYPE_DIRECTORY = u'dire'
GC_TYPE_EMAIL = u'emai'
GC_TYPE_FILE = u'file'
GC_TYPE_INTEGER = u'inte'
GC_TYPE_LANGUAGE = u'lang'
GC_TYPE_STRING = u'stri'

GC_VAR_TYPE = u'type'
GC_VAR_LIMITS = u'lmit'

GC_VAR_INFO = {
  GC_ACTIVITY_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 500)},
  GC_AUTO_BATCH_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_CACHE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_CHARSET: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_CLIENT_SECRETS_JSON: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_CONFIG_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_CUSTOMER_ID: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DEBUG_LEVEL: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_DEVICE_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_DOMAIN: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DRIVE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_DRIVE_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_NO_BROWSER: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_CACHE: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_UPDATE_CHECK: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_VERIFY_SSL: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NUM_THREADS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, None)},
  GC_OAUTH2_TXT: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_OAUTH2SERVICE_JSON: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_SECTION: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_SHOW_COUNTS_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_SHOW_GETTINGS: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_SITE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_USER_BATCH_SIZE: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_USER_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 500)},
  }
#
CLEAR_NONE_ARGUMENT = [u'clear', u'none',]
#
MESSAGE_CLIENT_API_ACCESS_DENIED = u'Access Denied. Please make sure the Client Name:\n\n{0}\n\nis authorized for the API Scope(s):\n\n{1}\n\nThis can be configured in your Control Panel under:\n\nSecurity -->\nAdvanced Settings -->\nManage API client access'
MESSAGE_GAM_EXITING_FOR_UPDATE = u'GAM is now exiting so that you can overwrite this old version with the latest release'
MESSAGE_GAM_OUT_OF_MEMORY = u'GAM has run out of memory. If this is a large Google Apps instance, you should use a 64-bit version of GAM on Windows or a 64-bit version of Python on other systems.'
MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS = u'Header "{0}" not found in CSV headers of "{1}".'
MESSAGE_HIT_CONTROL_C_TO_UPDATE = u'\n\nHit CTRL+C to visit the GAM website and download the latest release or wait 15 seconds continue with this boring old version. GAM won\'t bother you with this announcement for 1 week or you can create a file named noupdatecheck.txt in the same location as gam.py or gam.exe and GAM won\'t ever check for updates.'
MESSAGE_INVALID_JSON = u'The file {0} has an invalid format.'
MESSAGE_NO_DISCOVERY_INFORMATION = u'No online discovery doc and {0} does not exist locally'
MESSAGE_NO_PYTHON_SSL = u'You don\'t have the Python SSL module installed so we can\'t verify SSL Certificates. You can fix this by installing the Python SSL module or you can live on the edge and turn SSL validation off by creating a file named noverifyssl.txt in the same location as gam.exe / gam.py'
MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE = u'Cowardly refusing to perform migration due to lack of target drive space. Source size: {0}mb Target Free: {1}mb'
MESSAGE_REQUEST_COMPLETED_NO_FILES = u'Request completed but no results/files were returned, try requesting again'
MESSAGE_REQUEST_NOT_COMPLETE = u'Request needs to be completed before downloading, current status is: {0}'
MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET = u'Results are too large for Google Spreadsheets. Uploading as a regular CSV file.'
MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON = u'Please follow the instructions at this site to setup a Service Account.'
MESSAGE_OAUTH2SERVICE_JSON_INVALID = u'The file {0} is missing required keys (client_email, client_id or private_key).'

def convertUTF8(data):
  import collections
  if isinstance(data, str):
    return data
  if isinstance(data, unicode):
    if GM_Globals[GM_WINDOWS]:
      return data
    return data.encode(GM_Globals[GM_SYS_ENCODING])
  if isinstance(data, collections.Mapping):
    return dict(map(convertUTF8, data.iteritems()))
  if isinstance(data, collections.Iterable):
    return type(data)(map(convertUTF8, data))
  return data

def win32_unicode_argv():
  from ctypes import POINTER, byref, cdll, c_int, windll
  from ctypes.wintypes import LPCWSTR, LPWSTR

  GetCommandLineW = cdll.kernel32.GetCommandLineW
  GetCommandLineW.argtypes = []
  GetCommandLineW.restype = LPCWSTR

  CommandLineToArgvW = windll.shell32.CommandLineToArgvW
  CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
  CommandLineToArgvW.restype = POINTER(LPWSTR)

  cmd = GetCommandLineW()
  argc = c_int(0)
  argv = CommandLineToArgvW(cmd, byref(argc))
  if argc.value > 0:
    # Remove Python executable and commands if present
    start = argc.value - len(sys.argv)
    return [argv[i] for i in xrange(start, argc.value)]

from HTMLParser import HTMLParser
from re import sub
from sys import stderr
from traceback import print_exc

class _DeHTMLParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.__text = []

  def handle_data(self, data):
    text = data.strip()
    if len(text) > 0:
      text = sub('[ \t\r\n]+', ' ', text)
      self.__text.append(text + ' ')

  def handle_starttag(self, tag, attrs):
    if tag == 'p':
      self.__text.append('\n\n')
    elif tag == 'br':
      self.__text.append('\n')

  def handle_startendtag(self, tag, attrs):
    if tag == 'br':
      self.__text.append('\n\n')

  def text(self):
    return ''.join(self.__text).strip()


def dehtml(text):
  try:
    parser = _DeHTMLParser()
    parser.feed(text.encode('utf-8'))
    parser.close()
    return parser.text()
  except:
    print_exc(file=stderr)
    return text

def showUsage():
  doGAMVersion()
  print u'''
Usage: gam [OPTIONS]...

GAM. Retrieve or set Google Apps domain,
user, group and alias settings. Exhaustive list of commands
can be found at: https://github.com/jay0lee/GAM/wiki

Examples:
gam info domain
gam create user jsmith firstname John lastname Smith password secretpass
gam update user jsmith suspended on
gam.exe update group announcements add member jsmith
...

'''
#
# Error handling
#
def stderrErrorMsg(message):
  sys.stderr.write(convertUTF8(u'\n{0}{1}\n'.format(ERROR_PREFIX, message)))

def stderrWarningMsg(message):
  sys.stderr.write(convertUTF8(u'\n{0}{1}\n'.format(WARNING_PREFIX, message)))

def systemErrorExit(sysRC, message):
  if message:
    stderrErrorMsg(message)
  sys.exit(sysRC)

def invalidJSONExit(fileName):
  systemErrorExit(17, MESSAGE_INVALID_JSON.format(fileName))

def noPythonSSLExit():
  systemErrorExit(8, MESSAGE_NO_PYTHON_SSL)

def printLine(message):
  sys.stdout.write(message+u'\n')
#
def getCharSet(i):
  if (i == len(sys.argv)) or (sys.argv[i].lower() != u'charset'):
    return (i, GC_Values.get(GC_CHARSET, GM_Globals[GM_SYS_ENCODING]))
  return (i+2, sys.argv[i+1])

#
# Open a file
#
def openFile(filename, mode=u'rb'):
  try:
    if filename != u'-':
      return open(filename, mode)
    if mode.startswith(u'r'):
      return StringIO.StringIO(unicode(sys.stdin.read()))
    return sys.stdout
  except IOError as e:
    systemErrorExit(6, e)
#
# Close a file
#
def closeFile(f):
  try:
    f.close()
    return True
  except IOError as e:
    stderrErrorMsg(e)
    return False
#
# Read a file
#
def readFile(filename, mode=u'rb', continueOnError=False, displayError=True, encoding=None):
  try:
    if filename != u'-':
      if not encoding:
        with open(filename, mode) as f:
          return f.read()
      else:
        with codecs.open(filename, mode, encoding) as f:
          content = f.read()
          if not content.startswith(codecs.BOM_UTF8):
            return content
          return content.replace(codecs.BOM_UTF8, u'', 1)
    else:
      return unicode(sys.stdin.read())
  except IOError as e:
    if continueOnError:
      if displayError:
        stderrWarningMsg(e)
      return None
    systemErrorExit(6, e)
#
# Write a file
#
def writeFile(filename, data, mode=u'wb', continueOnError=False, displayError=True):
  try:
    with open(filename, mode) as f:
      f.write(data)
    return True
  except IOError as e:
    if continueOnError:
      if displayError:
        stderrErrorMsg(e)
      return False
    systemErrorExit(6, e)
#
# Set global variables
# Check for GAM updates based on status of noupdatecheck.txt
#
def SetGlobalVariables():

  def _getOldEnvVar(itemName, envVar):
    value = os.environ.get(envVar, GC_Defaults[itemName])
    if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_INTEGER:
      try:
        number = int(value)
        minVal, maxVal = GC_VAR_INFO[itemName][GC_VAR_LIMITS]
        if number < minVal:
          number = minVal
        elif maxVal and (number > maxVal):
          number = maxVal
      except ValueError:
        number = GC_Defaults[itemName]
      value = number
    GC_Defaults[itemName] = value

  def _getOldSignalFile(itemName, fileName, trueValue=True, falseValue=False):
    GC_Defaults[itemName] = trueValue if os.path.isfile(os.path.join(GC_Defaults[GC_CONFIG_DIR], fileName)) else falseValue

  def _getCfgDirectory(itemName):
    return GC_Defaults[itemName]

  def _getCfgFile(itemName):
    value = os.path.expanduser(GC_Defaults[itemName])
    if not os.path.isabs(value):
      value = os.path.expanduser(os.path.join(GC_Values[GC_CONFIG_DIR], value))
    return value

  GC_Defaults[GC_CONFIG_DIR] = GM_Globals[GM_GAM_PATH]
  GC_Defaults[GC_CACHE_DIR] = os.path.join(GM_Globals[GM_GAM_PATH], u'gamcache')
  GC_Defaults[GC_DRIVE_DIR] = GM_Globals[GM_GAM_PATH]
  GC_Defaults[GC_SITE_DIR] = GM_Globals[GM_GAM_PATH]

  _getOldEnvVar(GC_CONFIG_DIR, u'GAMUSERCONFIGDIR')
  _getOldEnvVar(GC_SITE_DIR, u'GAMSITECONFIGDIR')
  _getOldEnvVar(GC_CACHE_DIR, u'GAMCACHEDIR')
  _getOldEnvVar(GC_DRIVE_DIR, u'GAMDRIVEDIR')
  _getOldEnvVar(GC_OAUTH2_TXT, u'OAUTHFILE')
  _getOldEnvVar(GC_OAUTH2SERVICE_JSON, u'OAUTHSERVICEFILE')
  if GC_Defaults[GC_OAUTH2SERVICE_JSON].find(u'.') == -1:
    GC_Defaults[GC_OAUTH2SERVICE_JSON] += u'.json'
  _getOldEnvVar(GC_CLIENT_SECRETS_JSON, u'CLIENTSECRETS')
  _getOldEnvVar(GC_DOMAIN, u'GA_DOMAIN')
  _getOldEnvVar(GC_CUSTOMER_ID, u'CUSTOMER_ID')
  _getOldEnvVar(GC_CHARSET, u'GAM_CHARSET')
  _getOldEnvVar(GC_NUM_THREADS, u'GAM_THREADS')
  _getOldEnvVar(GC_AUTO_BATCH_MIN, u'GAM_AUTOBATCH')
  _getOldEnvVar(GC_ACTIVITY_MAX_RESULTS, u'GAM_ACTIVITY_MAX_RESULTS')
  _getOldEnvVar(GC_DEVICE_MAX_RESULTS, u'GAM_DEVICE_MAX_RESULTS')
  _getOldEnvVar(GC_DRIVE_MAX_RESULTS, u'GAM_DRIVE_MAX_RESULTS')
  _getOldEnvVar(GC_USER_MAX_RESULTS, u'GAM_USER_MAX_RESULTS')
  _getOldSignalFile(GC_DEBUG_LEVEL, u'debug.gam', trueValue=4, falseValue=0)
  _getOldSignalFile(GC_NO_VERIFY_SSL, u'noverifyssl.txt')
  _getOldSignalFile(GC_NO_BROWSER, u'nobrowser.txt')
  _getOldSignalFile(GC_NO_CACHE, u'nocache.txt')
  _getOldSignalFile(GC_NO_UPDATE_CHECK, u'noupdatecheck.txt')
# Assign directories first
  for itemName in GC_VAR_INFO:
    if GC_VAR_INFO[itemName][GC_VAR_TYPE] == GC_TYPE_DIRECTORY:
      GC_Values[itemName] = _getCfgDirectory(itemName)
  for itemName in GC_VAR_INFO:
    varType = GC_VAR_INFO[itemName][GC_VAR_TYPE]
    if varType == GC_TYPE_FILE:
      GC_Values[itemName] = _getCfgFile(itemName)
    else:
      GC_Values[itemName] = GC_Defaults[itemName]
  GM_Globals[GM_LAST_UPDATE_CHECK_TXT] = os.path.join(GC_Values[GC_CONFIG_DIR], FN_LAST_UPDATE_CHECK_TXT)
  if not GC_Values[GC_NO_UPDATE_CHECK]:
    doGAMCheckForUpdates()
# Globals derived from config file values
  GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = None
  GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = None
  GM_Globals[GM_EXTRA_ARGS_DICT] = {u'prettyPrint': GC_Values[GC_DEBUG_LEVEL] > 0}
  httplib2.debuglevel = GC_Values[GC_DEBUG_LEVEL]
  if os.path.isfile(os.path.join(GC_Values[GC_CONFIG_DIR], FN_EXTRA_ARGS_TXT)):
    import ConfigParser
    ea_config = ConfigParser.ConfigParser()
    ea_config.optionxform = str
    ea_config.read(os.path.join(GC_Values[GC_CONFIG_DIR], FN_EXTRA_ARGS_TXT))
    GM_Globals[GM_EXTRA_ARGS_DICT].update(dict(ea_config.items(u'extra-args')))
  if GC_Values[GC_NO_CACHE]:
    GC_Values[GC_CACHE_DIR] = None
  return True

def doGAMCheckForUpdates(forceCheck=False):
  import urllib2
  try:
    current_version = float(__version__)
  except ValueError:
    return
  now_time = calendar.timegm(time.gmtime())
  if not forceCheck:
    last_check_time = readFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], continueOnError=True, displayError=forceCheck)
    if last_check_time == None:
      last_check_time = 0
    if last_check_time > now_time-604800:
      return
  try:
    c = urllib2.urlopen(GAM_APPSPOT_LATEST_VERSION)
    try:
      latest_version = float(c.read())
    except ValueError:
      return
    if forceCheck or (latest_version > current_version):
      print u'Version: Check, Current: {0:.2f}, Latest: {1:.2f}'.format(current_version, latest_version)
    if latest_version <= current_version:
      writeFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
      return
    a = urllib2.urlopen(GAM_APPSPOT_LATEST_VERSION_ANNOUNCEMENT)
    announcement = a.read()
    sys.stderr.write(announcement)
    try:
      printLine(MESSAGE_HIT_CONTROL_C_TO_UPDATE)
      time.sleep(15)
    except KeyboardInterrupt:
      import webbrowser
      webbrowser.open(GAM_RELEASES)
      printLine(MESSAGE_GAM_EXITING_FOR_UPDATE)
      sys.exit(0)
    writeFile(GM_Globals[GM_LAST_UPDATE_CHECK_TXT], str(now_time), continueOnError=True, displayError=forceCheck)
    return
  except (urllib2.HTTPError, urllib2.URLError):
    return

def doGAMVersion():
  import struct
  print u'GAM {0} - {1}\n{2}\nPython {3}.{4}.{5} {6}-bit {7}\ngoogle-api-python-client {8}\n{9} {10}\nPath: {11}'.format(__version__, GAM_URL,
                                                                                                                         __author__,
                                                                                                                         sys.version_info[0], sys.version_info[1], sys.version_info[2],
                                                                                                                         struct.calcsize('P')*8, sys.version_info[3],
                                                                                                                         googleapiclient.__version__,
                                                                                                                         platform.platform(), platform.machine(),
                                                                                                                         GM_Globals[GM_GAM_PATH])

def tryOAuth(gdataObject):
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    doRequestOAuth()
    credentials = storage.get()
  if credentials.access_token_expired:
    credentials.refresh(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
  gdataObject.additional_headers = {u'Authorization': u'Bearer %s' % credentials.access_token}
  if not GC_Values[GC_DOMAIN]:
    GC_Values[GC_DOMAIN] = credentials.id_token.get(u'hd', UNKNOWN).lower()
  if not GC_Values[GC_CUSTOMER_ID]:
    GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  gdataObject.domain = GC_Values[GC_DOMAIN]
  return True

def checkGDataError(e, service):
  # First check for errors that need special handling
  if e[0].get(u'reason', u'') in [u'Token invalid - Invalid token: Stateless token expired', u'Token invalid - Invalid token: Token not found']:
    keep_domain = service.domain
    tryOAuth(service)
    service.domain = keep_domain
    return False
  if e[0][u'body'].startswith(u'Required field must not be blank:') or e[0][u'body'].startswith(u'These characters are not allowed:'):
    return e[0]['body']
  if e.error_code == 600 and e[0][u'body'] == u'Quota exceeded for the current request' or e[0][u'reason'] == u'Bad Gateway':
    return False
  if e.error_code == 600 and e[0][u'reason'] == u'Token invalid - Invalid token: Token disabled, revoked, or expired.':
    return u'403 - Token disabled, revoked, or expired. Please delete and re-create oauth.txt'
  # We got a "normal" error, define the mapping below
  error_code_map = {
    1000: False,
    1001: False,
    1002: u'Unauthorized and forbidden',
    1100: u'User deleted recently',
    1200: u'Domain user limit exceeded',
    1201: u'Domain alias limit exceeded',
    1202: u'Domain suspended',
    1203: u'Domain feature unavailable',
    1300: u'Entity %s exists' % getattr(e, u'invalidInput', u'<unknown>'),
    1301: u'Entity %s Does Not Exist' % getattr(e, u'invalidInput', u'<unknown>'),
    1302: u'Entity Name Is Reserved',
    1303: u'Entity %s name not valid' % getattr(e, u'invalidInput', u'<unknown>'),
    1306: u'%s has members. Cannot delete.' % getattr(e, u'invalidInput', u'<unknown>'),
    1400: u'Invalid Given Name',
    1401: u'Invalid Family Name',
    1402: u'Invalid Password',
    1403: u'Invalid Username',
    1404: u'Invalid Hash Function Name',
    1405: u'Invalid Hash Digest Length',
    1406: u'Invalid Email Address',
    1407: u'Invalid Query Parameter Value',
    1408: u'Invalid SSO Signing Key',
    1409: u'Invalid Encryption Public Key',
    1410: u'Feature Unavailable For User',
    1500: u'Too Many Recipients On Email List',
    1501: u'Too Many Aliases For User',
    1502: u'Too Many Delegates For User',
    1601: u'Duplicate Destinations',
    1602: u'Too Many Destinations',
    1603: u'Invalid Route Address',
    1700: u'Group Cannot Contain Cycle',
    1800: u'Group Cannot Contain Cycle',
    1801: u'Invalid value %s' % getattr(e, u'invalidInput', u'<unknown>'),
  }
  return u'{0} - {1}'.format(e.error_code, error_code_map.get(e.error_code, u'Unknown Error: {0}'.format(str(e))))

def callGData(service, function, soft_errors=False, throw_errors=[], **kwargs):
  import gdata.apps.service
  method = getattr(service, function)
  retries = 10
  for n in range(1, retries+1):
    try:
      return method(**kwargs)
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkGDataError(e, service)
      if e.error_code in throw_errors:
        raise
      if not terminating_error and n != retries:
        wait_on_fail = (2 ** n) if (2 ** n) < 60 else 60
        randomness = float(random.randint(1, 1000)) / 1000
        wait_on_fail = wait_on_fail + randomness
        if n > 3:
          sys.stderr.write(u'Temp error. Backing off %s seconds...' % (int(wait_on_fail)))
        time.sleep(wait_on_fail)
        if n > 3:
          sys.stderr.write(u'attempt %s/%s\n' % (n+1, retries))
        continue
      stderrErrorMsg(terminating_error)
      if soft_errors:
        if n != 1:
          sys.stderr.write(u' - Giving up.\n')
        return None
      sys.exit(int(e.error_code))

def callGAPI(service, function, silent_errors=False, soft_errors=False, throw_reasons=[], retry_reasons=[], **kwargs):
  method = getattr(service, function)
  retries = 10
  parameters = dict(kwargs.items() + GM_Globals[GM_EXTRA_ARGS_DICT].items())
  for n in range(1, retries+1):
    try:
      return method(**parameters).execute()
    except googleapiclient.errors.HttpError, e:
      try:
        error = json.loads(e.content)
      except ValueError:
        if n < 3:
          service._http.request.credentials.refresh(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL]))
          continue
        if (e.resp[u'status'] == u'503') and (e.content == u'Quota exceeded for the current request'):
          time.sleep(1)
          continue
        if not silent_errors:
          stderrErrorMsg(e.content)
        if soft_errors:
          return None
        sys.exit(5)
      http_status = error[u'error'][u'code']
      message = error[u'error'][u'errors'][0][u'message']
      try:
        reason = error[u'error'][u'errors'][0][u'reason']
      except KeyError:
        reason = http_status
      if reason in throw_reasons:
        raise e
      if n != retries and (reason in [u'quotaExceeded', u'rateLimitExceeded', u'userRateLimitExceeded', u'backendError', u'internalError'] or reason in retry_reasons):
        wait_on_fail = (2 ** n) if (2 ** n) < 60 else 60
        randomness = float(random.randint(1, 1000)) / 1000
        wait_on_fail = wait_on_fail + randomness
        if n > 3:
          sys.stderr.write(u'Temp error %s. Backing off %s seconds...' % (reason, int(wait_on_fail)))
        time.sleep(wait_on_fail)
        if n > 3:
          sys.stderr.write(u'attempt %s/%s\n' % (n+1, retries))
        continue
      stderrErrorMsg(u'{0}: {1} - {2}'.format(http_status, message, reason))
      if soft_errors:
        if n != 1:
          sys.stderr.write(u' - Giving up.\n')
        return None
      sys.exit(int(http_status))
    except oauth2client.client.AccessTokenRefreshError, e:
      stderrErrorMsg(u'Authentication Token Error: {0}'.format(e))
      sys.exit(403)
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()
    except TypeError, e:
      systemErrorExit(4, e)

def callGAPIpages(service, function, items=u'items', nextPageToken=u'nextPageToken', page_message=None, message_attribute=None, **kwargs):
  pageToken = None
  all_pages = list()
  total_items = 0
  while True:
    this_page = callGAPI(service=service, function=function, pageToken=pageToken, **kwargs)
    if this_page:
      pageToken = this_page.get(nextPageToken)
      if items in this_page:
        page_items = len(this_page[items])
        total_items += page_items
        all_pages.extend(this_page[items])
      else:
        this_page = {items: []}
        page_items = 0
    else:
      pageToken = None
      this_page = {items: []}
      page_items = 0
    if page_message:
      show_message = page_message.replace(u'%%num_items%%', str(page_items))
      show_message = show_message.replace(u'%%total_items%%', str(total_items))
      if message_attribute:
        try:
          show_message = show_message.replace(u'%%first_item%%', str(this_page[items][0][message_attribute]))
          show_message = show_message.replace(u'%%last_item%%', str(this_page[items][-1][message_attribute]))
        except (IndexError, KeyError):
          show_message = show_message.replace(u'%%first_item%%', '')
          show_message = show_message.replace(u'%%last_item%%', '')
      sys.stderr.write('\r')
      sys.stderr.flush()
      sys.stderr.write(show_message)
    if not pageToken:
      if page_message and (page_message[-1] != u'\n'):
        sys.stderr.write(u'\r\n')
        sys.stderr.flush()
      return all_pages

API_VER_MAPPING = {
  u'admin-settings': u'v1',
  u'appsactivity': u'v1',
  u'calendar': u'v3',
  u'classroom': u'v1',
  u'cloudprint': u'v2',
  u'datatransfer': u'datatransfer_v1',
  u'directory': u'directory_v1',
  u'drive': u'v2',
  u'gmail': u'v1',
  u'groupssettings': u'v1',
  u'licensing': u'v1',
  u'oauth2': u'v2',
  u'plus': u'v1',
  u'plusDomains': u'v1',
  u'reports': u'reports_v1',
  u'siteVerification': u'v1',
  }

def getAPIVer(api):
  return API_VER_MAPPING.get(api, u'v1')

API_SCOPE_MAPPING = {
  u'appsactivity': [u'https://www.googleapis.com/auth/activity',
                    u'https://www.googleapis.com/auth/drive'],
  u'calendar': [u'https://www.googleapis.com/auth/calendar',],
  u'drive': [u'https://www.googleapis.com/auth/drive',],
  u'gmail': [u'https://mail.google.com/',],
  u'plus': [u'https://www.googleapis.com/auth/plus.me',],
  u'plusDomains': [u'https://www.googleapis.com/auth/plus.me',
                   u'https://www.googleapis.com/auth/plus.circles.read',
                   u'https://www.googleapis.com/auth/plus.circles.write'],
}

def getAPIScope(api):
  return API_SCOPE_MAPPING.get(api, [])

def getServiceFromDiscoveryDocument(api, version, http):
  disc_filename = u'%s-%s.json' % (api, version)
  disc_file = os.path.join(GC_Values[GC_SITE_DIR], disc_filename)
  if hasattr(sys, '_MEIPASS'):
    pyinstaller_disc_file = os.path.join(sys._MEIPASS, disc_filename)
  else:
    pyinstaller_disc_file = None
  if os.path.isfile(disc_file):
    discovery = readFile(disc_file)
  elif pyinstaller_disc_file:
    discovery = readFile(pyinstaller_disc_file)
  else:
    systemErrorExit(4, MESSAGE_NO_DISCOVERY_INFORMATION.format(disc_file))
  return googleapiclient.discovery.build_from_document(discovery, base=u'https://www.googleapis.com', http=http)

def buildGAPIObject(api):
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  if not credentials or credentials.invalid:
    doRequestOAuth()
    credentials = storage.get()
  credentials.user_agent = GAM_INFO
  http = credentials.authorize(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL], cache=GC_Values[GC_CACHE_DIR]))
  version = getAPIVer(api)
  if api in [u'directory', u'reports', u'datatransfer']:
    api = u'admin'
  try:
    service = googleapiclient.discovery.build(api, version, http=http, cache_discovery=False)
  except googleapiclient.errors.UnknownApiNameOrVersion:
    service = getServiceFromDiscoveryDocument(api, version, http)
  except httplib2.ServerNotFoundError as e:
    systemErrorExit(4, e)
  except httplib2.CertificateValidationUnsupported:
    noPythonSSLExit()
  if GC_Values[GC_DOMAIN]:
    if not GC_Values[GC_CUSTOMER_ID]:
      resp, result = service._http.request(u'https://www.googleapis.com/admin/directory/v1/users?domain={0}&maxResults=1&fields=users(customerId)'.format(GC_Values[GC_DOMAIN]))
      try:
        resultObj = json.loads(result)
      except ValueError:
        systemErrorExit(8, u'Unexpected response: {0}'.format(result))
      if resp[u'status'] in [u'403', u'404']:
        try:
          message = resultObj[u'error'][u'errors'][0][u'message']
        except KeyError:
          message = resultObj[u'error'][u'message']
        systemErrorExit(8, u'{0} - {1}'.format(message, GC_Values[GC_DOMAIN]))
      try:
        GC_Values[GC_CUSTOMER_ID] = resultObj[u'users'][0][u'customerId']
      except KeyError:
        GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  else:
    GC_Values[GC_DOMAIN] = credentials.id_token.get(u'hd', UNKNOWN).lower()
    if not GC_Values[GC_CUSTOMER_ID]:
      GC_Values[GC_CUSTOMER_ID] = MY_CUSTOMER
  return service

def buildGAPIServiceObject(api, act_as, soft_errors=False):
  try:
    if not GM_Globals[GM_OAUTH2SERVICE_JSON_DATA]:
      json_string = readFile(GC_Values[GC_OAUTH2SERVICE_JSON], continueOnError=True, displayError=True)
      if not json_string:
        printLine(MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON)
        printLine(GAM_WIKI_CREATE_CLIENT_SECRETS)
        systemErrorExit(6, None)
      GM_Globals[GM_OAUTH2SERVICE_JSON_DATA] = json.loads(json_string)
    scopes = getAPIScope(api)
    credentials = oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_dict(GM_Globals[GM_OAUTH2SERVICE_JSON_DATA], scopes)
    credentials = credentials.create_delegated(act_as)
    credentials.user_agent = GAM_INFO
    serialization_data = credentials.serialization_data
    GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID] = serialization_data[u'client_id']
  except (ValueError, KeyError):
    printLine(MESSAGE_WIKI_INSTRUCTIONS_OAUTH2SERVICE_JSON)
    printLine(GAM_WIKI_CREATE_CLIENT_SECRETS)
    invalidJSONExit(GC_Values[GC_OAUTH2SERVICE_JSON])
  http = credentials.authorize(httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL],
                                             cache=GC_Values[GC_CACHE_DIR]))
  version = getAPIVer(api)
  try:
    return googleapiclient.discovery.build(api, version, http=http, cache_discovery=False)
  except googleapiclient.errors.UnknownApiNameOrVersion:
    return getServiceFromDiscoveryDocument(api, version, http)
  except httplib2.ServerNotFoundError as e:
    systemErrorExit(4, e)
  except oauth2client.client.AccessTokenRefreshError, e:
    if e.message in [u'access_denied',
                     u'unauthorized_client: Unauthorized client or scope in request.',
                     u'access_denied: Requested client not authorized.']:
      systemErrorExit(5, MESSAGE_CLIENT_API_ACCESS_DENIED.format(GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID], u','.join(scopes)))
    stderrErrorMsg(e)
    if soft_errors:
      return False
    sys.exit(4)

def buildDiscoveryObject(api):
  import uritemplate
  version = getAPIVer(api)
  if api in [u'directory', u'reports']:
    api = u'admin'
  params = {'api': api, 'apiVersion': version}
  http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL], cache=GC_Values[GC_CACHE_DIR])
  requested_url = uritemplate.expand(googleapiclient.discovery.DISCOVERY_URI, params)
  resp, content = http.request(requested_url)
  if resp.status == 404:
    raise googleapiclient.errors.UnknownApiNameOrVersion("name: %s  version: %s" % (api, version))
  if resp.status >= 400:
    raise googleapiclient.errors.HttpError(resp, content, uri=requested_url)
  try:
    return json.loads(content)
  except ValueError:
    stderrErrorMsg(u'Failed to parse as JSON: {0}'.format(content))
    raise googleapiclient.errors.InvalidJsonError()

def commonAppsObjInit(appsObj):
  if not tryOAuth(appsObj):
    doRequestOAuth()
    tryOAuth(appsObj)
  #Identify GAM to Google's Servers
  appsObj.source = GAM_INFO
  #Show debugging output if debug.gam exists
  if GC_Values[GC_DEBUG_LEVEL] > 0:
    appsObj.debug = True
  return appsObj

def getAdminSettingsObject():
  import gdata.apps.adminsettings.service
  return commonAppsObjInit(gdata.apps.adminsettings.service.AdminSettingsService())

def getAuditObject():
  import gdata.apps.audit.service
  return commonAppsObjInit(gdata.apps.audit.service.AuditService())

def getEmailSettingsObject():
  import gdata.apps.emailsettings.service
  return commonAppsObjInit(gdata.apps.emailsettings.service.EmailSettingsService())

def geturl(url, dst):
  import urllib2
  u = urllib2.urlopen(url)
  f = openFile(dst, u'wb')
  meta = u.info()
  try:
    file_size = int(meta.getheaders(u'Content-Length')[0])
  except IndexError:
    file_size = -1
  file_size_dl = 0
  block_sz = 8192
  while True:
    filebuff = u.read(block_sz)
    if not filebuff:
      break
    file_size_dl += len(filebuff)
    f.write(filebuff)
    if file_size != -1:
      status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
    else:
      status = r"%10d [unknown size]" % (file_size_dl)
    status = status + chr(8)*(len(status)+1)
    print status,
  closeFile(f)

def showReport():
  rep = buildGAPIObject(u'reports')
  report = sys.argv[2].lower()
  customerId = GC_Values[GC_CUSTOMER_ID]
  if customerId == MY_CUSTOMER:
    customerId = None
  date = filters = parameters = actorIpAddress = startTime = endTime = eventName = None
  to_drive = False
  userKey = 'all'
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'date':
      date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'start':
      startTime = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'end':
      endTime = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'event':
      eventName = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'user':
      userKey = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'filter', u'filters']:
      filters = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'fields', u'parameters']:
      parameters = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'ip':
      actorIpAddress = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      to_drive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument to "gam report"' % sys.argv[i]
      sys.exit(2)
  try_date = date
  if try_date == None:
    try_date = datetime.date.today()
  if report in [u'users', u'user']:
    while True:
      try:
        page_message = u'Got %%num_items%% users\n'
        usage = callGAPIpages(service=rep.userUsageReport(), function=u'get', items=u'usageReports', page_message=page_message, throw_reasons=[u'invalid'],
                              date=str(try_date), userKey=userKey, customerId=customerId, filters=filters, parameters=parameters)
        break
      except googleapiclient.errors.HttpError, e:
        error = json.loads(e.content)
      try:
        message = error[u'error'][u'errors'][0][u'message']
      except KeyError:
        raise
      match_date = re.match(u'Data for dates later than (.*) is not yet available. Please check back later', message)
      if not match_date:
        print u'Error: %s' % message
        sys.exit(4)
      else:
        try_date = match_date.group(1)
    user_attributes = []
    titles = [u'email', u'date']
    for user_report in usage:
      row = {u'email': user_report[u'entity'][u'userEmail'], u'date': str(try_date)}
      try:
        for report_item in user_report[u'parameters']:
          items = report_item.values()
          name = items[1]
          value = items[0]
          if not name in titles:
            titles.append(name)
          row[name] = value
      except KeyError:
        pass
      user_attributes.append(row)
    header = {}
    for title in titles:
      header[title] = title
    user_attributes.insert(0, header)
    output_csv(user_attributes, titles, u'User Reports - %s' % try_date, to_drive)
  elif report in [u'customer', u'customers', u'domain']:
    while True:
      try:
        usage = callGAPIpages(service=rep.customerUsageReports(), function=u'get', items=u'usageReports', throw_reasons=[u'invalid'],
                              customerId=customerId, date=str(try_date), parameters=parameters)
        break
      except googleapiclient.errors.HttpError, e:
        error = json.loads(e.content)
      try:
        message = error[u'error'][u'errors'][0][u'message']
      except KeyError:
        raise
      match_date = re.match(u'Data for dates later than (.*) is not yet available. Please check back later', message)
      if not match_date:
        print u'Error: %s' % message
        sys.exit(4)
      else:
        try_date = match_date.group(1)
    cust_attributes = [{u'name': u'name', u'value': u'value', u'client_id': u'client_id'}]
    titles = [u'name', u'value', u'client_id']
    auth_apps = list()
    for item in usage[0][u'parameters']:
      name = item[u'name']
      try:
        value = item[u'intValue']
      except KeyError:
        if name == u'accounts:authorized_apps':
          for subitem in item[u'msgValue']:
            app = dict()
            for an_item in subitem:
              if an_item == u'client_name':
                app['name'] = u'App: %s' % subitem[an_item]
              elif an_item == u'num_users':
                app['value'] = u'%s users' % subitem[an_item]
              elif an_item == u'client_id':
                app[u'client_id'] = subitem[an_item]
            auth_apps.append(app)
        continue
      cust_attributes.append({u'name': name, u'value': value})
    for app in auth_apps: # put apps at bottom
      cust_attributes.append(app)
    output_csv(csv_list=cust_attributes, titles=titles, list_type=u'Customer Report - %s' % try_date, todrive=to_drive)
  elif report in [u'doc', u'docs', u'calendar', u'calendars', u'login', u'logins', u'admin', u'drive', u'token', u'tokens']:
    if report in [u'doc', u'docs']:
      report = u'drive'
    elif report in [u'calendars']:
      report = u'calendar'
    elif report == u'logins':
      report = u'login'
    elif report == u'tokens':
      report = u'token'
    page_message = u'Got %%num_items%% items\n'
    activities = callGAPIpages(service=rep.activities(), function=u'list', page_message=page_message, applicationName=report,
                               userKey=userKey, customerId=customerId, actorIpAddress=actorIpAddress,
                               startTime=startTime, endTime=endTime, eventName=eventName, filters=filters)
    if len(activities) > 0:
      attrs = []
      titles = []
      for activity in activities:
        events = activity[u'events']
        del activity[u'events']
        activity_row = flatten_json(activity)
        for event in events:
          row = flatten_json(event)
          row.update(activity_row)
          for item in row:
            if item not in titles:
              titles.append(item)
          attrs.append(row)
      header = {}
      titles.remove(u'name')
      titles = sorted(titles)
      titles.insert(0, u'name')
      for title in titles:
        header[title] = title
      attrs.insert(0, header)
      cap_report = u'%s%s' % (report[0].upper(), report[1:])
      output_csv(attrs, titles, u'%s Activity Report' % cap_report, to_drive)

def doDelegates(users):
  import gdata.apps.service
  emailsettings = getEmailSettingsObject()
  if sys.argv[4].lower() == u'to':
    delegate = sys.argv[5].lower()
    if not delegate.find(u'@') > 0:
      delegate_domain = GC_Values[GC_DOMAIN].lower()
      delegate_email = u'%s@%s' % (delegate, delegate_domain)
    else:
      delegate_domain = delegate[delegate.find(u'@')+1:].lower()
      delegate_email = delegate
  else:
    print 'ERROR: %s is not a valid argument for "gam <users> delegate", expected to' % sys.argv[4]
    sys.exit(2)
  count = len(users)
  i = 1
  for delegator in users:
    if delegator.find(u'@') > 0:
      delegator_domain = delegator[delegator.find('@')+1:].lower()
      delegator_email = delegator
      delegator = delegator[:delegator.find('@')]
    else:
      delegator_domain = GC_Values[GC_DOMAIN].lower()
      delegator_email = u'%s@%s' % (delegator, delegator_domain)
    emailsettings.domain = delegator_domain
    print u"Giving %s delegate access to %s (%s of %s)" % (delegate_email, delegator_email, i, count)
    i += 1
    delete_alias = False
    if delegate_domain == delegator_domain:
      use_delegate_address = delegate_email
    else:
      # Need to use an alias in delegator domain, first check to see if delegate already has one...
      cd = buildGAPIObject(u'directory')
      aliases = callGAPI(service=cd.users().aliases(), function=u'list', userKey=delegate_email)
      found_alias_in_delegator_domain = False
      try:
        for alias in aliases[u'aliases']:
          alias_domain = alias[u'alias'][alias[u'alias'].find(u'@')+1:].lower()
          if alias_domain == delegator_domain:
            use_delegate_address = alias[u'alias']
            print u'  Using existing alias %s for delegation' % use_delegate_address
            found_alias_in_delegator_domain = True
            break
      except KeyError:
        pass
      if not found_alias_in_delegator_domain:
        delete_alias = True
        use_delegate_address = u'%s@%s' % (''.join(random.sample(u'abcdefghijklmnopqrstuvwxyz0123456789', 25)), delegator_domain)
        print u'  Giving %s temporary alias %s for delegation' % (delegate_email, use_delegate_address)
        callGAPI(service=cd.users().aliases(), function=u'insert', userKey=delegate_email, body={u'alias': use_delegate_address})
        time.sleep(5)
    retries = 10
    for n in range(1, retries+1):
      try:
        callGData(service=emailsettings, function=u'CreateDelegate', throw_errors=[600, 1000, 1001], delegate=use_delegate_address, delegator=delegator)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        # 1st check to see if delegation already exists (causes 1000 error on create when using alias)
        get_delegates = callGData(service=emailsettings, function=u'GetDelegates', delegator=delegator)
        for get_delegate in get_delegates:
          if get_delegate[u'address'].lower() == delegate_email: # Delegation is already in place
            print u'That delegation is already in place...'
            if delete_alias:
              print u'  Deleting temporary alias...'
              doDeleteAlias(alias_email=use_delegate_address)
            sys.exit(0) # Emulate functionality of duplicate delegation between users in same domain, returning clean
        # Now check if either user account is suspended or requires password change
        cd = buildGAPIObject(u'directory')
        delegate_user_details = callGAPI(service=cd.users(), function=u'get', userKey=delegate_email)
        delegator_user_details = callGAPI(service=cd.users(), function=u'get', userKey=delegator_email)
        if delegate_user_details[u'suspended'] == True:
          stderrErrorMsg(u'User {0} is suspended. You must unsuspend for delegation.'.format(delegate_email))
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegator_user_details[u'suspended'] == True:
          stderrErrorMsg(u'User {0} is suspended. You must unsuspend for delegation.'.format(delegator_email))
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegate_user_details[u'changePasswordAtNextLogin'] == True:
          stderrErrorMsg(u'User {0} is required to change password at next login. You must change password or clear changepassword flag for delegation.'.format(delegate_email))
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)
        if delegator_user_details[u'changePasswordAtNextLogin'] == True:
          stderrErrorMsg(u'User {0} is required to change password at next login. You must change password or clear changepassword flag for delegation.'.format(delegator_email))
          if delete_alias:
            doDeleteAlias(alias_email=use_delegate_address)
          sys.exit(5)

        # Guess it was just a normal backoff error then?
        if n == retries:
          sys.stderr.write(u' - giving up.')
          sys.exit(e.error_code)
        wait_on_fail = (2 ** n) if (2 ** n) < 60 else 60
        randomness = float(random.randint(1, 1000)) / 1000
        wait_on_fail = wait_on_fail + randomness
        if n > 3:
          sys.stderr.write(u'Temp error. Backing off %s seconds...' % (int(wait_on_fail)))
        time.sleep(wait_on_fail)
        if n > 3:
          sys.stderr.write(u'attempt %s/%s\n' % (n+1, retries))
    time.sleep(10) # on success, sleep 10 seconds before exiting or moving on to next user to prevent ghost delegates
    if delete_alias:
      doDeleteAlias(alias_email=use_delegate_address)

def gen_sha512_hash(password):
  from passlib.handlers.sha2_crypt import sha512_crypt
  return sha512_crypt.encrypt(password, rounds=5000)

def getDelegates(users):
  emailsettings = getEmailSettingsObject()
  csv_format = False
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'csv':
      csv_format = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> show delegates"' % sys.argv[i]
      sys.exit(2)
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    sys.stderr.write(u"Getting delegates for %s...\n" % (user + '@' + emailsettings.domain))
    delegates = callGData(service=emailsettings, function=u'GetDelegates', soft_errors=True, delegator=user)
    try:
      for delegate in delegates:
        if csv_format:
          print u'%s,%s,%s' % (user + u'@' + emailsettings.domain, delegate[u'address'], delegate[u'status'])
        else:
          print u"Delegator: %s\n Delegate: %s\n Status: %s\n Delegate Email: %s\n Delegate ID: %s\n" % (user, delegate[u'delegate'], delegate[u'status'], delegate[u'address'], delegate[u'delegationId'])
    except TypeError:
      pass

def deleteDelegate(users):
  emailsettings = getEmailSettingsObject()
  delegate = sys.argv[5]
  if not delegate.find(u'@') > 0:
    if users[0].find(u'@') > 0:
      delegatedomain = users[0][users[0].find(u'@')+1:]
    else:
      delegatedomain = GC_Values[GC_DOMAIN]
    delegate = delegate+u'@'+delegatedomain
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Deleting %s delegate access to %s (%s of %s)" % (delegate, user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'DeleteDelegate', delegate=delegate, delegator=user)

def doAddCourseParticipant():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[2]
  body_attribute = u'userId'
  if len(courseId) < 3 or (not courseId.isdigit() and courseId[:2] != u'd:'):
    courseId = u'd:%s' % courseId
  participant_type = sys.argv[4].lower()
  new_id = sys.argv[5]
  if participant_type in [u'teacher', u'teachers']:
    service = croom.courses().teachers()
  elif participant_type in [u'students', u'student']:
    service = croom.courses().students()
  elif participant_type in [u'alias']:
    service = croom.courses().aliases()
    body_attribute = u'alias'
    if new_id[1] != u':':
      new_id = u'd:%s' % new_id
  else:
    print u'ERROR: %s is not a valid argument to "gam course ID add"' % participant_type
    sys.exit(2)
  body = {body_attribute: new_id}
  callGAPI(service=service, function=u'create', courseId=courseId, body=body)
  if courseId[:2] == u'd:':
    courseId = courseId[2:]
  if new_id[:2] == u'd:':
    new_id = new_id[2:]
  print u'Added %s as a %s of course %s' % (new_id, participant_type, courseId)

def doSyncCourseParticipants():
  courseId = sys.argv[2]
  if not courseId.isdigit() and courseId[:2] != u'd:':
    courseId = u'd:%s' % courseId
  participant_type = sys.argv[4].lower()
  diff_entity_type = sys.argv[5]
  diff_entity = sys.argv[6]
  current_course_users = getUsersToModify(entity_type=participant_type, entity=courseId)
  print
  current_course_users = [x.lower() for x in current_course_users]
  if diff_entity_type == u'courseparticipants':
    diff_entity_type = participant_type
  diff_against_users = getUsersToModify(entity_type=diff_entity_type, entity=diff_entity)
  print
  diff_against_users = [x.lower() for x in diff_against_users]
  to_add = list(set(diff_against_users) - set(current_course_users))
  to_remove = list(set(current_course_users) - set(diff_against_users))
  gam_commands = []
  for add_email in to_add:
    gam_commands.append([u'course', courseId, u'add', participant_type, add_email])
  for remove_email in to_remove:
    gam_commands.append([u'course', courseId, u'remove', participant_type, remove_email])
  run_batch(items=gam_commands)

def doDelCourseParticipant():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[2]
  if not courseId.isdigit() and courseId[:2] != u'd:':
    courseId = u'd:%s' % courseId
  participant_type = sys.argv[4].lower()
  remove_id = sys.argv[5]
  kwargs = {}
  if participant_type in [u'teacher', u'teachers']:
    service = croom.courses().teachers()
    kwargs[u'userId'] = remove_id
  elif participant_type in [u'student', u'students']:
    service = croom.courses().students()
    kwargs[u'userId'] = remove_id
  elif participant_type in [u'alias']:
    service = croom.courses().aliases()
    if remove_id[1] != u':':
      remove_id = u'd:%s' % remove_id
    kwargs[u'alias'] = remove_id
  else:
    print u'ERROR: %s is not a valid argument to "gam course ID delete"' % participant_type
    sys.exit(2)
  callGAPI(service=service, function=u'delete', courseId=courseId, **kwargs)
  if courseId[:2] == u'd:':
    courseId = courseId[2:]
  if remove_id[:2] == u'd:':
    remove_id = remove_id[2:]
  print u'Removed %s as a %s of course %s' % (remove_id, participant_type, courseId)

def doDelCourse():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[3]
  if not courseId.isdigit():
    courseId = u'd:%s' % courseId
  callGAPI(service=croom.courses(), function=u'delete', id=courseId)
  print u'Deleted Course %s' % courseId

def doUpdateCourse():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[3]
  if not courseId.isdigit():
    courseId = u'd:%s' % courseId
  body = {}
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'section':
      body[u'section'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'heading':
      body[u'descriptionHeading'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'room':
      body[u'room'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'state', u'status']:
      body[u'courseState'] = sys.argv[i+1].upper()
      if body[u'courseState'] not in [u'ACTIVE', u'ARCHIVED', u'PROVISIONED', u'DECLINED']:
        print 'ERROR: course state can be active or archived. Got %s' % body[u'courseState']
        sys.exit(2)
      i += 2
    else:
      print u'ERROR: %s is not a valid argument to "gam update course"' % sys.argv[i]
      sys.exit(2)
  updateMask = u','.join(body.keys())
  body[u'id'] = courseId
  result = callGAPI(service=croom.courses(), function=u'patch', id=courseId, body=body, updateMask=updateMask)
  print u'Updated Course %s' % result[u'id']

def doCreateDomain():
  cd = buildGAPIObject(u'directory')
  domain_name = sys.argv[3]
  body = {u'domainName': domain_name}
  callGAPI(service=cd.domains(), function=u'insert', customer=GC_Values[GC_CUSTOMER_ID], body=body)
  print u'Added domain %s' % domain_name

def doCreateDomainAlias():
  cd = buildGAPIObject(u'directory')
  body = {}
  body[u'domainAliasName'] = sys.argv[3]
  body[u'parentDomainName'] = sys.argv[4]
  callGAPI(service=cd.domainAliases(), function=u'insert', customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doUpdateDomain():
  cd = buildGAPIObject(u'directory')
  domain_name = sys.argv[3]
  i = 4
  body = {}
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'primary':
      body[u'customerDomain'] = domain_name
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam update domain"' % sys.argv[i]
      sys.exit(2)
  callGAPI(service=cd.customers(), function=u'update', customerKey=GC_Values[GC_CUSTOMER_ID], body=body)
  print u'%s is now the primary domain.' % domain_name

def doGetDomainInfo():
  if (len(sys.argv) < 4) or (sys.argv[3] == u'logo'):
    doGetInstanceInfo()
    return
  cd = buildGAPIObject(u'directory')
  domainName = sys.argv[3]
  result = callGAPI(service=cd.domains(), function=u'get', customer=GC_Values[GC_CUSTOMER_ID], domainName=domainName)
  if u'creationTime' in result:
    result[u'creationTime'] = unicode(datetime.datetime.fromtimestamp(int(result[u'creationTime'])/1000))
  if u'domainAliases' in result:
    for i in range(0, len(result[u'domainAliases'])):
      if u'creationTime' in result[u'domainAliases'][i]:
        result[u'domainAliases'][i][u'creationTime'] = unicode(datetime.datetime.fromtimestamp(int(result[u'domainAliases'][i][u'creationTime'])/1000))
  print_json(None, result)

def doGetDomainAliasInfo():
  cd = buildGAPIObject(u'directory')
  alias = sys.argv[3]
  result = callGAPI(service=cd.domainAliases(), function=u'get', customer=GC_Values[GC_CUSTOMER_ID], domainAliasName=alias)
  if u'creationTime' in result:
    result[u'creationTime'] = unicode(datetime.datetime.fromtimestamp(int(result[u'creationTime'])/1000))
  print_json(None, result)

def doGetCustomerInfo():
  cd = buildGAPIObject(u'directory')
  customer_info = callGAPI(service=cd.customers(), function=u'get', customerKey=GC_Values[GC_CUSTOMER_ID])
  print_json(None, customer_info)

def doUpdateCustomer():
  cd = buildGAPIObject(u'directory')
  body = {}
  i = 3
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'alternateemail':
      body[u'alternateEmail'] = sys.argv[i+1]
      i += 2
    elif myarg in [u'contactname', u'organizationname', u'locality', u'region', u'countrycode', u'addressline1', u'addressline2', u'addressline3', u'postalcode']:
      if u'postalAddress' not in body:
        body[u'postalAddress'] = {}
      if myarg == u'contactname':
        myarg = u'contactName'
      elif myarg == u'organizationname':
        myarg = u'organizationName'
      elif myarg == u'countrycode':
        myarg = u'countryCode'
      elif myarg == u'addressline1':
        myarg = u'addressLine1'
      elif myarg == u'addressline2':
        myarg = u'addressLine2'
      elif myarg == u'addressline3':
        myarg = u'addressLine3'
      elif myarg == u'postalcode':
        myarg = u'postalCode'
      body[u'postalAddress'][myarg] = sys.argv[i+1]
      i += 2
    elif myarg in [u'phone', u'phonenumber']:
      body[u'phoneNumber'] = sys.argv[i+1]
      i += 2
    elif myarg == u'language':
      body[u'language'] = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam update customer"' % myarg
      sys.exit(2)
  callGAPI(service=cd.customers(), function=u'update', customerKey=GC_Values[GC_CUSTOMER_ID], body=body)
  print u'Updated customer'

def doDelDomain():
  cd = buildGAPIObject(u'directory')
  domainName = sys.argv[3]
  callGAPI(service=cd.domains(), function=u'delete', customer=GC_Values[GC_CUSTOMER_ID], domainName=domainName)

def doDelDomainAlias():
  cd = buildGAPIObject(u'directory')
  domainAliasName = sys.argv[3]
  callGAPI(service=cd.domainAliases(), function=u'delete', customer=GC_Values[GC_CUSTOMER_ID], domainAliasName=domainAliasName)

def doPrintDomains():
  cd = buildGAPIObject(u'directory')
  titles = []
  domains_attributes = [{}]
  todrive = False
  domains = callGAPI(service=cd.domains(), function=u'list', customer=GC_Values[GC_CUSTOMER_ID])
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam print domains".' % sys.argv[i]
      sys.exit(2)
  for domain in domains[u'domains']:
    domain_attributes = {}
    if domain[u'isPrimary'] == True:
      domain[u'type'] = u'primary'
    else:
      domain[u'type'] = u'secondary'
    for attr in domain:
      if attr in [u'kind', u'domainAliases', u'etag', u'etags', u'isPrimary']:
        continue
      elif attr in [u'creationTime',]:
        domain[attr] = unicode(datetime.datetime.fromtimestamp(int(domain[attr])/1000))
      if attr not in titles:
        titles.append(attr)
        domains_attributes[0][attr] = attr
      domain_attributes[attr] = domain[attr]
    domains_attributes.append(domain_attributes)
    if u'domainAliases' in domain:
      for aliasdomain in domain[u'domainAliases']:
        aliasdomain[u'domainName'] = aliasdomain[u'domainAliasName']
        del aliasdomain[u'domainAliasName']
        aliasdomain[u'type'] = u'alias'
        aliasdomain_attributes = {}
        for attr in aliasdomain:
          if attr in [u'kind', u'etag']:
            continue
          elif attr in [u'creationTime',]:
            aliasdomain[attr] = unicode(datetime.datetime.fromtimestamp(int(aliasdomain[attr])/1000))
          if attr not in titles:
            titles.append(attr)
            domains_attributes[0][attr] = attr
          aliasdomain_attributes[attr] = aliasdomain[attr]
        domains_attributes.append(aliasdomain_attributes)
  output_csv(domains_attributes, titles, u'Domains', todrive)

def doDelAdmin():
  cd = buildGAPIObject(u'directory')
  roleAssignmentId = sys.argv[3]
  print u'Deleting Admin Role Assignment %s' % roleAssignmentId
  callGAPI(service=cd.roleAssignments(), function=u'delete',
           customer=GC_Values[GC_CUSTOMER_ID], roleAssignmentId=roleAssignmentId)

def doCreateAdmin():
  cd = buildGAPIObject(u'directory')
  body = {}
  user = sys.argv[3]
  if user[:4].lower() == u'uid:':
    body[u'assignedTo'] = user[4:]
  else:
    print user[:3]
    body[u'assignedTo'] = callGAPI(service=cd.users(), function=u'get',
                                   userKey=user, projection=u'basic', fields=u'id')[u'id']
  role = sys.argv[4]
  if role[:4].lower() == u'uid:':
    body[u'roleId'] = role[4:]
  else:
    body[u'roleId'] = roleid_from_role(role)
  if not body[u'roleId']:
    print u'ERROR: %s is not a valid role. Please ensure role name is exactly as shown in admin console.' % role
    sys.exit(4)
  body[u'scopeType'] = sys.argv[5].upper()
  if body[u'scopeType'] not in [u'CUSTOMER', u'ORG_UNIT']:
    print u'ERROR: scope type must be customer or org_unit, got %s' % body[u'scopeType']
    sys.exit(3)
  if body[u'scopeType'] == u'ORG_UNIT':
    orgUnit = sys.argv[6]
    if orgUnit[:3] == u'id:':
      body[u'orgUnitId'] = orgUnit[3:]
    elif orgUnit[:4] == u'uid:':
      body[u'orgUnitId'] = orgUnit[4:]
    else:
      if orgUnit[0] == u'/':
        orgUnit = orgUnit[1:]
      body[u'orgUnitId'] = callGAPI(service=cd.orgunits(), function=u'get',
                                    customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnit,
                                    fields=u'orgUnitId')[u'orgUnitId'][3:]
  if body[u'scopeType'] == u'CUSTOMER':
    scope = u'customer'
  else:
    scope = orgUnit
  print u'Giving %s admin role %s for %s' % (user, role, scope)
  callGAPI(service=cd.roleAssignments(), function=u'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doPrintAdminRoles():
  cd = buildGAPIObject(u'directory')
  roles = callGAPIpages(service=cd.roles(), function=u'list', items=u'items',
                        customer=GC_Values[GC_CUSTOMER_ID])
  roles_attrib = [{}]
  for role in roles:
    role_attrib = {}
    for key, value in role.items():
      if key in [u'kind', u'etag', u'etags']:
        continue
      if not isinstance(value, (str, unicode, bool)):
        continue
      if key not in roles_attrib[0]:
        roles_attrib[0][key] = key
      role_attrib[key] = value
    roles_attrib.append(role_attrib)
  output_csv(roles_attrib, roles_attrib[0], u'Admin Roles', False)

def doPrintAdmins():
  cd = buildGAPIObject(u'directory')
  roleId = None
  userKey = None
  todrive = False
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'user':
      userKey = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'role':
      role = sys.argv[i+1]
      if role[:4].lower() == u'uid:':
        roleId = role[4:]
      else:
        roleId = roleid_from_role(role)
        if not roleId:
          print u'ERROR: %s is not a valid role' % role
          sys.exit(5)
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam print admins".' % sys.argv[i]
      sys.exit(2)
  admins = callGAPIpages(service=cd.roleAssignments(), function=u'list',
                         customer=GC_Values[GC_CUSTOMER_ID], userKey=userKey, roleId=roleId, maxResults=200)
  admins_attrib = [{}]
  for admin in admins:
    admin_attrib = {}
    for key, value in admin.items():
      if key in [u'kind', u'etag']:
        continue
      if key not in admins_attrib[0]:
        admins_attrib[0][key] = key
      admin_attrib[key] = value
      if key == u'assignedTo':
        assignedToUser = user_from_userid(value)
        if u'assignedToUser' not in admins_attrib[0]:
          admins_attrib[0][u'assignedToUser'] = u'assignedToUser'
        admin_attrib[u'assignedToUser'] = assignedToUser
      elif key == u'roleId':
        role = role_from_roleid(value)
        if u'role' not in admins_attrib[0]:
          admins_attrib[0][u'role'] = u'role'
        admin_attrib[u'role'] = role
      elif key == u'orgUnitId':
        orgUnit = orgunit_from_orgunitid(value)
        if u'orgUnit' not in admins_attrib[0]:
          admins_attrib[0][u'orgUnit'] = u'orgUnit'
        admin_attrib[u'orgUnit'] = orgUnit
    admins_attrib.append(admin_attrib)
  output_csv(admins_attrib, admins_attrib[0], u'Admins', todrive)

def buildOrgUnitIdToNameMap():
  cd = buildGAPIObject(u'directory')
  result = callGAPI(service=cd.orgunits(), function=u'list',
                    customerId=GC_Values[GC_CUSTOMER_ID],
                    fields=u'organizationUnits(orgUnitPath,orgUnitId)')
  GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME] = {}
  for orgUnit in result[u'organizationUnits']:
    GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME][orgUnit[u'orgUnitId']] = orgUnit[u'orgUnitPath']

def orgunit_from_orgunitid(orgunitid):
  if not GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME]:
    buildOrgUnitIdToNameMap()
  return GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME][u'id:%s' % orgunitid]

def buildRoleIdToNameToIdMap():
  cd = buildGAPIObject(u'directory')
  result = callGAPIpages(service=cd.roles(), function=u'list', items=u'items',
                         customer=GC_Values[GC_CUSTOMER_ID],
                         fields=u'nextPageToken,items(roleId,roleName)',
                         maxResults=100)
  GM_Globals[GM_MAP_ROLE_ID_TO_NAME] = {}
  GM_Globals[GM_MAP_ROLE_NAME_TO_ID] = {}
  for role in result:
    GM_Globals[GM_MAP_ROLE_ID_TO_NAME][role[u'roleId']] = role[u'roleName']
    GM_Globals[GM_MAP_ROLE_NAME_TO_ID][role[u'roleName']] = role[u'roleId']

def role_from_roleid(roleid):
  if not GM_Globals[GM_MAP_ROLE_ID_TO_NAME]:
    buildRoleIdToNameToIdMap()
  return GM_Globals[GM_MAP_ROLE_ID_TO_NAME][roleid]

def roleid_from_role(role):
  if not GM_Globals[GM_MAP_ROLE_NAME_TO_ID]:
    buildRoleIdToNameToIdMap()
  return GM_Globals[GM_MAP_ROLE_NAME_TO_ID].get(role, None)

def buildUserIdToNameMap():
  cd = buildGAPIObject(u'directory')
  result = callGAPIpages(service=cd.users(), function=u'list', items=u'users',
                         customer=GC_Values[GC_CUSTOMER_ID],
                         fields=u'nextPageToken,users(id,primaryEmail)',
                         maxResults=GC_Values[GC_USER_MAX_RESULTS])
  GM_Globals[GM_MAP_USER_ID_TO_NAME] = {}
  for user in result:
    GM_Globals[GM_MAP_USER_ID_TO_NAME][user[u'id']] = user[u'primaryEmail']

def user_from_userid(userid):
  if not GM_Globals[GM_MAP_USER_ID_TO_NAME]:
    buildUserIdToNameMap()
  return GM_Globals[GM_MAP_USER_ID_TO_NAME].get(userid, '')

SERVICE_NAME_TO_ID_MAP = {
  u'Drive': u'55656082996',
  u'Google+': '553547912911',
  }

def appID2app(dt, appID):
  for serviceName, serviceID in SERVICE_NAME_TO_ID_MAP.items():
    if appID == serviceID:
      return serviceName
  online_services = callGAPIpages(service=dt.applications(), function=u'list', items=u'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for online_service in online_services:
    if appID == online_service[u'id']:
      return online_service[u'name']
  print u'ERROR: %s is not a valid app ID for data transfer.' % appID
  sys.exit(2)

SERVICE_NAME_CHOICES_MAP = {
  u'googleplus': u'Google+',
  u'gplus': u'Google+',
  u'g+': u'Google+',
  u'googledrive': u'Drive',
  u'gdrive': u'Drive',
  }

def app2appID(dt, app):
  serviceName = app.lower()
  if serviceName in SERVICE_NAME_CHOICES_MAP:
    return (SERVICE_NAME_CHOICES_MAP[serviceName], SERVICE_NAME_TO_ID_MAP[SERVICE_NAME_CHOICES_MAP[serviceName]])
  online_services = callGAPIpages(service=dt.applications(), function=u'list', items=u'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for online_service in online_services:
    if serviceName == online_service[u'name'].lower():
      return online_service[u'id']
  print u'ERROR: %s is not a valid service for data transfer.' % app
  sys.exit(2)

def convertToUserID(user):
  if user[:4].lower() == u'uid:':
    return user[4:]
  cd = buildGAPIObject(u'directory')
  if user.find(u'@') == -1:
    user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
  try:
    return callGAPI(service=cd.users(), function=u'get', throw_reasons=[u'notFound'], userKey=user, fields=u'id')[u'id']
  except googleapiclient.errors.HttpError:
    print u'ERROR: no such user %s' % user
    sys.exit(3)

def convertUserIDtoEmail(uid):
  cd = buildGAPIObject(u'directory')
  try:
    return callGAPI(service=cd.users(), function=u'get', throw_reasons=[u'notFound'], userKey=uid, fields=u'primaryEmail')[u'primaryEmail']
  except googleapiclient.errors.HttpError:
    print u'ERROR: no such user %s' % id
    sys.exit(3)

def doCreateDataTranfer():
  dt = buildGAPIObject(u'datatransfer')
  body = {}
  old_owner = sys.argv[3]
  body[u'oldOwnerUserId'] = convertToUserID(old_owner)
  service = sys.argv[4]
  new_owner = sys.argv[5]
  body[u'newOwnerUserId'] = convertToUserID(new_owner)
  parameters = {}
  i = 6
  while i < len(sys.argv):
    parameters[sys.argv[i].upper()] = sys.argv[i+1].upper().split(u',')
    i += 2
  body[u'applicationDataTransfers'] = [{u'applicationId': app2appID(dt, service)}]
  for key in parameters:
    if u'applicationDataTransferParams' not in body[u'applicationDataTransfers'][0]:
      body[u'applicationDataTransfers'][0][u'applicationTransferParams'] = []
    body[u'applicationDataTransfers'][0][u'applicationTransferParams'].append({u'key': key, u'value': parameters[key]})
  result = callGAPI(service=dt.transfers(), function=u'insert', body=body, fields=u'id')[u'id']
  print u'Submitted request id %s to transfer %s from %s to %s' % (result, service, old_owner, new_owner)

def doPrintTransferApps():
  dt = buildGAPIObject(u'datatransfer')
  apps = callGAPIpages(service=dt.applications(), function=u'list', items=u'applications', customerId=GC_Values[GC_CUSTOMER_ID])
  for app in apps:
    print_json(None, app)
    print

def doPrintDataTransfers():
  dt = buildGAPIObject(u'datatransfer')
  i = 3
  newOwnerUserId = None
  oldOwnerUserId = None
  status = None
  todrive = False
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', '') in [u'olduser', u'oldowner']:
      oldOwnerUserId = convertToUserID(sys.argv[i+1])
      i += 2
    elif sys.argv[i].lower().replace(u'_', '') in [u'newuser', u'newowner']:
      newOwnerUserId = convertToUserID(sys.argv[i+1])
      i += 2
    elif sys.argv[i].lower() == u'status':
      status = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam print transfers"' % sys.argv[i]
      sys.exit(2)
  transfers_attributes = [{}]
  transfers = callGAPIpages(service=dt.transfers(), function=u'list',
                            items=u'dataTransfers', customerId=GC_Values[GC_CUSTOMER_ID], status=status,
                            newOwnerUserId=newOwnerUserId, oldOwnerUserId=oldOwnerUserId)
  for transfer in transfers:
    for i in range(0, len(transfer[u'applicationDataTransfers'])):
      a_transfer = dict()
      a_transfer[u'oldOwnerUserEmail'] = convertUserIDtoEmail(transfer[u'oldOwnerUserId'])
      a_transfer[u'newOwnerUserEmail'] = convertUserIDtoEmail(transfer[u'newOwnerUserId'])
      a_transfer[u'requestTime'] = transfer[u'requestTime']
      a_transfer[u'applicationId'] = transfer[u'applicationDataTransfers'][i][u'applicationId']
      a_transfer[u'application'] = appID2app(dt, a_transfer[u'applicationId'])
      a_transfer[u'status'] = transfer[u'applicationDataTransfers'][i][u'applicationTransferStatus']
      a_transfer[u'id'] = transfer[u'id']
      if u'applicationTransferParams' in transfer[u'applicationDataTransfers'][i]:
        for param in transfer[u'applicationDataTransfers'][i][u'applicationTransferParams']:
          a_transfer[param[u'key']] = ','.join(param[u'value'])
    for title in a_transfer:
      if title not in transfers_attributes[0]:
        transfers_attributes[0][title] = title
    transfers_attributes.append(a_transfer)
  output_csv(transfers_attributes, transfers_attributes[0], u'Data Transfers', todrive)

def doGetDataTransferInfo():
  dt = buildGAPIObject(u'datatransfer')
  dtId = sys.argv[3]
  transfer = callGAPI(service=dt.transfers(), function=u'get', dataTransferId=dtId)
  print u'Old Owner: %s' % convertUserIDtoEmail(transfer[u'oldOwnerUserId'])
  print u'New Owner: %s' % convertUserIDtoEmail(transfer[u'newOwnerUserId'])
  print u'Request Time: %s' % transfer[u'requestTime']
  for app in transfer[u'applicationDataTransfers']:
    print u'Application: %s' % appID2app(dt, app[u'applicationId'])
    print u'Status: %s' % app[u'applicationTransferStatus']
    print u'Parameters:'
    if u'applicationTransferParams' in app:
      for param in app[u'applicationTransferParams']:
        print   u' %s: %s' % (param[u'key'], u','.join(param[u'value']))
    else:
      print u' None'
    print

def doCreateCourse():
  croom = buildGAPIObject(u'classroom')
  body = dict()
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'alias', u'id']:
      body[u'id'] = u'd:%s' % sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'section':
      body[u'section'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'heading':
      body[u'descriptionHeading'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'room':
      body[u'room'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'teacher':
      body[u'ownerId'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'state', u'status']:
      body[u'courseState'] = sys.argv[i+1].upper()
      if body[u'courseState'] not in [u'ACTIVE', u'ARCHIVED', u'PROVISIONED', u'DECLINED']:
        print 'ERROR: course state can be active or archived. Got %s' % body[u'courseState']
        sys.exit(2)
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam create course".' % sys.argv[i]
      sys.exit(2)
  if not u'ownerId' in body:
    body['ownerId'] = u'me'
  if not u'name' in body:
    body['name'] = u'Unknown Course'
  result = callGAPI(service=croom.courses(), function=u'create', body=body)
  print u'Created course %s' % result[u'id']

def doGetCourseInfo():
  croom = buildGAPIObject(u'classroom')
  courseId = sys.argv[3]
  if not courseId.isdigit():
    courseId = u'd:%s' % courseId
  info = callGAPI(service=croom.courses(), function=u'get', id=courseId)
  print_json(None, info)
  teachers = callGAPIpages(service=croom.courses().teachers(), function=u'list', items=u'teachers', courseId=courseId)
  students = callGAPIpages(service=croom.courses().students(), function=u'list', items=u'students', courseId=courseId)
  try:
    aliases = callGAPIpages(service=croom.courses().aliases(), function=u'list', items=u'aliases', throw_reasons=[u'notImplemented'], courseId=courseId)
  except googleapiclient.errors.HttpError:
    aliases = []
  if aliases:
    print u'Aliases:'
    for alias in aliases:
      print u'  %s' % alias[u'alias'][2:]
  print u'Participants:'
  print u' Teachers:'
  for teacher in teachers:
    try:
      print convertUTF8(u'  %s - %s' % (teacher[u'profile'][u'name'][u'fullName'], teacher[u'profile'][u'emailAddress']))
    except KeyError:
      print convertUTF8(u'  %s' % teacher[u'profile'][u'name'][u'fullName'])
  print u' Students:'
  for student in students:
    try:
      print convertUTF8(u'  %s - %s' % (student[u'profile'][u'name'][u'fullName'], student[u'profile'][u'emailAddress']))
    except KeyError:
      print convertUTF8(u'  %s' % student[u'profile'][u'name'][u'fullName'])

def doPrintCourses():
  croom = buildGAPIObject(u'classroom')
  croom_attributes = [{}]
  titles = []
  todrive = False
  teacherId = None
  studentId = None
  get_aliases = False
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'teacher':
      teacherId = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'student':
      studentId = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() in [u'alias', u'aliases']:
      get_aliases = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam print courses"' % sys.argv[i]
      sys.exit(2)
  sys.stderr.write(u'Retrieving courses for organization (may take some time for large accounts)...\n')
  page_message = u'Got %%num_items%% courses...\n'
  all_courses = callGAPIpages(service=croom.courses(), function=u'list', items=u'courses', page_message=page_message, teacherId=teacherId, studentId=studentId)
  for course in all_courses:
    croom_attributes.append(flatten_json(course))
    for item in croom_attributes[-1]:
      if item not in titles:
        titles.append(item)
        croom_attributes[0][item] = item
  if get_aliases:
    titles.append(u'Aliases')
    croom_attributes[0].update(Aliases=u'Aliases')
    num_courses = len(croom_attributes[1:])
    i = 1
    for course in croom_attributes[1:]:
      sys.stderr.write('Getting aliases for course %s (%s/%s)\n' % (course[u'id'], i, num_courses))
      course_aliases = callGAPIpages(service=croom.courses().aliases(), function=u'list', items=u'aliases', courseId=course[u'id'])
      my_aliases = []
      for alias in course_aliases:
        my_aliases.append(alias[u'alias'][2:])
      course.update(Aliases=u' '.join(my_aliases))
      i += 1
  output_csv(croom_attributes, titles, u'Courses', todrive)

def doPrintCourseParticipants():
  croom = buildGAPIObject(u'classroom')
  participants_attributes = [{}]
  titles = []
  todrive = False
  courses = []
  teacherId = None
  studentId = None
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() in [u'course', u'class']:
      course = sys.argv[i+1]
      if not course.isdigit():
        course = u'd:%s' % course
      courses.append(course)
      i += 2
    elif sys.argv[i].lower() == u'teacher':
      teacherId = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'student':
      studentId = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam print course-participants"' % sys.argv[i]
      sys.exit(2)
    sys.stderr.write(u'Retrieving courses for organization (may take some time for large accounts)...\n')
  if len(courses) == 0:
    page_message = u'Got %%num_items%% courses...\n'
    all_courses = callGAPIpages(service=croom.courses(), function=u'list', items=u'courses', page_message=page_message, teacherId=teacherId, studentId=studentId)
    for course in all_courses:
      courses.append(course[u'id'])
  else:
    all_courses = []
    for course in courses:
      all_courses.append(callGAPI(service=croom.courses(), function=u'get', id=course))
  y = 1
  num_courses = len(all_courses)
  for course in all_courses:
    course_id = course[u'id']
    teacher_message = u' got %%%%num_items%%%% teachers for course %s (%s/%s)' % (course_id, y, num_courses)
    student_message = u' got %%%%num_items%%%% students for course %s (%s/%s)' % (course_id, y, num_courses)
    teachers = callGAPIpages(service=croom.courses().teachers(), function=u'list', items=u'teachers', page_message=teacher_message, courseId=course_id)
    students = callGAPIpages(service=croom.courses().students(), function=u'list', items=u'students', page_message=student_message, courseId=course_id)
    for teacher in teachers:
      participant = flatten_json(teacher)
      participant[u'courseId'] = course_id
      participant[u'courseName'] = course[u'name']
      participant[u'userRole'] = u'TEACHER'
      participants_attributes.append(participant)
      for item in participant:
        if item not in titles:
          titles.append(item)
          participants_attributes[0][item] = item
    for student in students:
      participant = flatten_json(student)
      participant[u'courseId'] = course_id
      participant[u'courseName'] = course[u'name']
      participant[u'userRole'] = u'STUDENT'
      participants_attributes.append(participant)
      for item in participant:
        if item not in titles:
          titles.append(item)
          participants_attributes[0][item] = item
    y += 1
  output_csv(participants_attributes, titles, u'Course Participants', todrive)

PRINTJOB_ASCENDINGORDER_MAP = {
  u'createtime': u'CREATE_TIME',
  u'status': u'STATUS',
  u'title': u'TITLE',
  }
PRINTJOB_DESCENDINGORDER_MAP = {
  u'CREATE_TIME': u'CREATE_TIME_DESC',
  u'STATUS':  u'STATUS_DESC',
  u'TITLE': u'TITLE_DESC',
  }

def doPrintPrintJobs():
  cp = buildGAPIObject(u'cloudprint')
  job_attributes = [{}]
  titles = []
  todrive = False
  printerid = None
  owner = None
  status = None
  sortorder = None
  descending = False
  query = None
  i = 3
  age = None
  older_or_newer = None
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower().replace(u'_', u'') in [u'olderthan', u'newerthan']:
      if sys.argv[i].lower().replace(u'_', u'') == u'olderthan':
        older_or_newer = u'older'
      else:
        older_or_newer = u'newer'
      age_number = sys.argv[i+1][:-1]
      if not age_number.isdigit():
        print u'ERROR: expected a number, got %s' % age_number
        sys.exit(2)
      age_unit = sys.argv[i+1][-1].lower()
      if age_unit == u'm':
        age = int(time.time()) - (int(age_number) * 60)
      elif age_unit == u'h':
        age = int(time.time()) - (int(age_number) * 60 * 60)
      elif age_unit == u'd':
        age = int(time.time()) - (int(age_number) * 60 * 60 * 24)
      else:
        print u'ERROR: expected m (minutes), h (hours) or d (days), got %s' % age_unit
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'status':
      status = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'ascending':
      descending = False
      i += 1
    elif sys.argv[i].lower() == u'descending':
      descending = True
      i += 1
    elif sys.argv[i].lower() == u'orderby':
      sortorder = sys.argv[i+1].lower().replace(u'_', u'')
      if sortorder not in PRINTJOB_ASCENDINGORDER_MAP:
        print u'ERROR: orderby must be one of %s. Got %s' % (','.join(PRINTJOB_ASCENDINGORDER_MAP), sortorder)
        sys.exit(2)
      sortorder = PRINTJOB_ASCENDINGORDER_MAP[sortorder]
      i += 2
    elif sys.argv[i].lower() in [u'printer', u'printerid']:
      printerid = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'owner', u'user']:
      owner = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam print printjobs"' % sys.argv[i]
      sys.exit(2)
  if sortorder and descending:
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  jobs = callGAPI(service=cp.jobs(), function=u'list', q=query, status=status, sortorder=sortorder, printerid=printerid, owner=owner)
  checkCloudPrintResult(jobs)
  for job in jobs[u'jobs']:
    createTime = int(job[u'createTime'])/1000
    if older_or_newer:
      if older_or_newer == u'older' and createTime > age:
        continue
      elif older_or_newer == u'newer' and createTime < age:
        continue
    updateTime = int(job[u'updateTime'])/1000
    job[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
    job[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
    job[u'tags'] = u' '.join(job[u'tags'])
    job_attributes.append(flatten_json(job))
    for item in job_attributes[-1]:
      if item not in titles:
        titles.append(item)
        job_attributes[0][item] = item
  output_csv(job_attributes, titles, u'Print Jobs', todrive)

def doPrintPrinters():
  cp = buildGAPIObject(u'cloudprint')
  printer_attributes = [{}]
  titles = []
  todrive = False
  query = None
  printer_type = None
  connection_status = None
  extra_fields = None
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'type':
      printer_type = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'status':
      connection_status = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'extrafields':
      extra_fields = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam print printers"' % sys.argv[i]
      sys.exit(2)
  printers = callGAPI(service=cp.printers(), function=u'list', q=query, type=printer_type, connection_status=connection_status, extra_fields=extra_fields)
  checkCloudPrintResult(printers)
  for printer in printers[u'printers']:
    createTime = int(printer[u'createTime'])/1000
    accessTime = int(printer[u'accessTime'])/1000
    updateTime = int(printer[u'updateTime'])/1000
    printer[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'accessTime'] = datetime.datetime.fromtimestamp(accessTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
    printer[u'tags'] = u' '.join(printer[u'tags'])
    printer_attributes.append(flatten_json(printer))
    for item in printer_attributes[-1]:
      if item not in titles:
        titles.append(item)
        printer_attributes[0][item] = item
  output_csv(printer_attributes, titles, u'Printers', todrive)

def changeCalendarAttendees(users):
  cal = buildGAPIServiceObject(u'calendar', users[0])
  do_it = True
  i = 5
  allevents = False
  start_date = end_date = None
  while len(sys.argv) > i:
    if sys.argv[i].lower() == u'csv':
      csv_file = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'dryrun':
      do_it = False
      i += 1
    elif sys.argv[i].lower() == u'start':
      start_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'end':
      end_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'allevents':
      allevents = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> update calattendees"' % sys.argv[i]
      sys.exit(2)
  attendee_map = dict()
  csvfile = csv.reader(open(csv_file, u'rb'))
  for row in csvfile:
    attendee_map[row[0].lower()] = row[1].lower()
  for user in users:
    sys.stdout.write(u'Checking user %s\n' % user)
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    cal = buildGAPIServiceObject(u'calendar', user)
    page_token = None
    while True:
      events_page = callGAPI(service=cal.events(), function=u'list', calendarId=user, pageToken=page_token, timeMin=start_date, timeMax=end_date, showDeleted=False, showHiddenInvitations=False)
      print u'Got %s items' % len(events_page.get(u'items', []))
      for event in events_page.get(u'items', []):
        if event[u'status'] == u'cancelled':
          #print ' skipping cancelled event'
          continue
        try:
          event_summary = convertUTF8(event[u'summary'])
        except (KeyError, UnicodeEncodeError, UnicodeDecodeError):
          event_summary = event[u'id']
        try:
          if not allevents and event[u'organizer'][u'email'].lower() != user:
            #print ' skipping not-my-event %s' % event_summary
            continue
        except KeyError:
          pass # no email for organizer
        needs_update = False
        try:
          for attendee in event[u'attendees']:
            try:
              if attendee[u'email'].lower() in attendee_map:
                old_email = attendee[u'email'].lower()
                new_email = attendee_map[attendee[u'email'].lower()]
                print u' SWITCHING attendee %s to %s for %s' % (old_email, new_email, event_summary)
                event[u'attendees'].remove(attendee)
                event[u'attendees'].append({u'email': new_email})
                needs_update = True
            except KeyError: # no email for that attendee
              pass
        except KeyError:
          continue # no attendees
        if needs_update:
          body = dict()
          body[u'attendees'] = event[u'attendees']
          print u'UPDATING %s' % event_summary
          if do_it:
            callGAPI(service=cal.events(), function=u'patch', calendarId=user, eventId=event[u'id'], sendNotifications=False, body=body)
          else:
            print u' not pulling the trigger.'
        #else:
        #  print ' no update needed for %s' % event_summary
      try:
        page_token = events_page[u'nextPageToken']
      except KeyError:
        break

def deleteCalendar(users):
  buildGAPIObject(u'calendar')
  calendarId = sys.argv[5]
  if calendarId.find(u'@') == -1:
    calendarId = u'%s@%s' % (calendarId, GC_Values[GC_DOMAIN])
  for user in users:
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    cal = buildGAPIServiceObject(u'calendar', user)
    callGAPI(service=cal.calendarList(), function=u'delete', calendarId=calendarId)

CALENDAR_REMINDER_METHODS = [u'email', u'sms', u'popup',]
CALENDAR_NOTIFICATION_METHODS = [u'email', u'sms',]
CALENDAR_NOTIFICATION_TYPES_MAP = {
  u'eventcreation': u'eventCreation',
  u'eventchange': u'eventChange',
  u'eventcancellation': u'eventCancellation',
  u'eventresponse': u'eventResponse',
  u'agenda': u'agenda',
  }

def getCalendarAttributes(i, body, function):
  colorRgbFormat = False
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'selected':
      if sys.argv[i+1].lower() in true_values:
        body[u'selected'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'selected'] = False
      else:
        print u'ERROR: Value for selected must be true or false, not %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif myarg == u'hidden':
      if sys.argv[i+1].lower() in true_values:
        body[u'hidden'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'hidden'] = False
      else:
        print u'ERROR: Value for hidden must be true or false, not %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif myarg == u'summary':
      body[u'summaryOverride'] = sys.argv[i+1]
      i += 2
    elif myarg == u'colorindex':
      body[u'colorId'] = str(sys.argv[i+1])
      i += 2
    elif myarg == u'backgroundcolor':
      body[u'backgroundColor'] = sys.argv[i+1]
      colorRgbFormat = True
      i += 2
    elif myarg == u'foregroundcolor':
      body[u'foregroundColor'] = sys.argv[i+1]
      colorRgbFormat = True
      i += 2
    elif myarg == u'reminder':
      body.setdefault(u'defaultReminders', [])
      method = sys.argv[i+1].lower()
      if method not in CLEAR_NONE_ARGUMENT:
        if method not in CALENDAR_REMINDER_METHODS:
          print u'ERROR: Method must be %s. Got %s' % (u','.join(CALENDAR_REMINDER_METHODS+CLEAR_NONE_ARGUMENT), method)
          sys.exit(2)
        try:
          minutes = int(sys.argv[i+2])
        except ValueError:
          print u'ERROR: Reminder time must be specified in minutes, got %s' % sys.argv[i+2]
          sys.exit(2)
        body[u'defaultReminders'].append({u'method': method, u'minutes': minutes})
        i += 3
      else:
        i += 2
    elif myarg == u'notification':
      body.setdefault(u'notificationSettings', {u'notifications': []})
      method = sys.argv[i+1].lower()
      if method not in CLEAR_NONE_ARGUMENT:
        if method not in CALENDAR_NOTIFICATION_METHODS:
          print u'ERROR: Method must be %s. Got %s' % (u','.join(CALENDAR_NOTIFICATION_METHODS+CLEAR_NONE_ARGUMENT), method)
          sys.exit(2)
        eventType = sys.argv[i+2].lower()
        if eventType not in CALENDAR_NOTIFICATION_TYPES_MAP:
          print u'ERROR: Event must be %s. Got %s' % (u','.join(CALENDAR_NOTIFICATION_TYPES_MAP), eventType)
          sys.exit(2)
        body[u'notificationSettings'][u'notifications'].append({u'method': method, u'type': CALENDAR_NOTIFICATION_TYPES_MAP[eventType]})
        i += 3
      else:
        i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam %s calendar"' % (sys.argv[i], function)
      sys.exit(2)
  return colorRgbFormat

def addCalendar(users):
  buildGAPIObject(u'calendar')
  calendarId = sys.argv[5]
  if calendarId.find(u'@') == -1:
    calendarId = u'%s@%s' % (calendarId, GC_Values[GC_DOMAIN])
  body = {u'id': calendarId, u'selected': True, u'hidden': False}
  colorRgbFormat = getCalendarAttributes(6, body, u'add')
  i = 1
  count = len(users)
  for user in users:
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    print u"Subscribing %s to %s calendar (%s of %s)" % (user, calendarId, i, count)
    cal = buildGAPIServiceObject(u'calendar', user)
    callGAPI(service=cal.calendarList(), function=u'insert', body=body, colorRgbFormat=colorRgbFormat)
    i += 1

def updateCalendar(users):
  buildGAPIObject(u'calendar')
  calendarId = sys.argv[5]
  if calendarId.find(u'@') == -1:
    calendarId = u'%s@%s' % (calendarId, GC_Values[GC_DOMAIN])
  body = {}
  colorRgbFormat = getCalendarAttributes(6, body, u'update')
  i = 1
  count = len(users)
  for user in users:
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    print u"Updating %s's subscription to calendar %s (%s of %s)" % (user, calendarId, i, count)
    cal = buildGAPIServiceObject(u'calendar', user)
    callGAPI(service=cal.calendarList(), function=u'update', calendarId=calendarId, body=body, colorRgbFormat=colorRgbFormat)

def doPrinterShowACL():
  cp = buildGAPIObject(u'cloudprint')
  show_printer = sys.argv[2]
  printer_info = callGAPI(service=cp.printers(), function=u'get', printerid=show_printer)
  checkCloudPrintResult(printer_info)
  for acl in printer_info[u'printers'][0][u'access']:
    if u'key' in acl:
      acl[u'accessURL'] = u'https://www.google.com/cloudprint/addpublicprinter.html?printerid=%s&key=%s' % (show_printer, acl[u'key'])
    print_json(None, acl)
    print

def doPrinterAddACL():
  cp = buildGAPIObject(u'cloudprint')
  printer = sys.argv[2]
  role = sys.argv[4].upper()
  scope = sys.argv[5]
  public = None
  skip_notification = True
  if scope.lower() == u'public':
    public = True
    scope = None
    role = None
    skip_notification = None
  elif scope.find(u'@') == -1:
    scope = u'/hd/domain/%s' % scope
  result = callGAPI(service=cp.printers(), function=u'share', printerid=printer, role=role, scope=scope, public=public, skip_notification=skip_notification)
  checkCloudPrintResult(result)
  who = scope
  if who == None:
    who = 'public'
    role = 'user'
  print u'Added %s %s' % (role, who)

def doPrinterDelACL():
  cp = buildGAPIObject(u'cloudprint')
  printer = sys.argv[2]
  scope = sys.argv[4]
  public = None
  if scope.lower() == u'public':
    public = True
    scope = None
  elif scope.find(u'@') == -1:
    scope = u'/hd/domain/%s' % scope
  result = callGAPI(service=cp.printers(), function=u'unshare', printerid=printer, scope=scope, public=public)
  checkCloudPrintResult(result)
  who = scope
  if who == None:
    who = u'public'
  print u'Removed %s' % who

def encode_multipart(fields, files, boundary=None):
  def escape_quote(s):
    return s.replace('"', '\\"')

  def getFormDataLine(name, value, boundary):
    return '--{0}'.format(boundary), 'Content-Disposition: form-data; name="{0}"'.format(escape_quote(name)), '', str(value)

  if boundary is None:
    boundary = ''.join(random.choice(string.digits + string.ascii_letters) for i in range(30))
  lines = []
  for name, value in fields.items():
    if name == u'tags':
      for tag in value:
        lines.extend(getFormDataLine('tag', tag, boundary))
    else:
      lines.extend(getFormDataLine(name, value, boundary))
  for name, value in files.items():
    filename = value['filename']
    mimetype = value['mimetype']
    lines.extend((
      '--{0}'.format(boundary),
      'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(
        escape_quote(name), escape_quote(filename)),
      'Content-Type: {0}'.format(mimetype),
      '',
      value['content'],
    ))
  lines.extend((
    '--{0}--'.format(boundary),
    '',
  ))
  body = '\r\n'.join(lines)
  headers = {
    'Content-Type': 'multipart/form-data; boundary={0}'.format(boundary),
    'Content-Length': str(len(body)),
  }
  return (body, headers)

def doPrintJobFetch():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[2]
  if printerid == u'any':
    printerid = None
  owner = None
  status = None
  sortorder = None
  descending = False
  query = None
  age = None
  older_or_newer = None
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') in [u'olderthan', u'newerthan']:
      if sys.argv[i].lower().replace(u'_', u'') == u'olderthan':
        older_or_newer = u'older'
      else:
        older_or_newer = u'newer'
      age_number = sys.argv[i+1][:-1]
      if not age_number.isdigit():
        print u'ERROR: expected a number, got %s' % age_number
        sys.exit(2)
      age_unit = sys.argv[i+1][-1].lower()
      if age_unit == u'm':
        age = int(time.time()) - (int(age_number) * 60)
      elif age_unit == u'h':
        age = int(time.time()) - (int(age_number) * 60 * 60)
      elif age_unit == u'd':
        age = int(time.time()) - (int(age_number) * 60 * 60 * 24)
      else:
        print u'ERROR: expected m (minutes), h (hours) or d (days), got %s' % age_unit
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'status':
      status = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'ascending':
      descending = False
      i += 1
    elif sys.argv[i].lower() == u'descending':
      descending = True
      i += 1
    elif sys.argv[i].lower() == u'orderby':
      sortorder = sys.argv[i+1].lower().replace(u'_', u'')
      if sortorder not in PRINTJOB_ASCENDINGORDER_MAP:
        print 'ERROR: orderby must be one of %s. Got %s' % (','.join(PRINTJOB_ASCENDINGORDER_MAP), sortorder)
        sys.exit(2)
      sortorder = PRINTJOB_ASCENDINGORDER_MAP[sortorder]
      i += 2
    elif sys.argv[i].lower() in [u'owner', u'user']:
      owner = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam printjobs fetch"' % sys.argv[i]
      sys.exit(2)
  if sortorder and descending:
    sortorder = PRINTJOB_DESCENDINGORDER_MAP[sortorder]
  result = callGAPI(service=cp.jobs(), function=u'list', q=query, status=status, sortorder=sortorder, printerid=printerid, owner=owner)
  if u'errorCode' in result and result[u'errorCode'] == 413:
    print u'No print jobs.'
    sys.exit(0)
  checkCloudPrintResult(result)
  valid_chars = u'-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  ssd = '''{
  "state": {"type": "DONE"}
}'''
  for job in result[u'jobs']:
    createTime = int(job[u'createTime'])/1000
    if older_or_newer:
      if older_or_newer == u'older' and createTime > age:
        continue
      elif older_or_newer == u'newer' and createTime < age:
        continue
    fileUrl = job[u'fileUrl']
    jobid = job[u'id']
    fileName = job[u'title']
    fileName = u''.join(c if c in valid_chars else u'_' for c in fileName)
    fileName = u'%s-%s' % (fileName, jobid)
    _, content = cp._http.request(uri=fileUrl, method='GET')
    if writeFile(fileName, content, continueOnError=True):
#      ticket = callGAPI(service=cp.jobs(), function=u'getticket', jobid=jobid, use_cjt=True)
      result = callGAPI(service=cp.jobs(), function=u'update', jobid=jobid, semantic_state_diff=ssd)
      checkCloudPrintResult(result)
      print u'Printed job %s to %s' % (jobid, fileName)

def doDelPrinter():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[3]
  result = callGAPI(service=cp.printers(), function=u'delete', printerid=printerid)
  checkCloudPrintResult(result)

def doGetPrinterInfo():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[3]
  everything = False
  i = 4
  while i < len(sys.argv):
    if sys.argv[i] == u'everything':
      everything = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam info printer"' % sys.argv[i]
      sys.exit(2)
  result = callGAPI(service=cp.printers(), function=u'get', printerid=printerid)
  checkCloudPrintResult(result)
  printer_info = result[u'printers'][0]
  createTime = int(printer_info[u'createTime'])/1000
  accessTime = int(printer_info[u'accessTime'])/1000
  updateTime = int(printer_info[u'updateTime'])/1000
  printer_info[u'createTime'] = datetime.datetime.fromtimestamp(createTime).strftime(u'%Y-%m-%d %H:%M:%S')
  printer_info[u'accessTime'] = datetime.datetime.fromtimestamp(accessTime).strftime(u'%Y-%m-%d %H:%M:%S')
  printer_info[u'updateTime'] = datetime.datetime.fromtimestamp(updateTime).strftime(u'%Y-%m-%d %H:%M:%S')
  printer_info[u'tags'] = u' '.join(printer_info[u'tags'])
  if not everything:
    del printer_info[u'capabilities']
    del printer_info[u'access']
  print_json(None, printer_info)

def doUpdatePrinter():
  cp = buildGAPIObject(u'cloudprint')
  printerid = sys.argv[3]
  kwargs = {}
  i = 4
  update_items = [u'isTosAccepted', u'gcpVersion', u'setupUrl',
                  u'quotaEnabled', u'id', u'supportUrl', u'firmware',
                  u'currentQuota', u'type', u'public', u'status', u'description',
                  u'defaultDisplayName', u'proxy', u'dailyQuota', u'manufacturer',
                  u'displayName', u'name', u'uuid', u'updateUrl', u'ownerId', u'model']
  while i < len(sys.argv):
    arg_in_item = False
    for item in update_items:
      if item.lower() == sys.argv[i].lower():
        kwargs[item] = sys.argv[i+1]
        i += 2
        arg_in_item = True
        break
    if not arg_in_item:
      print u'ERROR: %s is not a valid argument for "gam update printer"' % sys.argv[i]
      sys.exit(2)
  result = callGAPI(service=cp.printers(), function=u'update', printerid=printerid, **kwargs)
  checkCloudPrintResult(result)
  print u'Updated printer %s' % printerid

def doPrinterRegister():
  cp = buildGAPIObject(u'cloudprint')
  form_fields = {u'name': u'GAM',
                 u'proxy': u'GAM',
                 u'uuid': cp._http.request.credentials.id_token[u'sub'],
                 u'manufacturer': __author__,
                 u'model': u'cp1',
                 u'gcp_version': u'2.0',
                 u'setup_url': GAM_URL,
                 u'support_url': u'https://groups.google.com/forum/#!forum/google-apps-manager',
                 u'update_url': GAM_RELEASES,
                 u'firmware': __version__,
                 u'semantic_state': {"version": "1.0", "printer": {"state": "IDLE",}},
                 u'use_cdd': True,
                 u'capabilities': {"version": "1.0",
                                   "printer": {"supported_content_type": [{"content_type": "application/pdf", "min_version": "1.5"},
                                                                          {"content_type": "image/jpeg"},
                                                                          {"content_type": "text/plain"}
                                                                         ],
                                               "copies": {"default": 1, "max": 100},
                                               "media_size": {"option": [{"name": "ISO_A4", "width_microns": 210000, "height_microns": 297000},
                                                                         {"name": "NA_LEGAL", "width_microns": 215900, "height_microns": 355600},
                                                                         {"name": "NA_LETTER", "width_microns": 215900, "height_microns": 279400, "is_default": True}
                                                                        ],
                                                             },
                                              },
                                  },
                 u'tags': [u'GAM', GAM_URL],
                }
  form_files = {}
  body, headers = encode_multipart(form_fields, form_files)
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(service=cp.printers(), function=u'list')
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/register', method='POST', body=body, headers=headers)
  result = json.loads(result)
  checkCloudPrintResult(result)
  print u'Created printer %s' % result[u'printers'][0][u'id']

def doPrintJobResubmit():
  cp = buildGAPIObject(u'cloudprint')
  jobid = sys.argv[2]
  printerid = sys.argv[4]
  ssd = '''{
  "state": {"type": "HELD"}
}'''
  result = callGAPI(service=cp.jobs(), function=u'update', jobid=jobid, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  ticket = callGAPI(service=cp.jobs(), function=u'getticket', jobid=jobid, use_cjt=True)
  result = callGAPI(service=cp.jobs(), function=u'resubmit', printerid=printerid, jobid=jobid, ticket=ticket)
  checkCloudPrintResult(result)
  print u'Success resubmitting %s as job %s to printer %s' % (jobid, result[u'job'][u'id'], printerid)

def doPrintJobSubmit():
  cp = buildGAPIObject(u'cloudprint')
  printer = sys.argv[2]
  content = sys.argv[4]
  form_fields = {u'printerid': printer,
                 u'title': content,
                 u'ticket': u'{"version": "1.0"}',
                 u'tags': [u'GAM', GAM_URL]}
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'tag':
      form_fields[u'tags'].append(sys.argv[i+1])
      i += 2
    elif sys.argv[i].lower() in [u'name', u'title']:
      form_fields[u'title'] = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam printer ... print"' % sys.argv[i]
      sys.exit(2)
  form_files = {}
  if content[:4] == u'http':
    form_fields[u'content'] = content
    form_fields[u'contentType'] = u'url'
  else:
    filepath = content
    content = ntpath.basename(content)
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype == None:
      mimetype = u'application/octet-stream'
    filecontent = readFile(filepath)
    form_files[u'content'] = {u'filename': content, u'content': filecontent, u'mimetype': mimetype}
  #result = callGAPI(service=cp.printers(), function=u'submit', body=body)
  body, headers = encode_multipart(form_fields, form_files)
  #Get the printer first to make sure our OAuth access token is fresh
  callGAPI(service=cp.printers(), function=u'get', printerid=printer)
  _, result = cp._http.request(uri='https://www.google.com/cloudprint/submit', method='POST', body=body, headers=headers)
  checkCloudPrintResult(result)
  if type(result) is str:
    result = json.loads(result)
  print u'Submitted print job %s' % result[u'job'][u'id']

def doDeletePrintJob():
  cp = buildGAPIObject(u'cloudprint')
  job = sys.argv[2]
  result = callGAPI(service=cp.jobs(), function=u'delete', jobid=job)
  checkCloudPrintResult(result)
  print u'Print Job %s deleted' % job

def doCancelPrintJob():
  cp = buildGAPIObject(u'cloudprint')
  job = sys.argv[2]
  ssd = '{"state": {"type": "ABORTED", "user_action_cause": {"action_code": "CANCELLED"}}}'
  result = callGAPI(service=cp.jobs(), function=u'update', jobid=job, semantic_state_diff=ssd)
  checkCloudPrintResult(result)
  print u'Print Job %s cancelled' % job

def checkCloudPrintResult(result):
  if type(result) is str:
    try:
      result = json.loads(result)
    except ValueError:
      print u'ERROR: unexpected response: %s' % result
      sys.exit(3)
  if not result[u'success']:
    print u'ERROR %s: %s' % (result[u'errorCode'], result[u'message'])
    sys.exit(result[u'errorCode'])

def doCalendarShowACL():
  cal = buildGAPIObject(u'calendar')
  show_cal = sys.argv[2]
  if show_cal.find(u'@') == -1:
    show_cal = u'%s@%s' % (show_cal, GC_Values[GC_DOMAIN])
  acls = callGAPI(service=cal.acl(), function=u'list', calendarId=show_cal)
  try:
    for rule in acls[u'items']:
      print u'  Scope %s - %s' % (rule[u'scope'][u'type'], rule[u'scope'][u'value'])
      print u'  Role: %s' % (rule[u'role'])
      print u''
  except IndexError:
    pass

def doCalendarAddACL(calendarId=None, act_as=None, role=None, scope=None, entity=None):
  if act_as != None:
    cal = buildGAPIServiceObject(u'calendar', act_as)
  else:
    cal = buildGAPIObject(u'calendar')
  body = dict()
  body[u'scope'] = dict()
  if calendarId == None:
    calendarId = sys.argv[2]
  if calendarId.find(u'@') == -1:
    calendarId = u'%s@%s' % (calendarId, GC_Values[GC_DOMAIN])
  if role != None:
    body[u'role'] = role
  else:
    body[u'role'] = sys.argv[4].lower()
  if body[u'role'] not in [u'freebusy', u'read', u'reader', u'editor', u'owner', u'none']:
    print u'ERROR: Role must be freebusy, read, editor, owner or none. Not %s' % body['role']
    sys.exit(2)
  if body[u'role'] == u'freebusy':
    body[u'role'] = u'freeBusyReader'
  elif body[u'role'] in [u'read', u'reader']:
    body[u'role'] = u'reader'
  elif body[u'role'] == u'editor':
    body[u'role'] = u'writer'
  if scope != None:
    body[u'scope'][u'type'] = scope
  else:
    body[u'scope'][u'type'] = sys.argv[5].lower()
  i = 6
  if body[u'scope'][u'type'] not in [u'default', u'user', u'group', u'domain']:
    body[u'scope'][u'type'] = u'user'
    i = 5
  try:
    if entity != None and body[u'scope'][u'type'] != u'default':
      body[u'scope'][u'value'] = entity
    else:
      body[u'scope'][u'value'] = sys.argv[i].lower()
    if (body[u'scope'][u'type'] in [u'user', u'group']) and body[u'scope'][u'value'].find(u'@') == -1:
      body[u'scope'][u'value'] = u'%s@%s' % (body[u'scope'][u'value'], GC_Values[GC_DOMAIN])
  except IndexError:
    pass
  if body[u'scope'][u'type'] == u'domain':
    try:
      body[u'scope'][u'value'] = sys.argv[6].lower()
    except IndexError:
      body[u'scope'][u'value'] = GC_Values[GC_DOMAIN]
  callGAPI(service=cal.acl(), function=u'insert', calendarId=calendarId, body=body)

def doCalendarUpdateACL():
  calendarId = sys.argv[2]
  role = sys.argv[4].lower()
  scope = sys.argv[5].lower()
  if len(sys.argv) > 6:
    entity = sys.argv[6].lower()
  else:
    entity = None
  doCalendarAddACL(calendarId=calendarId, role=role, scope=scope, entity=entity)

def doCalendarDelACL():
  calendarId = sys.argv[2]
  entity = sys.argv[5].lower()
  scope = u'user'
  if entity == u'domain':
    scope = u'domain'
  elif entity == u'default':
    scope = u'default'
    entity = ''
  doCalendarAddACL(calendarId=calendarId, role=u'none', scope=scope, entity=entity)

def doCalendarWipeData():
  calendarId = sys.argv[2]
  cal = buildGAPIServiceObject(u'calendar', calendarId)
  if calendarId.find(u'@') == -1:
    calendarId = u'%s@%s' % (calendarId, GC_Values[GC_DOMAIN])
  callGAPI(service=cal.calendars(), function=u'clear', calendarId=calendarId)

def doCalendarAddEvent():
  calendarId = sys.argv[2]
  cal = buildGAPIServiceObject(u'calendar', calendarId)
  sendNotifications = timeZone = None
  i = 4
  body = {}
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'notifyattendees':
      sendNotifications = True
      i += 1
    elif sys.argv[i].lower() == u'attendee':
      try:
        body[u'attendees'].append({u'email': sys.argv[i+1]})
      except KeyError:
        body[u'attendees'] = [{u'email': sys.argv[i+1]},]
      i += 2
    elif sys.argv[i].lower() == u'optionalattendee':
      try:
        body[u'attendees'].append({u'email': sys.argv[i+1], u'optional': True})
      except TypeError:
        body[u'attendees'] = [{u'email': sys.argv[i+1], u'optional': True},]
      i += 2
    elif sys.argv[i].lower() == u'anyonecanaddself':
      body[u'anyoneCanAddSelf'] = True
      i += 1
    elif sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'start':
      if sys.argv[i+1].lower() == u'allday':
        body[u'start'] = {u'date': sys.argv[i+2]}
        i += 3
      else:
        body[u'start'] = {u'dateTime': sys.argv[i+1]}
        i += 2
    elif sys.argv[i].lower() == u'end':
      if sys.argv[i+1].lower() == u'allday':
        body[u'end'] = {u'date': sys.argv[i+2]}
        i += 3
      else:
        body[u'end'] = {u'dateTime': sys.argv[i+1]}
        i += 2
    elif sys.argv[i].lower() == u'guestscantinviteothers':
      body[u'guestsCanInviteOthers'] = False
      i += 1
    elif sys.argv[i].lower() == u'guestscantseeothers':
      body[u'guestsCanSeeOtherGuests'] = False
      i += 1
    elif sys.argv[i].lower() == u'id':
      body[u'id'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'summary':
      body[u'summary'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'location':
      body[u'location'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'available':
      body[u'transparency'] = u'transparent'
      i += 1
    elif sys.argv[i].lower() == u'visibility':
      if sys.argv[i+1].lower() in [u'default', u'public', u'private']:
        body[u'visibility'] = sys.argv[i+1].lower()
      else:
        print 'ERROR: visibility must be one of default, public or private, got %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'tentative':
      body[u'status'] = u'tentative'
      i += 1
    elif sys.argv[i].lower() == u'source':
      body[u'source'] = {u'title': sys.argv[i+1], u'url': sys.argv[i+2]}
      i += 3
    elif sys.argv[i].lower() == u'noreminders':
      body[u'reminders'] = {u'useDefault': False}
      i += 1
    elif sys.argv[i].lower() == u'reminder':
      try:
        body[u'reminders'][u'overrides'].append({u'minutes': sys.argv[i+1], u'method': sys.argv[i+2]})
        body[u'reminders'][u'useDefault'] = False
      except KeyError:
        body[u'reminders'] = {u'useDefault': False, u'overrides': [{u'minutes': sys.argv[i+1], u'method': sys.argv[i+2]},]}
      i += 3
    elif sys.argv[i].lower() == u'recurrence':
      try:
        body[u'recurrence'].append(sys.argv[i+1])
      except KeyError:
        body[u'recurrence'] = [sys.argv[i+1],]
      i += 2
    elif sys.argv[i].lower() == u'timezone':
      timeZone = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'privateproperty':
      if u'extendedProperties' not in body:
        body[u'extendedProperties'] = {u'private': {}, u'shared': {}}
      body[u'extendedProperties']['private'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif sys.argv[i].lower() == u'sharedproperty':
      if u'extendedProperties' not in body:
        body[u'extendedProperties'] = {u'private': {}, u'shared': {}}
      body[u'extendedProperties']['shared'][sys.argv[i+1]] = sys.argv[i+2]
      i += 3
    elif sys.argv[i].lower() == u'colorindex':
      body[u'colorId'] = str(sys.argv[i+1])
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam calendar"' % sys.argv[i]
      sys.exit(2)
  if not timeZone and u'recurrence' in body:
    timeZone = callGAPI(service=cal.calendars(), function=u'get', calendarId=calendarId, fields=u'timeZone')[u'timeZone']
  if u'recurrence' in body:
    for a_time in [u'start', u'end']:
      try:
        body[a_time][u'timeZone'] = timeZone
      except KeyError:
        pass

  callGAPI(service=cal.events(), function=u'insert', calendarId=calendarId, sendNotifications=sendNotifications, body=body)


def doProfile(users):
  cd = buildGAPIObject(u'directory')
  if sys.argv[4].lower() == u'share' or sys.argv[4].lower() == u'shared':
    body = {u'includeInGlobalAddressList': True}
  elif sys.argv[4].lower() == u'unshare' or sys.argv[4].lower() == u'unshared':
    body = {u'includeInGlobalAddressList': False}
  else:
    print u'ERROR: value for "gam <users> profile" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  count = len(users)
  i = 1
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    print u'Setting Profile Sharing to %s for %s (%s of %s)' % (body[u'includeInGlobalAddressList'], user, i, count)
    callGAPI(service=cd.users(), function=u'patch', soft_errors=True, userKey=user, body=body)
    i += 1

def showProfile(users):
  cd = buildGAPIObject(u'directory')
  i = 1
  count = len(users)
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    result = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'includeInGlobalAddressList')
    try:
      print u'User: %s  Profile Shared: %s (%s/%s)' % (user, result[u'includeInGlobalAddressList'], i, count)
    except IndexError:
      pass
    i += 1

def doPhoto(users):
  cd = buildGAPIObject(u'directory')
  i = 1
  count = len(users)
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find('@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    filename = sys.argv[5].replace(u'#user#', user)
    filename = filename.replace(u'#email#', user)
    filename = filename.replace(u'#username#', user[:user.find(u'@')])
    print u"Updating photo for %s with %s (%s of %s)" % (user, filename, i, count)
    i += 1
    if re.match(u'^(ht|f)tps?://.*$', filename):
      import urllib2
      try:
        f = urllib2.urlopen(filename)
        image_data = str(f.read())
      except urllib2.HTTPError, e:
        print e
        continue
    else:
      try:
        with open(filename, u'rb') as f:
          image_data = f.read()
      except IOError, e:
        print u' couldn\'t open %s: %s' % (filename, e.strerror)
        continue
    image_data = base64.urlsafe_b64encode(image_data)
    body = {u'photoData': image_data}
    callGAPI(service=cd.users().photos(), function=u'update', soft_errors=True, userKey=user, body=body)

def getPhoto(users):
  cd = buildGAPIObject(u'directory')
  i = 1
  count = len(users)
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    filename = u'%s.jpg' % user
    print u"Saving photo to %s (%s/%s)" % (filename, i, count)
    i += 1
    try:
      photo = callGAPI(service=cd.users().photos(), function=u'get', throw_reasons=[u'notFound'], userKey=user)
    except googleapiclient.errors.HttpError:
      print u' no photo for %s' % user
      continue
    try:
      photo_data = str(photo[u'photoData'])
      print photo_data
      photo_data = base64.urlsafe_b64decode(photo_data)
    except KeyError:
      print u' no photo for %s' % user
      continue
    writeFile(filename, photo_data, continueOnError=True)

def deletePhoto(users):
  cd = buildGAPIObject(u'directory')
  i = 1
  count = len(users)
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find('@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    print u"Deleting photo for %s (%s of %s)" % (user, i, count)
    callGAPI(service=cd.users().photos(), function='delete', userKey=user)
    i += 1

def showCalendars(users):
  for user in users:
    cal = buildGAPIServiceObject(u'calendar', user)
    feed = callGAPI(service=cal.calendarList(), function=u'list')
    for usercal in feed[u'items']:
      print u'  Name: %s' % usercal[u'id']
      print convertUTF8(u'  Summary: %s' % usercal[u'summary'])
      print convertUTF8(u'    Description: %s' % usercal.get(u'description', u''))
      print u'    Access Level: %s' % usercal[u'accessRole']
      print u'    Timezone: %s' % usercal[u'timeZone']
      print convertUTF8(u'    Location: %s' % usercal.get(u'location', u''))
      print u'    Hidden: %s' % usercal.get(u'hidden', u'False')
      print u'    Selected: %s' % usercal.get(u'selected', u'False')
      print u'    Default Reminders:'
      for reminder in usercal.get(u'defaultReminders', []):
        print u'      Type: %s  Minutes: %s' % (reminder[u'method'], reminder[u'minutes'])
      print u'    Notifications:'
      if u'notificationSettings' in usercal:
        for notification in usercal[u'notificationSettings'].get(u'notifications', []):
          print u'      Method: %s  Type: %s' % (notification[u'method'], notification[u'type'])
      print u''

def showCalSettings(users):
  for user in users:
    for user in users:
      cal = buildGAPIServiceObject(u'calendar', user)
      feed = callGAPI(service=cal.settings(), function='list')
      for setting in feed[u'items']:
        print u'%s: %s' % (setting[u'id'], setting[u'value'])

def showDriveSettings(users):
  todrive = False
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> show drivesettings"' % sys.argv[i]
      sys.exit(2)
  dont_show = [u'kind', u'selfLink', u'exportFormats', u'importFormats', u'maxUploadSizes', u'additionalRoleInfo', u'etag', u'features', u'user', u'isCurrentAppInstalled']
  count = 1
  drive_attr = []
  titles = [u'email',]
  for user in users:
    sys.stderr.write(u'Getting Drive settings for %s (%s of %s)\n' % (user, count, len(users)))
    count += 1
    drive = buildGAPIServiceObject(u'drive', user)
    feed = callGAPI(service=drive.about(), function=u'get', soft_errors=True)
    if feed == None:
      continue
    row = {u'email': user}
    for setting in feed:
      if setting in dont_show:
        continue
      if setting == u'quotaBytesByService':
        for subsetting in feed[setting]:
          my_name = subsetting[u'serviceName']
          my_bytes = int(subsetting[u'bytesUsed'])
          row[my_name] = u'%smb' % (my_bytes / 1024 / 1024)
          if my_name not in titles:
            titles.append(my_name)
        continue
      row[setting] = feed[setting]
      if setting not in titles:
        titles.append(setting)
    drive_attr.append(row)
  headers = {}
  for title in titles:
    headers[title] = title
  drive_attr.insert(0, headers)
  output_csv(drive_attr, titles, u'User Drive Settings', todrive)

def doDriveActivity(users):
  drive_ancestorId = u'root'
  drive_fileId = None
  todrive = False
  i = 5
  while i < len(sys.argv):
    activity_object = sys.argv[i].lower().replace(u'_', '')
    if activity_object == u'fileid':
      drive_fileId = sys.argv[i+1]
      drive_ancestorId = None
      i += 2
    elif activity_object == u'folderid':
      drive_ancestorId = sys.argv[i+1]
      i += 2
    elif activity_object == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> show driveactivity"' % sys.argv[i]
      sys.exit(2)
  activity_attributes = [{},]
  for user in users:
    activity = buildGAPIServiceObject(u'appsactivity', user)
    page_message = u'Retrieved %%%%total_items%%%% activities for %s' % user
    feed = callGAPIpages(service=activity.activities(), function=u'list', items=u'activities',
                         page_message=page_message, source=u'drive.google.com', userId=u'me',
                         drive_ancestorId=drive_ancestorId, groupingStrategy=u'none',
                         drive_fileId=drive_fileId, pageSize=GC_Values[GC_ACTIVITY_MAX_RESULTS])
    for item in feed:
      activity_attributes.append(flatten_json(item[u'combinedEvent']))
      for an_item in activity_attributes[-1]:
        if an_item not in activity_attributes[0]:
          activity_attributes[0][an_item] = an_item
  output_csv(activity_attributes, activity_attributes[0], u'Drive Activity', todrive)

def showDriveFileACL(users):
  fileId = sys.argv[5]
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    feed = callGAPI(service=drive.permissions(), function=u'list', fileId=fileId)
    for permission in feed[u'items']:
      try:
        print permission[u'name']
      except KeyError:
        pass
      for key in permission:
        if key in [u'name', u'kind', u'etag', u'selfLink',]:
          continue
        print u' %s: %s' % (key, permission[key])
      print u''

def delDriveFileACL(users):
  fileId = sys.argv[5]
  permissionId = unicode(sys.argv[6])
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if permissionId[:3].lower() == u'id:':
      permissionId = permissionId[3:]
    elif permissionId.lower() in [u'anyone']:
      pass
    else:
      permissionId = callGAPI(service=drive.permissions(), function=u'getIdForEmail', email=permissionId, fields=u'id')[u'id']
    print u'Removing permission for %s from %s' % (permissionId, fileId)
    callGAPI(service=drive.permissions(), function=u'delete', fileId=fileId, permissionId=permissionId)

def addDriveFileACL(users):
  fileId = sys.argv[5]
  body = {u'type': sys.argv[6].lower()}
  sendNotificationEmails = False
  emailMessage = None
  if body[u'type'] not in [u'user', u'group', u'domain', u'anyone']:
    print u'ERROR: permission type must be user, group domain or anyone. Got %s' % body[u'type']
  if body[u'type'] == u'anyone':
    i = 7
  else:
    body[u'value'] = sys.argv[7]
    i = 8
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'withlink':
      body[u'withLink'] = True
      i += 1
    elif sys.argv[i].lower() == u'role':
      body[u'role'] = sys.argv[i+1]
      if body[u'role'] not in [u'reader', u'commenter', u'writer', u'owner', u'editor']:
        print u'ERROR: role must be reader, commenter, writer or owner, got %s' % body[u'role']
        sys.exit(2)
      if body[u'role'] == u'commenter':
        body[u'role'] = u'reader'
        body[u'additionalRoles'] = [u'commenter']
      elif body[u'role'] == u'editor':
        body[u'role'] = u'writer'
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'sendemail':
      sendNotificationEmails = True
      i += 1
    elif sys.argv[i].lower().replace(u'_', u'') == u'emailmessage':
      sendNotificationEmails = True
      emailMessage = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> add drivefileacl"' % sys.argv[i]
      sys.exit(2)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    result = callGAPI(service=drive.permissions(), function=u'insert', fileId=fileId, sendNotificationEmails=sendNotificationEmails, emailMessage=emailMessage, body=body)
    print result

def updateDriveFileACL(users):
  fileId = sys.argv[5]
  permissionId = unicode(sys.argv[6])
  transferOwnership = None
  body = {}
  i = 7
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'withlink':
      body[u'withLink'] = True
      i += 1
    elif sys.argv[i].lower() == u'role':
      body[u'role'] = sys.argv[i+1]
      if body[u'role'] not in [u'reader', u'commenter', u'writer', u'owner']:
        print u'ERROR: role must be reader, commenter, writer or owner, got %s' % body[u'role']
        sys.exit(2)
      if body[u'role'] == u'commenter':
        body[u'role'] = u'reader'
        body[u'additionalRoles'] = [u'commenter']
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'transferownership':
      if sys.argv[i+1].lower() in true_values:
        transferOwnership = True
      elif sys.argv[i+1].lower() in false_values:
        transferOwnership = False
      else:
        print u'ERROR: transferownership should be true or false, got %s' % sys.argv[i+1].lower()
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> update drivefileacl"' % sys.argv[i]
      sys.exit(2)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if permissionId[:3].lower() == u'id:':
      permissionId = permissionId[3:]
    else:
      permissionId = callGAPI(service=drive.permissions(), function=u'getIdForEmail', email=permissionId, fields=u'id')[u'id']
    print u'updating permissions for %s to file %s' % (permissionId, fileId)
    result = callGAPI(service=drive.permissions(), function=u'patch', fileId=fileId, permissionId=permissionId, transferOwnership=transferOwnership, body=body)
    print result

def showDriveFiles(users):
  files_attr = [{u'Owner': u'Owner',}]
  titles = [u'Owner',]
  fields = u'nextPageToken,items(title,alternateLink'
  todrive = False
  query = u'"me" in owners'
  i = 5
  labels = list()
  while i < len(sys.argv):
    my_arg = sys.argv[i].lower().replace('_', '')
    if my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'query':
      query += u' and %s' % sys.argv[i+1]
      i += 2
    elif my_arg == u'allfields':
      fields = u'*'
      i += 1
    elif my_arg == u'createddate':
      fields += u',createdDate'
      i += 1
    elif my_arg == u'description':
      fields += u',description'
      i += 1
    elif my_arg == u'fileextension':
      fields += u',fileExtension'
      i += 1
    elif my_arg == u'filesize':
      fields += u',fileSize'
      i += 1
    elif my_arg == u'id':
      fields += u',id'
      i += 1
    elif my_arg in [u'restricted', u'restrict']:
      labels.append(u'restricted')
      i += 1
    elif my_arg in [u'starred', u'star']:
      labels.append(u'starred')
      i += 1
    elif my_arg in [u'trashed', u'trash']:
      labels.append(u'trashed')
      i += 1
    elif my_arg in [u'viewed', u'view']:
      labels.append(u'viewed')
      i += 1
    elif my_arg in [u'lastmodifyinguser', u'lastmodifyingusername']:
      fields += u',lastModifyingUserName'
      i += 1
    elif my_arg in [u'lastviewedbyuser', u'lastviewedbymedate']:
      fields += u',lastViewedByMeDate'
      i += 1
    elif my_arg in [u'md5', u'md5sum', u'md5checksum']:
      fields += u',md5Checksum'
      i += 1
    elif my_arg in [u'mimetype', u'mime']:
      fields += u',mimeType'
      i += 1
    elif my_arg in [u'modifiedbyuser', u'modifiedbymedate']:
      fields += u',modifiedByMeDate'
      i += 1
    elif my_arg in [u'modifieddate']:
      fields += u',modifiedDate'
      i += 1
    elif my_arg in [u'originalfilename']:
      fields += u',originalFilename'
      i += 1
    elif my_arg in [u'quotaused', 'quotabytesused']:
      fields += u',quotaBytesUsed'
      i += 1
    elif my_arg in [u'shared']:
      fields += u',shared'
      i += 1
    elif my_arg in [u'writerscanshare']:
      fields += u',writersCanShare'
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> show filelist"' % my_arg
      sys.exit(2)
  if len(labels) > 0:
    fields += ',labels(%s)' % ','.join(labels)
  if fields != u'*':
    fields += ')'
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if user.find(u'@') == -1:
      print u'ERROR: got %s, expected a full email address' % user
      sys.exit(2)
    sys.stderr.write(u'Getting files for %s...\n' % user)
    page_message = u' got %%%%total_items%%%% files for %s...\n' % user
    feed = callGAPIpages(service=drive.files(), function=u'list',
                         page_message=page_message, soft_errors=True,
                         q=query, fields=fields, maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    for f_file in feed:
      a_file = {u'Owner': user}
      for attrib in f_file:
        if attrib in [u'kind', u'etags', u'etag', u'owners', u'parents', u'permissions']:
          continue
        attrib_type = type(f_file[attrib])
        if attrib not in titles and not attrib_type is dict:
          titles.append(attrib)
          files_attr[0][attrib] = attrib
        if attrib_type is list:
          a_file[attrib] = u' '.join(f_file[attrib])
        elif attrib_type is unicode or attrib_type is bool:
          a_file[attrib] = f_file[attrib]
        elif attrib_type is dict:
          if attrib == u'labels':
            for dict_attrib in f_file[attrib]:
              if dict_attrib not in titles:
                titles.append(dict_attrib)
                files_attr[0][dict_attrib] = dict_attrib
              a_file[dict_attrib] = f_file[attrib][dict_attrib]
          else:
            for dict_attrib in f_file[attrib]:
              if dict_attrib in [u'kind', u'etags', u'etag']:
                continue
              x_attrib = u'{0}.{1}'.format(attrib, dict_attrib)
              if x_attrib not in titles:
                titles.append(x_attrib)
                files_attr[0][x_attrib] = x_attrib
              a_file[x_attrib] = f_file[attrib][dict_attrib]
        else:
          print attrib_type
      files_attr.append(a_file)
  output_csv(files_attr, titles, u'%s %s Drive Files' % (sys.argv[1], sys.argv[2]), todrive)

def doDriveSearch(drive, query=None):
  print u'Searching for files with query: "%s"...' % query
  page_message = u' got %%total_items%% files...\n'
  files = callGAPIpages(service=drive.files(), function=u'list',
                        page_message=page_message,
                        q=query, fields=u'nextPageToken,items(id)', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
  ids = list()
  for f_file in files:
    ids.append(f_file[u'id'])
  return ids

DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP = {u'delete': u'purging', u'trash': u'trashing', u'untrash': u'untrashing',}

def deleteDriveFile(users):
  fileIds = sys.argv[5]
  function = u'trash'
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'purge':
      function = u'delete'
      i += 1
    elif sys.argv[i].lower() == u'untrash':
      function = u'untrash'
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> delete drivefile"' % sys.argv[i]
      sys.exit(2)
  action = DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP[function]
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if fileIds[:6].lower() == u'query:':
      file_ids = doDriveSearch(drive, query=fileIds[6:])
    else:
      if fileIds[:8].lower() == u'https://' or fileIds[:7].lower() == u'http://':
        fileIds = fileIds[fileIds.find(u'/d/')+3:]
        if fileIds.find(u'/') != -1:
          fileIds = fileIds[:fileIds.find(u'/')]
      file_ids = [fileIds,]
    if not file_ids:
      print u'No files to %s for %s' % (function, user)
    i = 0
    for fileId in file_ids:
      i += 1
      print u'%s %s for %s (%s of %s)' % (action, fileId, user, i, len(file_ids))
      callGAPI(service=drive.files(), function=function, fileId=fileId)

def printDriveFolderContents(feed, folderId, indent):
  for f_file in feed:
    for parent in f_file[u'parents']:
      if folderId == parent[u'id']:
        print ' ' * indent, convertUTF8(f_file[u'title'])
        if f_file[u'mimeType'] == u'application/vnd.google-apps.folder':
          printDriveFolderContents(feed, f_file[u'id'], indent+1)

def showDriveFileTree(users):
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if user.find(u'@') == -1:
      print u'ERROR: got %s, expected a full email address' % user
      sys.exit(2)
    root_folder = callGAPI(service=drive.about(), function=u'get', fields=u'rootFolderId')[u'rootFolderId']
    sys.stderr.write(u'Getting all files for %s...\n' % user)
    page_message = u' got %%%%total_items%%%% files for %s...\n' % user
    feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message,
                         fields=u'items(id,title,parents(id),mimeType),nextPageToken', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    printDriveFolderContents(feed, root_folder, 0)

def claimDriveFolder(users):
  files = []
  skipfiles = []
  skipfolders = []
  skipusers = []
  trashed = False
  # assign variables, and checking skipfiles and skipfolders
  i = 6
  target_folder = sys.argv[5]
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'skipfiles' or sys.argv[i].lower() == u'skipfolders' or sys.argv[i].lower() == u'skipusers':
      if sys.argv[i].lower() == u'skipfiles':
        f = openFile(sys.argv[i+1])
        for line in f:
          skipfiles.append(line.rstrip())
      if sys.argv[i].lower() == u'skipfolders':
        f = openFile(sys.argv[i+1])
        for line in f:
          skipfolders.append(line.rstrip())
      if sys.argv[i].lower() == u'skipusers':
        f = openFile(sys.argv[i+1])
        for line in f:
          skipusers.append(line.rstrip())
      i += 2
    elif sys.argv[i].lower() == u'includetrashed': 
      trashed = True
      i += 1
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if user.find(u'@') == -1:
      print u'ERROR: got %s, expected a full email address' % user
      sys.exit(2)
    sys.stderr.write(u'Getting all files for %s...\n' % user)
    page_message = u' got %%%%total_items%%%% files for %s...\n' % user
    feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message,
                         fields=u'items(id,parents(id),mimeType,owners(emailAddress),labels(trashed)),nextPageToken', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    permissionId = callGAPI(service=drive.permissions(), function=u'getIdForEmail', email=user, fields=u'id')[u'id']
    # check if user is owner of target_folder
    for f_file in feed:
      if f_file[u'id'] == target_folder:
        owner = f_file[u'owners'][0][u'emailAddress']
        if owner.lower() != user:
          files.append((owner, f_file[u'id']))
    i = 0
    timestamp = time.time()
    timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print u'%s: %s claiming folder %s' % (timestamp, user, target_folder)
    if skipfiles:
      print u' skipping file(s): "%s"' % skipfiles
    if skipfolders:
      print u' excluding folders(s): "%s' % skipfolders
    if skipusers:
      print u' excluding user(s): "%s' % skipusers
    print u' checking %s files in users drive' % len(feed)
    claimDriveFolderContents(user, i, files, feed, target_folder, permissionId, skipfiles, skipfolders, skipusers, trashed)

def claimDriveFolderContents(target_user, i, files, feed, target_folder, permissionId, skipfiles, skipfolders, skipusers, trashed):
  for f_file in feed:
    i += 1
    for parent in f_file[u'parents']:
      if target_folder == parent[u'id']:
        owner = f_file[u'owners'][0][u'emailAddress']
        # excluding trashed files (not sure if this is needed though, since all checking is done from the "claiming" user)
        if owner.lower() != target_user and f_file[u'id'] not in skipfiles and owner not in skipusers:
          if not trashed and not f_file[u'labels'][u'trashed'] or trashed:
            files.append((owner, f_file[u'id']))
        # not checking trashed folders (n.b. trashed folders could contain files that aren't trashed)
        if f_file[u'mimeType'] == u'application/vnd.google-apps.folder'and f_file[u'id'] not in skipfolders:
          if not trashed and not f_file[u'labels'][u'trashed'] or trashed:
            claimDriveFolderContents(target_user, i, files, feed, f_file[u'id'], permissionId, skipfiles, skipfolders, skipusers, trashed)
  if i == len(feed):
    if files:
      # sorting files per owner
      files.sort()
      source_user = ''
      tr_files = []
      j = 1
      for f_owner, f_id in files:
        if source_user == '':
          source_user = f_owner
        if f_owner == source_user:
          tr_files.append(f_id)
        if f_owner != source_user:
          claimDriveFiles(source_user, tr_files, permissionId, target_user)
          # reset source_user and files for new transfer 
          source_user = f_owner
          del tr_files[:]
          tr_files.append(f_id)
        if j == len(files):
          claimDriveFiles(source_user, tr_files, permissionId, target_user)
        j += 1
    print u'--- READY ---\n'

def claimDriveFiles(source_user, files, permissionId, target_user):
  userdomain = source_user.split("@")
  transferOwnership = True
  sendNotificationEmails = False
  emailMessage = None
  body = {u'role': u'owner'}
  bodyAdd = {u'role': u'writer', u'type': u'user', u'value': target_user}
  if userdomain[1] == GC_Values[GC_DOMAIN]:
    source_drive = buildGAPIServiceObject(u'drive', source_user)
    for file_id in files:
      print '  transferring %s from user %s to new owner %s' % (file_id, source_user, target_user)
      try:
        result = callGAPI(service=source_drive.permissions(), function=u'patch', fileId=file_id, permissionId=permissionId, transferOwnership=transferOwnership, body=body)
      except:
        # if claimer not in ACL (file might be visible for all with link)
        print '   adding %s to drivefileACL for file %s' % (target_user, file_id)
        result = callGAPI(service=source_drive.permissions(), function=u'insert', fileId=file_id, sendNotificationEmails=sendNotificationEmails, body=bodyAdd)
        print '   now transferring %s from user %s to new owner %s' % (file_id, source_user, target_user)
        result = callGAPI(service=source_drive.permissions(), function=u'patch', fileId=file_id, permissionId=permissionId, transferOwnership=transferOwnership, body=body)
    print u' transferred %s files from %s to %s' % (len(files), source_user, target_user)
  else:
    print u'    could not transfer files for user %s - user is on other domain:' % source_user
    for file in files:
      print u'     %s' % file

def transferDriveFolder(users):
  target_user = ''
  trashed = False
  # assign variables, and checking skipfiles and skipfolders
  target_folder = sys.argv[5]
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'newowner':
      target_user = sys.argv[i+1]
      target_user += u'@' + GC_Values[GC_DOMAIN]
      i += 2
    elif sys.argv[i].lower() == u'includetrashed': 
      trashed = True
      i += 1
  for source_user in users:
    if source_user.find(u'@') == -1:
      print u'ERROR: got %s, expected a full email address' % source_user
      sys.exit(2)
    drive = buildGAPIServiceObject(u'drive', target_user)
    permissionId = callGAPI(service=drive.permissions(), function=u'getIdForEmail', email=target_user, fields=u'id')[u'id']
    del drive
    drive = buildGAPIServiceObject(u'drive', source_user)
    sys.stderr.write(u'Getting all files for %s...\n' % source_user)
    page_message = u' got %%%%total_items%%%% files for %s...\n' % source_user
    feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message,
                         fields=u'items(id,parents(id),mimeType,owners(emailAddress),labels(trashed)),nextPageToken', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
    body = {u'role': u'owner'}
    bodyAdd = {u'role': u'writer', u'type': u'user', u'value': target_user}
    #check ownership on target_folder
    for f_file in feed:
      if f_file[u'id'] == target_folder:
        owner = f_file[u'owners'][0][u'emailAddress']
        if owner.lower() == source_user:
          file_id = f_file[u'id']
          try:
            result = callGAPI(service=drive.permissions(), function=u'patch', fileId=file_id, permissionId=permissionId, transferOwnership=True, body=body)
            print '  transferring %s from user %s to new owner %s' % (file_id, source_user, target_user)
          except:
            print '   adding %s to drivefileACL for file %s' % (target_user, file_id)
            result = callGAPI(service=drive.permissions(), function=u'insert', fileId=file_id, sendNotificationEmails=False, emailMessage=None, body=bodyAdd)
            print '   now transferring %s from user %s to new owner %s' % (file_id, source_user, target_user)
            result = callGAPI(service=drive.permissions(), function=u'patch', fileId=file_id, permissionId=permissionId, transferOwnership=True, body=body)
    transferDriveFolderContents(drive, source_user, target_user, permissionId, body, bodyAdd, feed, target_folder, trashed)

def transferDriveFolderContents(drive, source_user, target_user, permissionId, body, bodyAdd, feed, folder_id, trashed):
  for f_file in feed:
    for parent in f_file[u'parents']:
      if folder_id == parent[u'id']:
        owner = f_file[u'owners'][0][u'emailAddress']
        if owner.lower() == source_user:
          file_id = f_file[u'id']
          if not trashed and not f_file[u'labels'][u'trashed'] or trashed:
            try:
              result = callGAPI(service=drive.permissions(), function=u'patch', fileId=file_id, permissionId=permissionId, transferOwnership=True, body=body)
              print '  transferring %s from user %s to new owner %s' % (file_id, source_user, target_user)
            except:
              # this might happen if target user isn't explicitly in ACL (i.e. shared with anyone)
              print '   adding %s to drivefileACL for file %s' % (target_user, file_id)
              result = callGAPI(service=drive.permissions(), function=u'insert', fileId=file_id, sendNotificationEmails=False, emailMessage=None, body=bodyAdd)
              print '   now transferring %s from user %s to new owner %s' % (fileId, source_user, target_user)
              result = callGAPI(service=drive.permissions(), function=u'patch', fileId=file_id, permissionId=permissionId, transferOwnership=True, body=body)
        if f_file[u'mimeType'] == u'application/vnd.google-apps.folder':
          if not trashed and not f_file[u'labels'][u'trashed'] or trashed:
            transferDriveFolderContents(drive, source_user, target_user, permissionId, body, bodyAdd, feed, f_file[u'id'], trashed)

def deleteEmptyDriveFolders(users):
  query = u'"me" in owners and mimeType = "application/vnd.google-apps.folder"'
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if user.find(u'@') == -1:
      print u'ERROR: got %s, expected a full email address' % user
      sys.exit(2)
    deleted_empty = True
    while deleted_empty:
      sys.stderr.write(u'Getting folders for %s...\n' % user)
      page_message = u' got %%%%total_items%%%% folders for %s...\n' % user
      feed = callGAPIpages(service=drive.files(), function=u'list', page_message=page_message,
                           q=query, fields=u'items(title,id),nextPageToken', maxResults=GC_Values[GC_DRIVE_MAX_RESULTS])
      deleted_empty = False
      for folder in feed:
        children = callGAPI(service=drive.children(), function=u'list',
                            folderId=folder[u'id'], fields=u'items(id)', maxResults=1)
        if not u'items' in children or len(children[u'items']) == 0:
          print convertUTF8(u' deleting empty folder %s...' % folder[u'title'])
          callGAPI(service=drive.files(), function=u'delete', fileId=folder[u'id'])
          deleted_empty = True
        else:
          print convertUTF8(u' not deleting folder %s because it contains at least 1 item (%s)' % (folder[u'title'], children[u'items'][0][u'id']))

def doUpdateDriveFile(users):
  convert = ocr = ocrLanguage = parent_query = local_filepath = media_body = fileIds = drivefilename = None
  operation = u'update'
  i = 5
  body = {}
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'localfile':
      local_filepath = sys.argv[i+1]
      local_filename = ntpath.basename(local_filepath)
      mimetype = mimetypes.guess_type(local_filepath)[0]
      if mimetype == None:
        mimetype = u'application/octet-stream'
      body[u'title'] = local_filename
      body[u'mimeType'] = mimetype
      i += 2
    elif sys.argv[i].lower() == u'copy':
      operation = u'copy'
      i += 1
    elif sys.argv[i].lower() == u'id':
      fileIds = [sys.argv[i+1],]
      i += 2
    elif sys.argv[i].lower() == u'drivefilename':
      drivefilename = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'newfilename':
      body[u'title'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'convert']:
      convert = True
      i += 1
    elif sys.argv[i].lower() in [u'ocr',]:
      ocr = True
      i += 1
    elif sys.argv[i].lower() in [u'ocrlanguage',]:
      ocrLanguage = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'restrict', 'restricted']:
      if 'labels' not in body:
        body[u'labels'] = dict()
      if sys.argv[i+1].lower() in true_values:
        body[u'labels'][u'restricted'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'labels'][u'restricted'] = False
      else:
        print u'ERROR: value for restricted must be true or false, got %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() in [u'star', u'starred']:
      if u'labels' not in body:
        body[u'labels'] = dict()
      if sys.argv[i+1].lower() in true_values:
        body[u'labels'][u'starred'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'labels'][u'starred'] = False
      else:
        print u'ERROR: value for starred must be true or false, got %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() in [u'trash', u'trashed']:
      if u'labels' not in body:
        body[u'labels'] = dict()
      if sys.argv[i+1].lower() in true_values:
        body[u'labels'][u'trashed'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'labels'][u'trashed'] = False
      else:
        print u'ERROR: value for trashed must be true or false, got %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() in [u'view', u'viewed']:
      if u'labels' not in body:
        body[u'labels'] = dict()
      if sys.argv[i+1].lower() in true_values:
        body[u'labels'][u'viewed'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'labels'][u'viewed'] = False
      else:
        print u'ERROR: value for viewed must be true or false, got %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'lastviewedbyme':
      body[u'lastViewedByMe'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'modifieddate':
      body[u'modifiedDate'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'description',]:
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'mimetype',]:
      body[u'mimeType'] = sys.argv[i+1]
      if body[u'mimeType'].lower() in [u'gdoc', u'gdocument']:
        body[u'mimeType'] = u'application/vnd.google-apps.document'
      elif body[u'mimeType'].lower() == u'gdrawing':
        body[u'mimeType'] = u'application/vnd.google-apps.drawing'
      elif body[u'mimeType'].lower() in [u'gfolder', u'gdirectory']:
        body[u'mimeType'] = u'application/vnd.google-apps.folder'
      elif body[u'mimeType'].lower() == u'gform':
        body[u'mimeType'] = u'application/vnd.google-apps.form'
      elif body[u'mimeType'].lower() == u'gfusion':
        body[u'mimeType'] = u'application/vnd.google-apps.fusiontable'
      elif body[u'mimeType'].lower() == u'gpresentation':
        body[u'mimeType'] = u'application/vnd.google-apps.presentation'
      elif body[u'mimeType'].lower() == u'gscript':
        body[u'mimeType'] = u'application/vnd.google-apps.script'
      elif body[u'mimeType'].lower() == u'gsite':
        body[u'mimeType'] = u'application/vnd.google-apps.sites'
      elif body[u'mimeType'].lower() in [u'gsheet', u'gspreadsheet']:
        body[u'mimeType'] = u'application/vnd.google-apps.spreadsheet'
      i += 2
    elif sys.argv[i].lower() in [u'parentid']:
      if u'parents' not in body:
        body[u'parents'] = list()
      body[u'parents'].append({u'id': sys.argv[i+1]})
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') in [u'parentname']:
      parent_query = u'mimeType = "application/vnd.google-apps.folder" and "me" in owners and title = "%s"' % sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'writerscantshare']:
      body[u'writersCanShare'] = False
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> update drivefile"' % sys.argv[i]
      sys.exit(2)
  if not fileIds and not drivefilename:
    print u'ERROR: you need to specify either id or query in order to determine the file(s) to update'
    sys.exit(2)
  elif fileIds and drivefilename:
    print u'ERROR: you cannot specify both an id and a query.'
    sys.exit(2)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if parent_query:
      more_parents = doDriveSearch(drive, query=parent_query)
      if u'parents' not in body:
        body[u'parents'] = list()
      for a_parent in more_parents:
        body[u'parents'].append({u'id': a_parent})
    if drivefilename:
      fileIds = doDriveSearch(drive, query=u'"me" in owners and title = "%s"' % drivefilename)
    if local_filepath:
      media_body = googleapiclient.http.MediaFileUpload(local_filepath, mimetype=mimetype, resumable=True)
    for fileId in fileIds:
      if operation == u'update':
        if media_body:
          result = callGAPI(service=drive.files(), function=u'update', fileId=fileId, convert=convert, ocr=ocr, ocrLanguage=ocrLanguage, media_body=media_body, body=body, fields='id')
        else:
          result = callGAPI(service=drive.files(), function=u'patch', fileId=fileId, convert=convert, ocr=ocr, ocrLanguage=ocrLanguage, body=body, fields='id,labels')
        try:
          print u'Successfully updated %s drive file with content from %s' % (result[u'id'], local_filename)
        except UnboundLocalError:
          print u'Successfully updated drive file/folder ID %s' % (result[u'id'])
      else:
        result = callGAPI(service=drive.files(), function=u'copy', fileId=fileId, convert=convert, ocr=ocr, ocrLanguage=ocrLanguage, body=body, fields=u'id,labels')
        print u'Successfully copied %s to %s' % (fileId, result[u'id'])

def createDriveFile(users):
  convert = ocr = ocrLanguage = parent_query = local_filepath = media_body = None
  i = 5
  body = {}
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'localfile':
      local_filepath = sys.argv[i+1]
      local_filename = ntpath.basename(local_filepath)
      mimetype = mimetypes.guess_type(local_filepath)[0]
      if mimetype == None:
        mimetype = u'application/octet-stream'
      body[u'title'] = local_filename
      body[u'mimeType'] = mimetype
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') == u'drivefilename':
      body[u'title'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'convert']:
      convert = True
      i += 1
    elif sys.argv[i].lower() in [u'ocr',]:
      ocr = True
      i += 1
    elif sys.argv[i].lower() in [u'ocrlanguage',]:
      ocrLanguage = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'restrict', 'restricted']:
      if u'labels' not in body:
        body[u'labels'] = dict()
      body[u'labels'][u'restricted'] = True
      i += 1
    elif sys.argv[i].lower() in [u'star', u'starred']:
      if u'labels' not in body:
        body[u'labels'] = dict()
      body[u'labels'][u'starred'] = True
      i += 1
    elif sys.argv[i].lower() in [u'trash', u'trashed']:
      if u'labels' not in body:
        body[u'labels'] = dict()
      body[u'labels'][u'trashed'] = True
      i += 1
    elif sys.argv[i].lower() in [u'view', u'viewed']:
      if u'labels' not in body:
        body[u'labels'] = dict()
      body[u'labels'][u'viewed'] = True
      i += 1
    elif sys.argv[i].lower() == u'lastviewedbyme':
      body[u'lastViewedByMe'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'modifieddate':
      body[u'modifiedDate'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'description',]:
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'mimetype',]:
      body[u'mimeType'] = sys.argv[i+1]
      if body[u'mimeType'].lower() in [u'gdoc', u'gdocument']:
        body[u'mimeType'] = u'application/vnd.google-apps.document'
      elif body[u'mimeType'].lower() == u'gdrawing':
        body[u'mimeType'] = u'application/vnd.google-apps.drawing'
      elif body[u'mimeType'].lower() in [u'gfolder', u'gdirectory']:
        body[u'mimeType'] = u'application/vnd.google-apps.folder'
      elif body[u'mimeType'].lower() == u'gform':
        body[u'mimeType'] = u'application/vnd.google-apps.form'
      elif body[u'mimeType'].lower() == u'gfusion':
        body[u'mimeType'] = u'application/vnd.google-apps.fusiontable'
      elif body[u'mimeType'].lower() == u'gpresentation':
        body[u'mimeType'] = u'application/vnd.google-apps.presentation'
      elif body[u'mimeType'].lower() == u'gscript':
        body[u'mimeType'] = u'application/vnd.google-apps.script'
      elif body[u'mimeType'].lower() == u'gsite':
        body[u'mimeType'] = u'application/vnd.google-apps.sites'
      elif body[u'mimeType'].lower() in [u'gsheet', u'gspreadsheet']:
        body[u'mimeType'] = u'application/vnd.google-apps.spreadsheet'
      i += 2
    elif sys.argv[i].lower() in [u'parentid']:
      if u'parents' not in body:
        body[u'parents'] = list()
      body[u'parents'].append({u'id': sys.argv[i+1]})
      i += 2
    elif sys.argv[i].lower().replace(u'_', u'') in [u'parentname']:
      parent_query = u'mimeType = "application/vnd.google-apps.folder" and "me" in owners and title = "%s"' % sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'writerscantshare']:
      body[u'writersCanShare'] = False
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> create drivefile"' % sys.argv[i]
      sys.exit(2)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if parent_query:
      more_parents = doDriveSearch(drive, query=parent_query)
      if u'parents' not in body:
        body[u'parents'] = list()
      for a_parent in more_parents:
        body[u'parents'].append({u'id': a_parent})
    if local_filepath:
      media_body = googleapiclient.http.MediaFileUpload(local_filepath, mimetype=mimetype, resumable=True)
    result = callGAPI(service=drive.files(), function=u'insert', convert=convert, ocr=ocr, ocrLanguage=ocrLanguage, media_body=media_body, body=body, fields='id')
    try:
      print u'Successfully uploaded %s to Drive file ID %s' % (local_filename, result[u'id'])
    except UnboundLocalError:
      print u'Successfully created drive file/folder ID %s' % (result[u'id'])

def downloadDriveFile(users):
  i = 5
  query = fileIds = None
  gdownload_format = u'openoffice'
  target_folder = GC_Values[GC_DRIVE_DIR]
  safe_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'id':
      fileIds = [sys.argv[i+1],]
      i += 2
    elif sys.argv[i].lower() == 'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'format':
      gdownload_format = sys.argv[i+1].lower()
      if gdownload_format not in [u'openoffice', u'ms', u'microsoft', u'micro$oft', u'pdf']:
        print 'ERROR: format must be one of openoffice, microsoft or pdf. Got %s' % gdownload_format
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower().replace('_', '') == u'targetfolder':
      target_folder = sys.argv[i+1]
      if not os.path.isdir(target_folder):
        os.makedirs(target_folder)
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> get drivefile"' % sys.argv[i]
      sys.exit(2)
  export_extensions = {u'application/pdf': '.pdf',
                       u'application/vnd.openxmlformats-officedocument.wordprocessingml.document': u'.docx',
                       u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': u'.xlsx',
                       u'application/vnd.openxmlformats-officedocument.presentationml.presentation': u'.pptx',
                       u'application/vnd.oasis.opendocument.text': u'.odt',
                       u'application/x-vnd.oasis.opendocument.spreadsheet': u'.ods'}
  if gdownload_format == u'openoffice':
    export_formats = [u'application/vnd.oasis.opendocument.text',
                      u'application/x-vnd.oasis.opendocument.spreadsheet']
  elif gdownload_format in [u'ms', u'microsoft', u'micro$oft']:
    export_formats = [u'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                      u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      u'application/vnd.openxmlformats-officedocument.presentationml.presentation']
  elif gdownload_format == u'pdf':
    export_formats = [u'application/pdf',]
  if not query and not fileIds:
    print u'ERROR: need to specify a file ID with id parameter or a search query with the query parameter.'
    sys.exit(2)
  elif query and fileIds:
    print u'ERROR: you cannot specify both the id and query parameters at the same time.'
    sys.exit(2)
  for user in users:
    drive = buildGAPIServiceObject(u'drive', user)
    if query:
      fileIds = doDriveSearch(drive, query=query)
    else:
      if fileIds[0][:8].lower() == 'https://' or fileIds[0][:7].lower() == 'http://':
        fileIds[0] = fileIds[0][fileIds[0].find('/d/')+3:]
        if fileIds[0].find('/') != -1:
          fileIds[0] = fileIds[0][:fileIds[0].find('/')]
    if not fileIds:
      print u'No files to download for %s' % user
    i = 0
    for fileId in fileIds:
      extension = None
      result = callGAPI(service=drive.files(), function=u'get', fileId=fileId, fields=u'fileSize,title,mimeType,downloadUrl,exportLinks')
      if result[u'mimeType'] == u'application/vnd.google-apps.folder':
        print convertUTF8(u'Skipping download of folder %s' % result[u'title'])
        continue
      try:
        result[u'fileSize'] = int(result[u'fileSize'])
        if result[u'fileSize'] < 1024:
          filesize = u'1kb'
        elif result[u'fileSize'] < (1024 * 1024):
          filesize = u'%skb' % (result[u'fileSize'] / 1024)
        elif result[u'fileSize'] < (1024 * 1024 * 1024):
          filesize = u'%smb' % (result[u'fileSize'] / 1024 / 1024)
        else:
          filesize = u'%sgb' % (result[u'fileSize'] / 1024 / 1024 / 1024)
        my_line = u'Downloading: %%s of %s bytes' % filesize
      except KeyError:
        my_line = u'Downloading Google Doc: %s'
      if u'downloadUrl' in result:
        download_url = result[u'downloadUrl']
      elif u'exportLinks' in result:
        for avail_export_format in result[u'exportLinks']:
          if avail_export_format in export_formats:
            download_url = result[u'exportLinks'][avail_export_format]
            try:
              extension = export_extensions[avail_export_format]
            except KeyError:
              pass
            break
        else:
          print convertUTF8(u'Skipping download of file {0}, Format {1} not available'.format(result[u'title'], ','.join(export_formats)))
          continue
      else:
        print convertUTF8(u'Skipping download of file {0}, Format not downloadable')
        continue
      file_title = result[u'title']
      safe_file_title = ''.join(c for c in file_title if c in safe_filename_chars)
      filename = os.path.join(target_folder, safe_file_title)
      if extension and filename.lower()[:len(extension)] != extension:
        filename = u'%s%s' % (filename, extension)
      y = 0
      if os.path.isfile(filename):
        while True:
          y += 1
          new_filename = os.path.join(target_folder, u'(%s)-%s' % (y, safe_file_title))
          if extension and new_filename.lower()[:len(extension)] != extension:
            new_filename = u'%s%s' % (new_filename, extension)
          if not os.path.isfile(new_filename):
            break
        filename = new_filename
      print convertUTF8(my_line % filename)
      _, content = drive._http.request(download_url)
      writeFile(filename, content, continueOnError=True)

def showDriveFileInfo(users):
  for user in users:
    fileId = sys.argv[5]
    drive = buildGAPIServiceObject(u'drive', user)
    feed = callGAPI(service=drive.files(), function=u'get', fileId=fileId)
    for setting in feed:
      if setting == u'kind':
        continue
      setting_type = str(type(feed[setting]))
      if setting_type == u"<type 'list'>":
        print u'%s:' % setting
        for settin in feed[setting]:
          if settin == u'kind':
            continue
          settin_type = str(type(settin))
          if settin_type == u"<type 'dict'>":
            for setti in settin:
              if setti == u'kind':
                continue
              print convertUTF8(u' %s: %s' % (setti, settin[setti]))
            print u''
      elif setting_type == u"<type 'dict'>":
        print u'%s:' % setting
        for settin in feed[setting]:
          if settin == u'kind':
            continue
          print convertUTF8(u' %s: %s' % (settin, feed[setting][settin]))
      else:
        print convertUTF8(u'%s: %s' % (setting, feed[setting]))

def transferSecCals(users):
  target_user = sys.argv[5]
  remove_source_user = True
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'keepuser':
      remove_source_user = False
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> transfer seccals"' % sys.argv[i]
      sys.exit(2)
  for user in users:
    source_cal = buildGAPIServiceObject(u'calendar', user)
    source_calendars = callGAPIpages(service=source_cal.calendarList(), function=u'list', minAccessRole=u'owner', showHidden=True, fields=u'items(id),nextPageToken')
    for source_cal in source_calendars:
      if source_cal[u'id'].find(u'@group.calendar.google.com') != -1:
        doCalendarAddACL(calendarId=source_cal[u'id'], act_as=user, role=u'owner', scope=u'user', entity=target_user)
        if remove_source_user:
          doCalendarAddACL(calendarId=source_cal[u'id'], act_as=target_user, role=u'none', scope=u'user', entity=user)

def transferDriveFiles(users):
  target_user = sys.argv[5]
  remove_source_user = True
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'keepuser':
      remove_source_user = False
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> transfer drive"' % sys.argv[i]
      sys.exit(2)
  target_drive = buildGAPIServiceObject(u'drive', target_user)
  target_about = callGAPI(service=target_drive.about(), function=u'get', fields=u'quotaBytesTotal,quotaBytesUsed,rootFolderId')
  target_drive_free = int(target_about[u'quotaBytesTotal']) - int(target_about[u'quotaBytesUsed'])
  for user in users:
    counter = 0
    source_drive = buildGAPIServiceObject(u'drive', user)
    source_about = callGAPI(service=source_drive.about(), function=u'get', fields=u'quotaBytesTotal,quotaBytesUsed,rootFolderId, permissionId')
    source_drive_size = int(source_about[u'quotaBytesUsed'])
    if target_drive_free < source_drive_size:
      systemErrorExit(4, MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE.format(source_drive_size / 1024 / 1024, target_drive_free / 1024 / 1024))
    print u'Source drive size: %smb  Target drive free: %smb' % (source_drive_size / 1024 / 1024, target_drive_free / 1024 / 1024)
    target_drive_free = target_drive_free - source_drive_size # prep target_drive_free for next user
    source_root = source_about[u'rootFolderId']
    source_permissionid = source_about[u'permissionId']
    print u"Getting file list for source user: %s..." % user
    page_message = u'  got %%total_items%% files\n'
    source_drive_files = callGAPIpages(service=source_drive.files(), function=u'list', page_message=page_message,
                                       q=u"'me' in owners and trashed = false", fields=u'items(id,parents,mimeType),nextPageToken')
    all_source_file_ids = []
    for source_drive_file in source_drive_files:
      all_source_file_ids.append(source_drive_file[u'id'])
    total_count = len(source_drive_files)
    print u"Getting folder list for target user: %s..." % target_user
    page_message = u'  got %%total_items%% folders\n'
    target_folders = callGAPIpages(service=target_drive.files(), function=u'list', page_message=page_message,
                                   q=u"'me' in owners and mimeType = 'application/vnd.google-apps.folder'", fields=u'items(id,title),nextPageToken')
    got_top_folder = False
    all_target_folder_ids = []
    for target_folder in target_folders:
      all_target_folder_ids.append(target_folder[u'id'])
      if (not got_top_folder) and target_folder[u'title'] == u'%s old files' % user:
        target_top_folder = target_folder[u'id']
        got_top_folder = True
    if not got_top_folder:
      create_folder = callGAPI(service=target_drive.files(), function=u'insert', body={u'title': u'%s old files' % user, u'mimeType': u'application/vnd.google-apps.folder'}, fields=u'id')
      target_top_folder = create_folder[u'id']
    transferred_files = []
    while True: # we loop thru, skipping files until all of their parents are done
      skipped_files = False
      for drive_file in source_drive_files:
        file_id = drive_file[u'id']
        if file_id in transferred_files:
          continue
        source_parents = drive_file[u'parents']
        skip_file_for_now = False
        for source_parent in source_parents:
          if source_parent[u'id'] not in all_source_file_ids and source_parent[u'id'] not in all_target_folder_ids:
            continue  # means this parent isn't owned by source or target, shouldn't matter
          if source_parent[u'id'] not in transferred_files and source_parent[u'id'] != source_root:
            #print 'skipping %s' % file_id
            skipped_files = skip_file_for_now = True
            break
        if skip_file_for_now:
          continue
        else:
          transferred_files.append(drive_file[u'id'])
        counter += 1
        print u'Changing owner for file %s (%s/%s)' % (drive_file[u'id'], counter, total_count)
        body = {u'role': u'owner', u'type': u'user', u'value': target_user}
        callGAPI(service=source_drive.permissions(), function=u'insert', soft_errors=True, fileId=file_id, sendNotificationEmails=False, body=body)
        target_parents = []
        for parent in source_parents:
          try:
            if parent[u'isRoot']:
              target_parents.append({u'id': target_top_folder})
            else:
              target_parents.append({u'id': parent[u'id']})
          except TypeError:
            pass
        callGAPI(service=target_drive.files(), function=u'patch', soft_errors=True, retry_reasons=[u'notFound'], fileId=file_id, body={u'parents': target_parents})
        if remove_source_user:
          callGAPI(service=target_drive.permissions(), function=u'delete', soft_errors=True, fileId=file_id, permissionId=source_permissionid)
      if not skipped_files:
        break

def doImap(users):
  if sys.argv[4].lower() in true_values:
    enable = True
  elif sys.argv[4].lower() in false_values:
    enable = False
  else:
    print u'ERROR: value for "gam <users> imap" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting IMAP Access to %s for %s (%s of %s)" % (str(enable), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateImap', soft_errors=True, username=user, enable=enable)

def getImap(users):
  emailsettings = getEmailSettingsObject()
  i = 1
  count = len(users)
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    imapsettings = callGData(service=emailsettings, function=u'GetImap', soft_errors=True, username=user)
    try:
      print u'User %s  IMAP Enabled:%s (%s of %s)' % (user+u'@'+emailsettings.domain, imapsettings[u'enable'], i, count)
    except TypeError:
      pass
    i += 1

def getProductAndSKU(sku):
  if sku.lower() in [u'apps', u'gafb', u'gafw']:
    sku = u'Google-Apps-For-Business'
  elif sku.lower() in [u'gams',]:
    sku = u'Google-Apps-For-Postini'
  elif sku.lower() in [u'gau', u'unlimited', u'd4w', u'dfw']:
    sku = u'Google-Apps-Unlimited'
  elif sku.lower() in [u'lite']:
    sku = u'Google-Apps-Lite'
  elif sku.lower() == u'coordinate':
    sku = u'Google-Coordinate'
  elif sku.lower() == u'vault':
    sku = u'Google-Vault'
  elif sku.lower() in [u'vfe',]:
    sku = u'Google-Vault-Former-Employee'
  elif sku.lower() in [u'drive-20gb', u'drive20gb', u'20gb']:
    sku = u'Google-Drive-storage-20GB'
  elif sku.lower() in [u'drive-50gb', u'drive50gb', u'50gb']:
    sku = u'Google-Drive-storage-50GB'
  elif sku.lower() in [u'drive-200gb', u'drive200gb', u'200gb']:
    sku = u'Google-Drive-storage-200GB'
  elif sku.lower() in [u'drive-400gb', u'drive400gb', u'400gb']:
    sku = u'Google-Drive-storage-400GB'
  elif sku.lower() in [u'drive-1tb', u'drive1tb', u'1tb']:
    sku = u'Google-Drive-storage-1TB'
  elif sku.lower() in [u'drive-2tb', u'drive2tb', u'2tb']:
    sku = u'Google-Drive-storage-2TB'
  elif sku.lower() in [u'drive-4tb', u'drive4tb', u'4tb']:
    sku = u'Google-Drive-storage-4TB'
  elif sku.lower() in [u'drive-4tb', u'drive8tb', u'8tb']:
    sku = u'Google-Drive-storage-8TB'
  elif sku.lower() in [u'drive-16tb', u'drive16tb', u'16tb']:
    sku = u'Google-Drive-storage-16TB'
  if sku[:20] == u'Google-Drive-storage':
    product = u'Google-Drive-storage'
  else:
    try:
      product = re.search(u'^([A-Z,a-z]*-[A-Z,a-z]*)', sku).group(1)
    except AttributeError:
      product = sku
  return (product, sku)

def doLicense(users, operation):
  lic = buildGAPIObject(u'licensing')
  sku = sys.argv[5]
  productId, skuId = getProductAndSKU(sku)
  for user in users:
    if user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    if operation == u'delete':
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=skuId, userId=user)
    elif operation == u'insert':
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=skuId, body={u'userId': user})
    elif operation == u'patch':
      try:
        old_sku = sys.argv[6]
        if old_sku.lower() == u'from':
          old_sku = sys.argv[7]
      except KeyError:
        print u'ERROR: You need to specify the user\'s old SKU as the last argument'
        sys.exit(2)
      _, old_sku = getProductAndSKU(old_sku)
      callGAPI(service=lic.licenseAssignments(), function=operation, soft_errors=True, productId=productId, skuId=old_sku, userId=user, body={u'skuId': skuId})

def doPop(users):
  if sys.argv[4].lower() in true_values:
    enable = True
  elif sys.argv[4].lower() in false_values:
    enable = False
  else:
    print u'ERROR: value for "gam <users> pop" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  enable_for = u'ALL_MAIL'
  action = u'KEEP'
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'for':
      if sys.argv[i+1].lower() == u'allmail':
        enable_for = u'ALL_MAIL'
        i += 2
      elif sys.argv[i+1].lower() == u'newmail':
        enable_for = u'MAIL_FROM_NOW_ON'
        i += 2
      else:
        print u'ERROR: %s is not a valid argument for "gam <users> pop for"' % sys.argv[i]
        sys.exit(2)
    elif sys.argv[i].lower() == u'action':
      if sys.argv[i+1].lower() == u'keep':
        action = u'KEEP'
        i += 2
      elif sys.argv[i+1].lower() == u'archive':
        action = u'ARCHIVE'
        i += 2
      elif sys.argv[i+1].lower() == u'delete':
        action = u'DELETE'
        i += 2
      else:
        print u'ERROR: %s is not a valid argument for "gam <users> pop action"' % sys.argv[i]
        sys.exit(2)
    elif sys.argv[i].lower() == u'confirm':
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> pop"' % sys.argv[i]
      sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting POP Access to %s for %s (%s of %s)" % (str(enable), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdatePop', soft_errors=True, username=user, enable=enable, enable_for=enable_for, action=action)

def getPop(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    popsettings = callGData(service=emailsettings, function=u'GetPop', soft_errors=True, username=user)
    try:
      print u'User %s  POP Enabled:%s  Action:%s' % (user+u'@'+emailsettings.domain, popsettings[u'enable'], popsettings[u'action'])
    except TypeError:
      pass

def doSendAs(users):
  sendas = sys.argv[4]
  sendasName = sys.argv[5]
  make_default = reply_to = None
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'default':
      make_default = True
      i += 1
    elif sys.argv[i].lower() == u'replyto':
      reply_to = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> sendas"' % sys.argv[i]
      sys.exit(2)
  emailsettings = getEmailSettingsObject()
  if sendas.find(u'@') < 0:
    sendas = sendas+u'@'+GC_Values[GC_DOMAIN]
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Allowing %s to send as %s (%s of %s)" % (user+u'@'+emailsettings.domain, sendas, i, count)
    i += 1
    callGData(service=emailsettings, function=u'CreateSendAsAlias', soft_errors=True, username=user, name=sendasName, address=sendas, make_default=make_default, reply_to=reply_to)

def showSendAs(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    print u'%s has the following send as aliases:' %  (user+u'@'+emailsettings.domain)
    sendases = callGData(service=emailsettings, function=u'GetSendAsAlias', soft_errors=True, username=user)
    try:
      for sendas in sendases:
        if sendas[u'isDefault'] == u'true':
          default = u'yes'
        else:
          default = u'no'
        if sendas[u'replyTo']:
          replyto = u' Reply To:<'+sendas[u'replyTo']+'>'
        else:
          replyto = u''
        if sendas[u'verified'] == u'true':
          verified = u'yes'
        else:
          verified = u'no'
        print u' "%s" <%s>%s Default:%s Verified:%s' % (sendas[u'name'], sendas[u'address'], replyto, default, verified)
    except TypeError:
      pass
    print u''

def doLanguage(users):
  language = sys.argv[4]
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting the language for %s to %s (%s of %s)" % (user+u'@'+emailsettings.domain, language, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateLanguage', soft_errors=True, username=user, language=language)

def doUTF(users):
  if sys.argv[4].lower() in true_values:
    SetUTF = True
  elif sys.argv[4].lower() in false_values:
    SetUTF = False
  else:
    print u'ERROR: value for "gam <users> utf" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting UTF-8 to %s for %s (%s of %s)" % (str(SetUTF), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, unicode=SetUTF)

def doPageSize(users):
  if sys.argv[4] == u'25' or sys.argv[4] == u'50' or sys.argv[4] == u'100':
    PageSize = sys.argv[4]
  else:
    print u'ERROR: %s is not a valid argument for "gam <users> pagesize"' % sys.argv[4]
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Page Size to %s for %s (%s of %s)" % (PageSize, user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, page_size=PageSize)

def doShortCuts(users):
  if sys.argv[4].lower() in true_values:
    SetShortCuts = True
  elif sys.argv[4].lower() in false_values:
    SetShortCuts = False
  else:
    print u'ERROR: value for "gam <users> shortcuts" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Keyboard Short Cuts to %s for %s (%s of %s)" % (str(SetShortCuts), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, shortcuts=SetShortCuts)

def doArrows(users):
  if sys.argv[4].lower() in true_values:
    SetArrows = True
  elif sys.argv[4].lower() in false_values:
    SetArrows = False
  else:
    print u'ERROR: value for "gam <users> arrows" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Personal Indicator Arrows to %s for %s (%s of %s)" % (str(SetArrows), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, arrows=SetArrows)

def doSnippets(users):
  if sys.argv[4].lower() in true_values:
    SetSnippets = True
  elif sys.argv[4].lower() in false_values:
    SetSnippets = False
  else:
    print u'ERROR: value for "gam <users> snippets" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Preview Snippets to %s for %s (%s of %s)" % (str(SetSnippets), user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateGeneral', soft_errors=True, username=user, snippets=SetSnippets)

def doLabel(users):
  label = sys.argv[4]
  count = len(users)
  i = 1
  n = 5
  if sys.argv[3].lower() == u'add':
    n = 6
    label = sys.argv[5]
  body = {u'name': label}
  while n < len(sys.argv):
    if sys.argv[n].lower().replace(u'_', u'') == u'labellistvisibility':
      if sys.argv[n+1].lower().replace(u'_', u'') == u'hide':
        body[u'labelListVisibility'] = u'labelHide'
      elif sys.argv[n+1].lower().replace(u'_', u'') == u'show':
        body[u'labelListVisibility'] = u'labelShow'
      elif sys.argv[n+1].lower().replace(u'_', u'') == u'showifunread':
        body[u'labelListVisibility'] = u'labelShowIfUnread'
      else:
        print u'ERROR: label_list_visibility must be one of hide, show or show_if_unread, got %s' % sys.argv[n+1]
        sys.exit(2)
      n += 2
    elif sys.argv[n].lower().replace(u'_', u'') == u'messagelistvisibility':
      if sys.argv[n+1].lower().replace(u'_', u'') == u'hide':
        body[u'messageListVisibility'] = u'hide'
      elif sys.argv[n+1].lower().replace(u'_', u'') == u'show':
        body[u'messageListVisibility'] = u'show'
      else:
        print u'ERROR: message_list_visibility must be one of hide or show, got %s' % sys.argv[n+1]
        sys.exit(2)
      n += 2
    else:
      print u'ERROR: %s is not a valid argument for this command.' % sys.argv[n]
      sys.exit(2)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', user)
    print u"Creating label %s for %s (%s of %s)" % (label, user, i, count)
    i += 1
    callGAPI(service=gmail.users().labels(), function=u'create', soft_errors=True, userId=user, body=body)

PROCESS_MESSAGE_FUNCTION_TO_ACTION_MAP = {u'delete': u'deleted', u'trash': u'trashed', u'untrash': u'untrashed', u'modify': u'modified'}

def labelsToLabelIds(gmail, labels):
  allLabels = {
    u'INBOX': u'INBOX', u'SPAM': u'SPAM', u'TRASH': u'TRASH',
    u'UNREAD': u'UNREAD', u'STARRED': u'STARRED', u'IMPORTANT': u'IMPORTANT',
    u'SENT': u'SENT', u'DRAFT': u'DRAFT',
    u'CATEGORY_PERSONAL': u'CATEGORY_PERSONAL',
    u'CATEGORY_SOCIAL': u'CATEGORY_SOCIAL',
    u'CATEGORY_PROMOTIONS': u'CATEGORY_PROMOTIONS',
    u'CATEGORY_UPDATES': u'CATEGORY_UPDATES',
    u'CATEGORY_FORUMS': u'CATEGORY_FORUMS',
    }
  labelIds = list()
  for label in labels:
    if label not in allLabels:
      # first refresh labels in user mailbox
      label_results = callGAPI(gmail.users().labels(), 'list',
                               userId='me', fields='labels(name,id,type)')
      for a_label in label_results['labels']:
        if a_label['type'] == 'system':
          allLabels[a_label['id']] = a_label['id']
        else:
          allLabels[a_label['name']] = a_label['id']
    if label not in allLabels:
      # if still not there, create it
      label_results = callGAPI(gmail.users().labels(), 'create',
                               body={'labelListVisibility': 'labelShow',
                                     'messageListVisibility': 'show', 'name': label},
                               userId='me', fields='id')
      allLabels[label] = label_results['id']
    try:
      labelIds.append(allLabels[label])
    except KeyError:
      pass
    if label.find('/') != -1:
      # make sure to create parent labels for proper nesting
      parent_label = label[:label.rfind('/')]
      while True:
        if not parent_label in allLabels:
          label_result = callGAPI(gmail.users().labels(), 'create',
                                  userId='me', body={'name': parent_label})
          allLabels[parent_label] = label_result['id']
        if parent_label.find('/') == -1:
          break
        parent_label = parent_label[:parent_label.rfind('/')]
  return labelIds

def doProcessMessages(users, function):
  query = None
  doIt = False
  maxToProcess = 1
  body = {}
  i = 5
  while i < len(sys.argv):
    myarg = sys.argv[i].lower().replace(u'_', u'')
    if myarg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif myarg == u'doit':
      doIt = True
      i += 1
    elif myarg in [u'maxtodelete', u'maxtotrash', u'maxtomodify', u'maxtountrash']:
      maxToProcess = int(sys.argv[i+1])
      i += 2
    elif (function == u'modify') and (myarg == u'addlabel'):
      body.setdefault(u'addLabelIds', [])
      body[u'addLabelIds'].append(sys.argv[i+1])
      i += 2
    elif (function == u'modify') and (myarg == u'removelabel'):
      body.setdefault(u'removeLabelIds', [])
      body[u'removeLabelIds'].append(sys.argv[i+1])
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> %s messages"' % (sys.argv[i], function)
      sys.exit(2)
  if not query:
    print u'ERROR: No query specified. You must specify some query!'
    sys.exit(2)
  action = PROCESS_MESSAGE_FUNCTION_TO_ACTION_MAP[function]
  for user in users:
    print u'Searching messages for %s' % user
    gmail = buildGAPIServiceObject(u'gmail', user)
    page_message = u'Got %%%%total_items%%%% messages for user %s' % user
    listResult = callGAPIpages(service=gmail.users().messages(),
                               function=u'list', items=u'messages', page_message=page_message,
                               userId=u'me', q=query, includeSpamTrash=True, soft_errors=True)
    result_count = len(listResult)
    if not doIt or result_count == 0:
      print u'would try to %s %s messages for user %s (max %s)\n' % (function, result_count, user, maxToProcess)
      continue
    elif result_count > maxToProcess:
      print u'WARNING: refusing to %s ANY messages for %s since max messages to process is %s and messages to be %s is %s\n' % (function, user, maxToProcess, action, result_count)
      continue
    i = 0
    if function == u'delete':
      id_batches = [[]]
      for del_me in listResult:
        id_batches[i].append(del_me[u'id'])
        if len(id_batches[i]) == 1000:
          i += 1
          id_batches.append([])
      deleted_messages = 0
      for id_batch in id_batches:
        print u'deleting %s messages' % len(id_batch)
        callGAPI(service=gmail.users().messages(), function=u'batchDelete',
                 body={u'ids': id_batch}, userId=u'me')
        deleted_messages += len(id_batch)
        print u'deleted %s of %s messages' % (deleted_messages, result_count)
      continue
    if not body:
      kwargs = {}
    else:
      kwargs = {u'body': {}}
      for my_key in body.keys():
        kwargs[u'body'][my_key] = labelsToLabelIds(gmail, body[my_key])
    for a_message in listResult:
      i += 1
      print u' %s message %s for user %s (%s/%s)' % (function, a_message[u'id'], user, i, result_count)
      callGAPI(service=gmail.users().messages(), function=function,
               id=a_message[u'id'], userId=u'me', **kwargs)

def doDeleteLabel(users):
  label = sys.argv[5]
  label_name_lower = label.lower()
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', user)
    print u'Getting all labels for %s...' % user
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user, fields=u'labels(name,id,type)')
    del_labels = []
    if label == u'--ALL_LABELS--':
      for del_label in labels[u'labels']:
        if del_label[u'type'] == u'system':
          continue
        del_labels.append(del_label)
    elif label[:6].lower() == u'regex:':
      regex = label[6:]
      p = re.compile(regex)
      for del_label in labels[u'labels']:
        if del_label[u'type'] == u'system':
          continue
        elif p.match(del_label[u'name']):
          del_labels.append(del_label)
    else:
      for del_label in labels[u'labels']:
        if label_name_lower == del_label[u'name'].lower():
          del_labels.append(del_label)
          break
      else:
        print u' Error: no such label for %s' % user
        continue
    del_me_count = len(del_labels)
    i = 1
    dbatch = googleapiclient.http.BatchHttpRequest()
    for del_me in del_labels:
      print u' deleting label %s (%s/%s)' % (del_me[u'name'], i, del_me_count)
      i += 1
      dbatch.add(gmail.users().labels().delete(userId=user, id=del_me[u'id']), callback=gmail_del_result)
      if len(dbatch._order) == 10:
        dbatch.execute()
        dbatch = googleapiclient.http.BatchHttpRequest()
    if len(dbatch._order) > 0:
      dbatch.execute()

def gmail_del_result(request_id, response, exception):
  if exception is not None:
    print exception

def showLabels(users):
  i = 5
  show_system = True
  while i < len(sys.argv):
    if sys.argv[i].lower().replace(u'_', u'') == u'onlyuser':
      show_system = False
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> show labels"' % sys.argv[i]
      sys.exit(2)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', user)
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user, soft_errors=True)
    if labels:
      for label in labels[u'labels']:
        if label[u'type'] == u'system' and not show_system:
          continue
        print convertUTF8(label[u'name'])
        for a_key in label:
          if a_key == u'name':
            continue
          print u' %s: %s' % (a_key, label[a_key])
        print u''

def showGmailProfile(users):
  todrive = False
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for gam <users> show gmailprofiles' % sys.argv[i]
      sys.exit(2)
  profiles = [{}]
  for user in users:
    print 'Getting Gmail profile for %s' % user
    gmail = buildGAPIServiceObject(u'gmail', user, soft_errors=True)
    if not gmail:
      continue
    results = callGAPI(service=gmail.users(), function=u'getProfile', userId=u'me', soft_errors=True)
    if results:
      for item in results:
        if item not in profiles[0]:
          profiles[0][item] = item
      profiles.append(results)
  output_csv(csv_list=profiles, titles=profiles[0], list_type=u'Gmail Profiles', todrive=todrive)

def updateLabels(users):
  label_name = sys.argv[5]
  label_name_lower = label_name.lower()
  body = {}
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'name'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower().replace(u'_', '') == u'messagelistvisibility':
      body[u'messageListVisibility'] = sys.argv[i+1].lower()
      if body[u'messageListVisibility'] not in [u'hide', u'show']:
        print 'ERROR: message_list_visibility should be show or hide, got %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower().replace(u' ', '') == u'labellistvisibility':
      if sys.argv[i+1].lower().replace(u'_', u'') == u'showifunread':
        body[u'labelListVisibility'] = u'labelShowIfUnread'
      elif sys.argv[i+1].lower().replace(u'_', u'') == u'show':
        body[u'labelListVisibility'] = u'labelShow'
      elif sys.argv[i+1].lower().replace(u'_', u'') == u'hide':
        body[u'labelListVisibility'] = u'labelHide'
      else:
        print 'ERROR: label_list_visibility should be hide, show or show_if_unread, got %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> update labels"' % sys.argv[i]
      sys.exit(2)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', user)
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user, fields=u'labels(id,name)')
    for label in labels[u'labels']:
      if label[u'name'].lower() == label_name_lower:
        callGAPI(service=gmail.users().labels(), function=u'patch', soft_errors=True,
                 userId=user, id=label[u'id'], body=body)
        break
    else:
      print 'Error: user does not have a label named %s' % label_name

def renameLabels(users):
  search = u'^Inbox/(.*)$'
  replace = u'%s'
  merge = False
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'search':
      search = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'replace':
      replace = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'merge':
      merge = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> rename label"' % sys.argv[i]
      sys.exit(2)
  pattern = re.compile(search, re.IGNORECASE)
  for user in users:
    gmail = buildGAPIServiceObject(u'gmail', user)
    labels = callGAPI(service=gmail.users().labels(), function=u'list', userId=user)
    for label in labels[u'labels']:
      if label[u'type'] == u'system':
        continue
      match_result = re.search(pattern, label[u'name'])
      if match_result != None:
        new_label_name = replace % match_result.groups()
        print u' Renaming "%s" to "%s"' % (label[u'name'], new_label_name)
        try:
          callGAPI(service=gmail.users().labels(), function=u'patch', soft_errors=True, throw_reasons=[u'aborted'], id=label[u'id'], userId=user, body={u'name': new_label_name})
        except googleapiclient.errors.HttpError:
          if merge:
            print u'  Merging %s label to existing %s label' % (label[u'name'], new_label_name)
            q = u'label:"%s"' % label[u'name']
            messages_to_relabel = callGAPIpages(service=gmail.users().messages(), function=u'list', items=u'messages', userId=user, q=q)
            if len(messages_to_relabel) > 0:
              for new_label in labels[u'labels']:
                if new_label[u'name'].lower() == new_label_name.lower():
                  new_label_id = new_label[u'id']
                  body = {u'addLabelIds': [new_label_id]}
                  break
              i = 1
              for message_to_relabel in messages_to_relabel:
                print u'    relabeling message %s (%s/%s)' % (message_to_relabel[u'id'], i, len(messages_to_relabel))
                callGAPI(service=gmail.users().messages(), function=u'modify', userId=user, id=message_to_relabel[u'id'], body=body)
                i += 1
            else:
              print u'   no messages with %s label' % label[u'name']
            print u'   Deleting label %s' % label[u'name']
            callGAPI(service=gmail.users().labels(), function=u'delete', id=label[u'id'], userId=user)
          else:
            print u'  Error: looks like %s already exists, not renaming. Use the "merge" argument to merge the labels' % new_label_name

def doFilter(users):
  i = 4 # filter arguments start here
  from_ = to = subject = has_the_word = does_not_have_the_word = has_attachment = label = should_mark_as_read = should_archive = should_star = forward_to = should_trash = should_not_spam = None
  haveCondition = False
  while sys.argv[i].lower() in [u'from', u'to', u'subject', u'haswords', u'nowords', u'musthaveattachment']:
    if sys.argv[i].lower() == u'from':
      from_ = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'to':
      to = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'subject':
      subject = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'haswords':
      has_the_word = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'nowords':
      does_not_have_the_word = sys.argv[i+1]
      i += 2
      haveCondition = True
    elif sys.argv[i].lower() == u'musthaveattachment':
      has_attachment = True
      i += 1
      haveCondition = True
  if not haveCondition:
    print u'ERROR: you must specifiy a condition for "gam <users> filter"'
    sys.exit(2)
  haveAction = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'label':
      label = sys.argv[i+1]
      i += 2
      haveAction = True
    elif sys.argv[i].lower() == u'markread':
      should_mark_as_read = True
      i += 1
      haveAction = True
    elif sys.argv[i].lower() == u'archive':
      should_archive = True
      i += 1
      haveAction = True
    elif sys.argv[i].lower() == u'star':
      should_star = True
      i += 1
      haveAction = True
    elif sys.argv[i].lower() == u'forward':
      forward_to = sys.argv[i+1]
      i += 2
      haveAction = True
    elif sys.argv[i].lower() == u'trash':
      should_trash = True
      i += 1
      haveAction = True
    elif sys.argv[i].lower() == u'neverspam':
      should_not_spam = True
      i += 1
      haveAction = True
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> filter"' % sys.argv[i]
      sys.exit(2)
  if not haveAction:
    print u'ERROR: you must specifiy an action for "gam <users> filter"'
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Creating filter for %s (%s of %s)" % (user+'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'CreateFilter', soft_errors=True,
              username=user, from_=from_, to=to, subject=subject, has_the_word=has_the_word, does_not_have_the_word=does_not_have_the_word,
              has_attachment=has_attachment, label=label, should_mark_as_read=should_mark_as_read, should_archive=should_archive,
              should_star=should_star, forward_to=forward_to, should_trash=should_trash, should_not_spam=should_not_spam)

def doForward(users):
  action = forward_to = None
  gotAction = gotForward = False
  if sys.argv[4].lower() in true_values:
    enable = True
  elif sys.argv[4].lower() in false_values:
    enable = False
  else:
    print u'ERROR: value for "gam <users> forward" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() in [u'keep', u'archive', u'delete']:
      action = sys.argv[i].upper()
      i += 1
      gotAction = True
    elif sys.argv[i].lower() == u'confirm':
      i += 1
    elif sys.argv[i].find(u'@') != -1:
      forward_to = sys.argv[i]
      gotForward = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> forward"' % sys.argv[i]
      sys.exit(2)
  if enable and (not gotAction or not gotForward):
    print u'ERROR: you must specify an action and a forwarding address for "gam <users> forward'
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Turning forward %s for %s, emails will be %s (%s of %s)" % (sys.argv[4], user+'@'+emailsettings.domain, action, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateForwarding', soft_errors=True, username=user, enable=enable, action=action, forward_to=forward_to)

def getForward(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    forward = callGData(service=emailsettings, function=u'GetForward', soft_errors=True, username=user)
    try:
      print u"User %s:  Forward To:%s  Enabled:%s  Action:%s" % (user+u'@'+emailsettings.domain, forward[u'forwardTo'], forward[u'enable'], forward[u'action'])
    except TypeError:
      pass

def doSignature(users):
  import cgi
  i = 4
  if sys.argv[i].lower() == u'file':
    filename = sys.argv[i+1]
    i += 2
    i, encoding = getCharSet(i)
    signature = readFile(filename, encoding=encoding).replace(u'\\n', u'&#xA;').replace(u'\n', u'<br/>')
  else:
    signature = cgi.escape(sys.argv[i]).replace(u'\\n', u'&#xA;').replace(u'"', u"'")
  xmlsig = u'''<?xml version="1.0" encoding="utf-8"?>
<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
    <apps:property name="signature" value="%s" />
</atom:entry>''' % signature
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Signature for %s (%s of %s)" % (user+u'@'+emailsettings.domain, i, count)
    uri = u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/%s/%s/signature' % (emailsettings.domain, user)
    i += 1
    callGData(service=emailsettings, function=u'Put', soft_errors=True, data=xmlsig, uri=uri)

def getSignature(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    signature = callGData(service=emailsettings, function=u'GetSignature', soft_errors=True, username=user)
    try:
      sys.stderr.write(u"User %s signature:\n  " % (user+u'@'+emailsettings.domain))
      print convertUTF8(u" %s" % signature[u'signature'])
    except TypeError:
      pass

def doWebClips(users):
  if sys.argv[4].lower() in true_values:
    enable = True
  elif sys.argv[4].lower() in false_values:
    enable = False
  else:
    print u'ERROR: value for "gam <users> webclips" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Turning Web Clips %s for %s (%s of %s)" % (sys.argv[4], user+u'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateWebClipSettings', soft_errors=True, username=user, enable=enable)

def doVacation(users):
  subject = message = u''
  if sys.argv[4].lower() in true_values:
    enable = True
  elif sys.argv[4].lower() in false_values:
    enable = False
  else:
    print u'ERROR: value for "gam <users> vacation" must be true or false, got %s' % sys.argv[4]
    sys.exit(2)
  contacts_only = domain_only = False
  start_date = end_date = None
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'subject':
      subject = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'message':
      message = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'contactsonly':
      contacts_only = True
      i += 1
    elif sys.argv[i].lower() == u'domainonly':
      domain_only = True
      i += 1
    elif sys.argv[i].lower() == u'startdate':
      start_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'enddate':
      end_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'file':
      filename = sys.argv[i+1]
      i += 2
      i, encoding = getCharSet(i)
      message = readFile(filename, encoding=encoding)
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> vacation"' % sys.argv[i]
      sys.exit(2)
  i = 1
  count = len(users)
  emailsettings = getEmailSettingsObject()
  message = message.replace(u'\\n', u'\n')
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN] #make sure it's back at default domain
    print u"Setting Vacation for %s (%s of %s)" % (user+'@'+emailsettings.domain, i, count)
    i += 1
    callGData(service=emailsettings, function=u'UpdateVacation',
              soft_errors=True,
              username=user, enable=enable, subject=subject, message=message,
              contacts_only=contacts_only, domain_only=domain_only, start_date=start_date, end_date=end_date)

def getVacation(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find(u'@') > 0:
      emailsettings.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    else:
      emailsettings.domain = GC_Values[GC_DOMAIN]
    vacationsettings = callGData(service=emailsettings, function=u'GetVacation', soft_errors=True, username=user)
    try:
      print convertUTF8(u'''User %s
 Enabled: %s
 Contacts Only: %s
 Domain Only: %s
 Subject: %s
 Message: %s
 Start Date: %s
 End Date: %s
''' % (user+u'@'+emailsettings.domain, vacationsettings[u'enable'], vacationsettings[u'contactsOnly'], vacationsettings[u'domainOnly'], vacationsettings[u'subject'],
       vacationsettings[u'message'], vacationsettings[u'startDate'], vacationsettings[u'endDate']))
    except TypeError:
      pass

def doDelSchema():
  cd = buildGAPIObject(u'directory')
  schemaKey = sys.argv[3]
  callGAPI(service=cd.schemas(), function=u'delete', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  print u'Deleted schema %s' % schemaKey

def doCreateOrUpdateUserSchema():
  cd = buildGAPIObject(u'directory')
  schemaName = sys.argv[3]
  body = {u'schemaName': schemaName, u'fields': []}
  i = 4
  while i < len(sys.argv):
    if sys.argv[i] in [u'field']:
      a_field = {u'fieldName': sys.argv[i+1]}
      i += 2
      while True:
        if sys.argv[i].lower() in [u'type']:
          a_field[u'fieldType'] = sys.argv[i+1].upper()
          if a_field[u'fieldType'] not in [u'BOOL', u'DOUBLE', u'EMAIL', u'INT64', u'PHONE', u'STRING']:
            print u'ERROR: type must be bool, double, email, int64, phone or string. Got %s' % a_field[u'fieldType']
            sys.exit(2)
          i += 2
        elif sys.argv[i].lower() in [u'multivalued']:
          a_field[u'multiValued'] = True
          i += 1
        elif sys.argv[i].lower() in [u'indexed']:
          a_field[u'indexed'] = True
          i += 1
        elif sys.argv[i].lower() in [u'restricted']:
          a_field[u'readAccessType'] = u'ADMINS_AND_SELF'
          i += 1
        elif sys.argv[i].lower() in [u'range']:
          a_field[u'numericIndexingSpec'] = {u'minValue': sys.argv[i+1], u'maxValue': sys.argv[i+2]}
          i += 3
        elif sys.argv[i].lower() in [u'endfield']:
          body[u'fields'].append(a_field)
          i += 1
          break
        else:
          print 'ERROR: %s is not a valid argument for "gam create schema"' % sys.argv[i]
          sys.exit(2)
    else:
      print 'ERROR: %s is not a valid argument for "gam create schema"' % sys.argv[i]
      sys.exit(2)
  if sys.argv[1].lower() == u'create':
    result = callGAPI(service=cd.schemas(), function=u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)
    print 'Created user schema %s' % result[u'schemaName']
  elif sys.argv[1].lower() == u'update':
    result = callGAPI(service=cd.schemas(), function=u'update', customerId=GC_Values[GC_CUSTOMER_ID], body=body, schemaKey=schemaName)
    print 'Updated user schema %s' % result[u'schemaName']

def doPrintUserSchemas():
  cd = buildGAPIObject(u'directory')
  schemas = callGAPI(service=cd.schemas(), function=u'list', customerId=GC_Values[GC_CUSTOMER_ID])
  if not schemas or u'schemas' not in schemas:
    return
  for schema in schemas[u'schemas']:
    print u'Schema: %s' % schema[u'schemaName']
    for a_key in schema:
      if a_key not in [u'schemaName', u'fields', u'etag', u'kind']:
        print '%s: %s' % (a_key, schema[a_key])
    print
    for field in schema[u'fields']:
      print u' Field: %s' % field[u'fieldName']
      for a_key in field:
        if a_key not in [u'fieldName', u'kind', u'etag']:
          print '  %s: %s' % (a_key, field[a_key])
      print
    print

def doGetUserSchema():
  cd = buildGAPIObject(u'directory')
  schemaKey = sys.argv[3]
  schema = callGAPI(service=cd.schemas(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], schemaKey=schemaKey)
  print u'Schema: %s' % schema[u'schemaName']
  for a_key in schema:
    if a_key not in [u'schemaName', u'fields', u'etag', u'kind']:
      print '%s: %s' % (a_key, schema[a_key])
  print
  for field in schema[u'fields']:
    print u' Field: %s' % field[u'fieldName']
    for a_key in field:
      if a_key not in [u'fieldName', u'kind', u'etag']:
        print '  %s: %s' % (a_key, field[a_key])
    print

def doCreateUser():
  cd = buildGAPIObject(u'directory')
  body = dict()
  body[u'name'] = dict()
  body[u'primaryEmail'] = sys.argv[3]
  if body[u'primaryEmail'].find(u'@') == -1:
    body[u'primaryEmail'] = u'%s@%s' % (body[u'primaryEmail'], GC_Values[GC_DOMAIN])
  gotFirstName = gotLastName = do_admin = False
  need_to_hash_password = need_password = True
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'firstname':
      body[u'name'][u'givenName'] = sys.argv[i+1]
      gotFirstName = True
      i += 2
    elif sys.argv[i].lower() == u'lastname':
      body[u'name'][u'familyName'] = sys.argv[i+1]
      gotLastName = True
      i += 2
    elif sys.argv[i].lower() == u'password':
      body[u'password'] = sys.argv[i+1]
      need_password = False
      i += 2
    elif sys.argv[i].lower() == u'suspended':
      if sys.argv[i+1].lower() in true_values:
        body[u'suspended'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'suspended'] = False
      else:
        print u'ERROR: suspended should be on or off, not %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'gal':
      if sys.argv[i+1].lower() in true_values:
        body[u'includeInGlobalAddressList'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'includeInGlobalAddressList'] = False
      else:
        print u'ERROR: gal should be on or off, not %s' % sys.argv[i+1]
        sys.exit(52)
      i += 2
    elif sys.argv[i].lower() in [u'sha', u'sha1', u'sha-1']:
      body[u'hashFunction'] = u'SHA-1'
      need_to_hash_password = False
      i += 1
    elif sys.argv[i].lower() == u'md5':
      body[u'hashFunction'] = u'MD5'
      need_to_hash_password = False
      i += 1
    elif sys.argv[i].lower() == u'crypt':
      body[u'hashFunction'] = u'crypt'
      need_to_hash_password = False
      i += 1
    elif sys.argv[i].lower() == u'nohash':
      need_to_hash_password = False
      i += 1
    elif sys.argv[i].lower() == u'changepassword':
      if sys.argv[i+1].lower() in true_values:
        body[u'changePasswordAtNextLogin'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'changePasswordAtNextLogin'] = False
      else:
        print u'ERROR: changepassword should be on or off, not %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'ipwhitelisted':
      if sys.argv[i+1].lower() in true_values:
        body[u'ipWhitelisted'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'ipWhitelisted'] = False
      else:
        print u'ERROR: ipwhitelisted should be on or off, not %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'admin':
      do_admin = True
      if sys.argv[i+1].lower() in true_values:
        admin_body = {u'status': True}
      elif sys.argv[i+1].lower() in false_values:
        admin_body = {u'status': False}
      else:
        print u'ERROR: admin should be on or off, not %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'agreedtoterms':
      if sys.argv[i+1].lower() in true_values:
        body[u'agreedToTerms'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'agreedToTerms'] = False
      else:
        print u'ERROR: agreedtoterms should be on or off, not %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() in [u'org', u'ou']:
      org = sys.argv[i+1]
      if org[0] != u'/':
        org = u'/%s' % org
      body[u'orgUnitPath'] = org
      i += 2
    elif sys.argv[i].lower() == u'im':
      im = dict()
      i += 1
      if sys.argv[i].lower() != u'type':
        print u'ERROR: wrong format for account im details. Expected type got %s' % sys.argv[i]
        sys.exit(2)
      i += 1
      im[u'type'] = sys.argv[i].lower()
      if im[u'type'] not in [u'custom', u'home', u'other', u'work']:
        print u'ERROR: type should be custom, home, other or work. Got %s' % im['type']
        sys.exit(2)
      if im[u'type'] == u'custom':
        i += 1
        im[u'customType'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() != u'protocol':
        print u'ERROR: wrong format for account details. Expected protocol got %s' % sys.argv[i]
        sys.exit(2)
      i += 1
      im[u'protocol'] = sys.argv[i].lower()
      if im[u'protocol'] not in [u'custom_protocol', u'aim', u'gtalk', u'icq', u'jabber', u'msn', u'net_meeting', u'qq', u'skype', u'yahoo']:
        print u'ERROR: protocol should be custom_protocol, aim, gtalk, icq, jabber, msn, net_meeting, qq, skype or yahoo. Got %s' % im[u'protocol']
        sys.exit(2)
      if im[u'protocol'] == u'custom_protocol':
        i += 1
        im[u'customProtocol'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() == u'primary':
        im[u'primary'] = True
        i += 1
      im[u'im'] = sys.argv[i]
      try:
        body[u'ims'].append(im)
      except KeyError:
        body[u'ims'] = [im,]
      i += 1
    elif sys.argv[i].lower() == u'address':
      address = dict()
      i += 1
      if sys.argv[i].lower() != u'type':
        print u'ERROR: wrong format for account address details. Expected type got %s' % sys.argv[i]
        sys.exit(2)
      i += 1
      address[u'type'] = sys.argv[i].lower()
      if address[u'type'] not in [u'custom', u'home', u'other', u'work']:
        print u'ERROR: wrong type should be custom, home, other or work. Got %s' % address[u'type']
        sys.exit(2)
      if address[u'type'] == u'custom':
        i += 1
        address[u'customType'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() == u'unstructured':
        i += 1
        address[u'sourceIsStructured'] = False
        address[u'formatted'] = sys.argv[i]
        i += 1
      while True:
        argument = sys.argv[i].lower()
        if argument == u'pobox':
          address[u'poBox'] = sys.argv[i+1]
          i += 2
        elif argument == u'extendedaddress':
          address[u'extendedAddress'] = sys.argv[i+1]
          i += 2
        elif argument == u'streetaddress':
          address[u'streetAddress'] = sys.argv[i+1]
          i += 2
        elif argument == u'locality':
          address[u'locality'] = sys.argv[i+1]
          i += 2
        elif argument == u'region':
          address[u'region'] = sys.argv[i+1]
          i += 2
        elif argument == u'postalcode':
          address[u'postalCode'] = sys.argv[i+1]
          i += 2
        elif argument == u'country':
          address[u'country'] = sys.argv[i+1]
          i += 2
        elif argument == u'countrycode':
          address[u'countryCode'] = sys.argv[i+1]
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          address[u'primary'] = True
          i += 1
          break
        else:
          print u'ERROR: invalid argument (%s) for account address details' % sys.argv[i]
          sys.exit(2)
      try:
        body[u'addresses'].append(address)
      except KeyError:
        body[u'addresses'] = [address,]
    elif sys.argv[i].lower() == u'organization':
      organization = dict()
      i += 1
      while True:
        argument = sys.argv[i].lower()
        if argument == u'name':
          organization[u'name'] = sys.argv[i+1]
          i += 2
        elif argument == u'title':
          organization[u'title'] = sys.argv[i+1]
          i += 2
        elif argument == u'customtype':
          organization[u'customType'] = sys.argv[i+1]
          i += 2
        elif argument == u'type':
          organization[u'type'] = sys.argv[i+1].lower()
          if organization[u'type'] not in [u'domain_only', u'school', u'unknown', u'work']:
            print u'ERROR: organization type must be domain_only, school, unknown or work. Got %s' % organization[u'type']
            sys.exit(2)
          i += 2
        elif argument == u'department':
          organization[u'department'] = sys.argv[i+1]
          i += 2
        elif argument == u'symbol':
          organization[u'symbol'] = sys.argv[i+1]
          i += 2
        elif argument == u'costcenter':
          organization[u'costCenter'] = sys.argv[i+1]
          i += 2
        elif argument == u'location':
          organization[u'location'] = sys.argv[i+1]
          i += 2
        elif argument == u'description':
          organization[u'description'] = sys.argv[i+1]
          i += 2
        elif argument == u'domain':
          organization[u'domain'] = sys.argv[i+1]
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          organization[u'primary'] = True
          i += 1
          break
        else:
          print u'ERROR: invalid argument (%s) for account organization details' % sys.argv[i]
          sys.exit(2)
      try:
        body[u'organizations'].append(organization)
      except KeyError:
        body[u'organizations'] = [organization,]
    elif sys.argv[i].lower() == u'phone':
      phone = dict()
      i += 1
      while True:
        argument = sys.argv[i].lower()
        if argument == u'value':
          phone[u'value'] = sys.argv[i+1]
          i += 2
        elif argument == u'type':
          phone[u'type'] = sys.argv[i+1].lower()
          if phone[u'type'] not in [u'assistant', u'callback', u'car', u'company_main', u'custom', u'grand_central', u'home', u'home_fax', u'isdn', u'main', u'mobile', u'other', u'other_fax', u'pager', u'radio', u'telex', u'tty_tdd', u'work', u'work_fax', u'work_mobile', u'work_pager']:
            print u'ERROR: phone type must be assistant, callback, car, company_main, custom, grand_central, home, home_fax, isdn, main, mobile, other, other_fax, pager, radio, telex, tty_tdd, work, work_fax, work_mobile, work_pager. Got %s' % phone[u'type']
            sys.exit(2)
          i += 2
          if phone[u'type'] == u'custom':
            phone[u'customType'] = sys.argv[i]
            i += 1
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          phone[u'primary'] = True
          i += 1
          break
        else:
          print u'ERROR: invalid argument (%s) for account phone details' % sys.argv[i]
          sys.exit(2)
      try:
        body[u'phones'].append(phone)
      except KeyError:
        body[u'phones'] = [phone,]
    elif sys.argv[i].lower() == u'relation':
      relation = dict()
      i += 1
      relation[u'type'] = sys.argv[i]
      if relation[u'type'].lower() not in [u'mother', u'father', u'sister', u'brother', u'manager', u'assistant', u'partner']:
        relation[u'type'] = u'custom'
        relation[u'customType'] = sys.argv[i]
      i += 1
      relation[u'value'] = sys.argv[i]
      try:
        body[u'relations'].append(relation)
      except KeyError:
        body[u'relations'] = [relation,]
      i += 1
    elif sys.argv[i].lower() == u'externalid':
      externalid = dict()
      i += 1
      externalid[u'type'] = sys.argv[i]
      if externalid[u'type'].lower() not in [u'account', u'customer', u'network', u'organization']:
        externalid[u'type'] = u'custom'
        externalid[u'customType'] = sys.argv[i]
      i += 1
      externalid[u'value'] = sys.argv[i]
      try:
        body[u'externalIds'].append(externalid)
      except KeyError:
        body[u'externalIds'] = [externalid,]
      i += 1
    else:
      if u'customSchemas' not in body:
        body[u'customSchemas'] = {}
      try:
        (schemaName, fieldName) = sys.argv[i].split(u'.')
      except ValueError:
        print 'ERROR: %s is not a valid create user argument or custom schema name.' % sys.argv[i]
        sys.exit(2)
      field_value = sys.argv[i+1]
      is_multivalue = False
      if field_value.lower() in [u'multivalue', u'multivalued', u'value']:
        is_multivalue = True
        field_value = sys.argv[i+2]
      if schemaName not in body[u'customSchemas']:
        body[u'customSchemas'][schemaName] = {}
      if is_multivalue:
        if fieldName not in body[u'customSchemas'][schemaName]:
          body[u'customSchemas'][schemaName][fieldName] = []
        body[u'customSchemas'][schemaName][fieldName].append({u'value': field_value})
      else:
        body[u'customSchemas'][schemaName][fieldName] = field_value
      i += 2
      if is_multivalue:
        i += 1
  if not gotFirstName:
    body[u'name'][u'givenName'] = u'Unknown'
  if not gotLastName:
    body[u'name'][u'familyName'] = u'Unknown'
  if need_password:
    body[u'password'] = u''.join(random.sample(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 25))
  if need_to_hash_password:
    body[u'password'] = gen_sha512_hash(body[u'password'])
    body[u'hashFunction'] = u'crypt'
  print u"Creating account for %s" % body[u'primaryEmail']
  callGAPI(service=cd.users(), function='insert', body=body, fields=u'primaryEmail')
  if do_admin:
    print u' Changing admin status for %s to %s' % (body[u'primaryEmail'], admin_body[u'status'])
    callGAPI(service=cd.users(), function=u'makeAdmin', userKey=body[u'primaryEmail'], body=admin_body)

def doCreateGroup():
  cd = buildGAPIObject(u'directory')
  use_gs_api = False
  body = dict()
  body[u'email'] = sys.argv[3]
  if body[u'email'].find(u'@') == -1:
    body[u'email'] = u'%s@%s' % (body[u'email'], GC_Values[GC_DOMAIN])
  got_name = False
  i = 4
  gs_body = dict()
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'name'] = sys.argv[i+1]
      got_name = True
      i += 2
    elif sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    else:
      value = sys.argv[i+1]
      gs_object = buildDiscoveryObject(u'groupssettings')
      matches_gs_setting = False
      for (attrib, params) in gs_object[u'schemas'][u'Groups'][u'properties'].items():
        if attrib in [u'kind', u'etag', u'email', u'name', u'description']:
          continue
        if sys.argv[i].lower().replace(u'_', u'') == attrib.lower():
          matches_gs_setting = True
          if params[u'type'] == u'integer':
            try:
              if value[-1:].upper() == u'M':
                value = int(value[:-1]) * 1024 * 1024
              elif value[-1:].upper() == u'K':
                value = int(value[:-1]) * 1024
              elif value[-1].upper() == u'B':
                value = int(value[:-1])
              else:
                value = int(value)
            except ValueError:
              print u'ERROR: %s must be a number ending with M (megabytes), K (kilobytes) or nothing (bytes). Got %s' % value
              sys.exit(2)
          elif params[u'type'] == u'string':
            if params[u'description'].find(value.upper()) != -1: # ugly hack because API wants some values uppercased.
              value = value.upper()
            elif value.lower() in true_values:
              value = u'true'
            elif value.lower() in false_values:
              value = u'false'
          break
      if not matches_gs_setting:
        print u'ERROR: %s is not a valid argument for "gam create group"' % sys.argv[i]
        sys.exit(2)
      gs_body[attrib] = value
      use_gs_api = True
      i += 2
  if not got_name:
    body[u'name'] = body[u'email']
  print u"Creating group %s" % body[u'email']
  callGAPI(service=cd.groups(), function=u'insert', body=body, fields=u'email')
  if use_gs_api:
    gs = buildGAPIObject(u'groupssettings')
    callGAPI(service=gs.groups(), function=u'patch', retry_reasons=[u'serviceLimit'], groupUniqueId=body[u'email'], body=gs_body)

def doCreateAlias():
  cd = buildGAPIObject(u'directory')
  body = dict()
  body[u'alias'] = sys.argv[3]
  if body[u'alias'].find(u'@') == -1:
    body[u'alias'] = u'%s@%s' % (body[u'alias'], GC_Values[GC_DOMAIN])
  target_type = sys.argv[4].lower()
  if target_type not in [u'user', u'group', u'target']:
    print u'ERROR: type of target should be user or group. Got %s' % target_type
    sys.exit(2)
  targetKey = sys.argv[5]
  if targetKey.find(u'@') == -1:
    targetKey = u'%s@%s' % (targetKey, GC_Values[GC_DOMAIN])
  print u'Creating alias %s for %s %s' % (body[u'alias'], target_type, targetKey)
  if target_type == u'user':
    callGAPI(service=cd.users().aliases(), function=u'insert', userKey=targetKey, body=body)
  elif target_type == u'group':
    callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=targetKey, body=body)
  elif target_type == u'target':
    try:
      callGAPI(service=cd.users().aliases(), function=u'insert', throw_reasons=[u'invalid'], userKey=targetKey, body=body)
    except googleapiclient.errors.HttpError:
      callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=targetKey, body=body)

def doCreateOrg():
  cd = buildGAPIObject(u'directory')
  body = dict()
  body[u'name'] = sys.argv[3]
  if body[u'name'][0] == u'/':
    body[u'name'] = body[u'name'][1:]
  i = 4
  body[u'parentOrgUnitPath'] = u'/'
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'description':
      body[u'description'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'parent':
      body[u'parentOrgUnitPath'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'noinherit':
      body[u'blockInheritance'] = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam create org"' % sys.argv[i]
      sys.exit(2)
  callGAPI(service=cd.orgunits(), function=u'insert', customerId=GC_Values[GC_CUSTOMER_ID], body=body)

def doCreateResourceCalendar():
  cd = buildGAPIObject(u'directory')
  body = {u'resourceId': sys.argv[3],
          u'resourceName': sys.argv[4]}
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'description':
      body[u'resourceDescription'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'type':
      body[u'resourceType'] = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam create resource"' % sys.argv[i]
      sys.exit(2)
  print u'Creating resource %s...' % body[u'resourceId']
  callGAPI(service=cd.resources().calendars(), function=u'insert',
           customer=GC_Values[GC_CUSTOMER_ID], body=body)

def doUpdateUser(users):
  cd = buildGAPIObject(u'directory')
  body = dict()
  gotPassword = isMD5 = isSHA1 = isCrypt = False
  is_admin = nohash = None
  if sys.argv[1].lower() == u'update':
    i = 4
  else:
    i = 5
  do_update_user = False
  do_admin_user = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'firstname':
      do_update_user = True
      if u'name' not in body:
        body[u'name'] = dict()
      body[u'name'][u'givenName'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'lastname':
      do_update_user = True
      if u'name' not in body:
        body[u'name'] = dict()
      body[u'name'][u'familyName'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'username', u'email']:
      do_update_user = True
      body[u'primaryEmail'] = sys.argv[i+1]
      if body[u'primaryEmail'].find(u'@') == -1:
        body[u'primaryEmail'] = u'%s@%s' % (body[u'primaryEmail'], GC_Values[GC_DOMAIN])
      i += 2
    elif sys.argv[i].lower() == u'password':
      do_update_user = True
      body[u'password'] = sys.argv[i+1]
      if body[u'password'].lower() == u'random':
        body[u'password'] = ''.join(random.sample(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 50))
      i += 2
      gotPassword = True
    elif sys.argv[i].lower() == u'admin':
      do_admin_user = True
      if sys.argv[i+1].lower() in true_values:
        is_admin = True
      elif sys.argv[i+1].lower() in false_values:
        is_admin = False
      i += 2
    elif sys.argv[i].lower() == u'suspended':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'suspended'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'suspended'] = False
      i += 2
    elif sys.argv[i].lower() == u'gal':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'includeInGlobalAddressList'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'includeInGlobalAddressList'] = False
      else:
        print u'ERROR: gal should be on or off, not %s' % sys.argv[i+1]
        sys.exit(2)
      i += 2
    elif sys.argv[i].lower() == u'ipwhitelisted':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'ipWhitelisted'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'ipWhitelisted'] = False
      i += 2
    elif sys.argv[i].lower() in [u'sha', u'sha1', u'sha-1']:
      do_update_user = True
      body[u'hashFunction'] = u'SHA-1'
      i += 1
      isSHA1 = True
    elif sys.argv[i].lower() == u'md5':
      do_update_user = True
      body[u'hashFunction'] = u'MD5'
      i += 1
      isMD5 = True
    elif sys.argv[i].lower() == u'crypt':
      do_update_user = True
      body[u'hashFunction'] = u'crypt'
      i += 1
      isCrypt = True
    elif sys.argv[i].lower() == u'nohash':
      nohash = True
      i += 1
    elif sys.argv[i].lower() == u'changepassword':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'changePasswordAtNextLogin'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'changePasswordAtNextLogin'] = False
      i += 2
    elif sys.argv[i].lower() in ['org', u'ou']:
      do_update_user = True
      body[u'orgUnitPath'] = sys.argv[i+1]
      if body[u'orgUnitPath'][0] != u'/':
        body[u'orgUnitPath'] = u'/'+body[u'orgUnitPath']
      i += 2
    elif sys.argv[i].lower() == u'agreedtoterms':
      do_update_user = True
      if sys.argv[i+1].lower() in true_values:
        body[u'agreedToTerms'] = True
      elif sys.argv[i+1].lower() in false_values:
        body[u'agreedToTerms'] = False
      i += 2
    elif sys.argv[i].lower() == u'customerid':
      do_update_user = True
      body[u'customerId'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'im':
      do_update_user = True
      im = dict()
      i += 1
      if sys.argv[i].lower() != u'type':
        print u'ERROR: wrong format for account im details. Expected type got %s' % sys.argv[i]
        sys.exit(2)
      i += 1
      im[u'type'] = sys.argv[i].lower()
      if im[u'type'] not in [u'custom', u'home', u'other', u'work']:
        print u'ERROR: type should be custom, home, other or work. Got %s' % im[u'type']
        sys.exit(2)
      if im[u'type'] == u'custom':
        i += 1
        im[u'customType'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() != u'protocol':
        print u'ERROR: wrong format for account details. Expected protocol got %s' % sys.argv[i]
        sys.exit(2)
      i += 1
      im[u'protocol'] = sys.argv[i].lower()
      if im[u'protocol'] not in [u'custom_protocol', u'aim', u'gtalk', u'icq', u'jabber', u'msn', u'net_meeting', u'qq', u'skype', u'yahoo']:
        print u'ERROR: protocol should be custom_protocol, aim, gtalk, icq, jabber, msn, net_meeting, qq, skype or yahoo. Got %s' % im[u'protocol']
        sys.exit(2)
      if im[u'protocol'] == u'custom_protocol':
        i += 1
        im[u'customProtocol'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() == u'primary':
        im[u'primary'] = True
        i += 1
      im[u'im'] = sys.argv[i]
      i += 1
      try:
        body[u'ims'].append(im)
      except KeyError:
        body[u'ims'] = [im,]
    elif sys.argv[i].lower() == u'address':
      do_update_user = True
      address = dict()
      i += 1
      if sys.argv[i].lower() != u'type':
        print u'ERROR: wrong format for account address details. Expected type got %s' % sys.argv[i]
        sys.exit(2)
      i += 1
      address[u'type'] = sys.argv[i].lower()
      if address[u'type'] not in [u'custom', u'home', u'other', u'work']:
        print u'ERROR: wrong type should be custom, home, other or work. Got %s' % address[u'type']
        sys.exit(2)
      if address[u'type'] == u'custom':
        i += 1
        address[u'customType'] = sys.argv[i]
      i += 1
      if sys.argv[i].lower() == u'unstructured':
        i += 1
        address[u'sourceIsStructured'] = False
        address[u'formatted'] = sys.argv[i]
        i += 1
      while True:
        argument = sys.argv[i].lower()
        if argument == u'pobox':
          address[u'poBox'] = sys.argv[i+1]
          i += 2
        elif argument == u'extendedaddress':
          address[u'extendedAddress'] = sys.argv[i+1]
          i += 2
        elif argument == u'streetaddress':
          address[u'streetAddress'] = sys.argv[i+1]
          i += 2
        elif argument == u'locality':
          address[u'locality'] = sys.argv[i+1]
          i += 2
        elif argument == u'region':
          address[u'region'] = sys.argv[i+1]
          i += 2
        elif argument == u'postalcode':
          address[u'postalCode'] = sys.argv[i+1]
          i += 2
        elif argument == u'country':
          address[u'country'] = sys.argv[i+1]
          i += 2
        elif argument == u'countrycode':
          address[u'countryCode'] = sys.argv[i+1]
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          address[u'primary'] = True
          i += 1
          break
        else:
          print u'ERROR: invalid argument (%s) for account address details' % sys.argv[i]
          sys.exit(2)
      try:
        body[u'addresses'].append(address)
      except KeyError:
        body[u'addresses'] = [address,]
    elif sys.argv[i].lower() == u'organization':
      do_update_user = True
      organization = dict()
      i += 1
      while True:
        argument = sys.argv[i].lower()
        if argument == u'name':
          organization[u'name'] = sys.argv[i+1]
          i += 2
        elif argument == u'title':
          organization[u'title'] = sys.argv[i+1]
          i += 2
        elif argument == u'customtype':
          organization[u'customType'] = sys.argv[i+1]
          i += 2
        elif argument == u'type':
          organization[u'type'] = sys.argv[i+1].lower()
          if organization[u'type'] not in [u'domain_only', u'school', u'unknown', u'work']:
            print u'ERROR: organization type must be domain_only, school, unknown or work. Got %s' % organization[u'type']
            sys.exit(2)
          i += 2
        elif argument == u'department':
          organization[u'department'] = sys.argv[i+1]
          i += 2
        elif argument == u'symbol':
          organization[u'symbol'] = sys.argv[i+1]
          i += 2
        elif argument == u'costcenter':
          organization[u'costCenter'] = sys.argv[i+1]
          i += 2
        elif argument == u'location':
          organization[u'location'] = sys.argv[i+1]
          i += 2
        elif argument == u'description':
          organization[u'description'] = sys.argv[i+1]
          i += 2
        elif argument == u'domain':
          organization[u'domain'] = sys.argv[i+1]
          i += 2
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          organization[u'primary'] = True
          i += 1
          break
        else:
          print u'ERROR: invalid argument (%s) for account organization details' % sys.argv[i]
          sys.exit(2)
      try:
        body[u'organizations'].append(organization)
      except KeyError:
        body[u'organizations'] = [organization,]
    elif sys.argv[i].lower() == u'phone':
      do_update_user = True
      phone = dict()
      i += 1
      while True:
        argument = sys.argv[i].lower()
        if argument == u'value':
          phone[u'value'] = sys.argv[i+1]
          i += 2
        elif argument == u'type':
          phone[u'type'] = sys.argv[i+1].lower()
          if phone[u'type'] not in [u'assistant', u'callback', u'car', u'company_main', u'custom', u'grand_central', u'home', u'home_fax', u'isdn', u'main', u'mobile', u'other', u'other_fax', u'pager', u'radio', u'telex', u'tty_tdd', u'work', u'work_fax', u'work_mobile', u'work_pager']:
            print u'ERROR: phone type must be assistant, callback, car, company_main, custom, grand_central, home, home_fax, isdn, main, mobile, other, other_fax, pager, radio, telex, tty_tdd, work, work_fax, work_mobile, work_pager. Got %s' % phone[u'type']
            sys.exit(2)
          i += 2
          if phone[u'type'] == u'custom':
            phone[u'customType'] = sys.argv[i]
            i += 1
        elif argument == u'notprimary':
          i += 1
          break
        elif argument == u'primary':
          phone[u'primary'] = True
          i += 1
          break
        else:
          print u'ERROR: invalid argument (%s) for account phone details' % sys.argv[i]
          sys.exit(2)
      try:
        body[u'phones'].append(phone)
      except KeyError:
        body[u'phones'] = [phone,]
    elif sys.argv[i].lower() == u'relation':
      do_update_user = True
      relation = dict()
      i += 1
      relation[u'type'] = sys.argv[i]
      if relation[u'type'].lower() not in [u'mother', u'father', u'sister', u'brother', u'manager', u'assistant', u'partner']:
        relation[u'type'] = u'custom'
        relation[u'customType'] = sys.argv[i]
      i += 1
      relation[u'value'] = sys.argv[i]
      try:
        body[u'relations'].append(relation)
      except KeyError:
        body[u'relations'] = [relation,]
      i += 1
    elif sys.argv[i].lower() == u'otheremail':
      do_update_user = True
      an_email = dict()
      i += 1
      an_email[u'type'] = sys.argv[i]
      if an_email[u'type'].lower() not in [u'custom', u'home', u'other', u'work']:
        an_email[u'type'] = u'custom'
        an_email[u'customType'] = sys.argv[i]
      i += 1
      an_email[u'address'] = sys.argv[i]
      if u'emails' not in body:
        body[u'emails'] = list()
      body[u'emails'].append(an_email)
      i += 1
    elif sys.argv[i].lower() == u'externalid':
      do_update_user = True
      externalid = dict()
      i += 1
      externalid[u'type'] = sys.argv[i]
      if externalid[u'type'].lower() not in [u'account', u'customer', u'network', u'organization']:
        externalid[u'type'] = u'custom'
        externalid[u'customType'] = sys.argv[i]
      i += 1
      externalid[u'value'] = sys.argv[i]
      try:
        body[u'externalIds'].append(externalid)
      except KeyError:
        body[u'externalIds'] = [externalid,]
      i += 1
#    else:
#      showUsage()
#      print u''
#      print u'ERROR: didn\'t expect %s command at position %s' % (sys.argv[i], i)
#      sys.exit(2)
    else:
      do_update_user = True
      if u'customSchemas' not in body:
        body[u'customSchemas'] = {}
      try:
        (schemaName, fieldName) = sys.argv[i].split(u'.')
      except ValueError:
        print u'ERROR: %s is not a valid user update argument or custom schema name' % sys.argv[i]
        sys.exit(2)
      field_value = sys.argv[i+1]
      is_multivalue = False
      if field_value.lower() in [u'multivalue', u'multivalued', u'value']:
        is_multivalue = True
        field_value = sys.argv[i+2]
      if schemaName not in body[u'customSchemas']:
        body[u'customSchemas'][schemaName] = {}
      if is_multivalue:
        if fieldName not in body[u'customSchemas'][schemaName]:
          body[u'customSchemas'][schemaName][fieldName] = []
        body[u'customSchemas'][schemaName][fieldName].append({u'value': field_value})
      else:
        body[u'customSchemas'][schemaName][fieldName] = field_value
      i += 2
      if is_multivalue:
        i += 1
  if gotPassword and not (isSHA1 or isMD5 or isCrypt or nohash):
    body[u'password'] = gen_sha512_hash(body[u'password'])
    body[u'hashFunction'] = u'crypt'
  for user in users:
    if user[:4].lower() == u'uid:':
      user = user[4:]
    elif user.find(u'@') == -1:
      user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
    if u'primaryEmail' in body and body[u'primaryEmail'][:4].lower() == u'vfe@':
      user_primary = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'primaryEmail,id')
      user = user_primary[u'id']
      user_primary = user_primary[u'primaryEmail']
      user_name = user_primary[:user_primary.find(u'@')]
      user_domain = user_primary[user_primary.find(u'@')+1:]
      body[u'primaryEmail'] = u'vfe.%s.%05d@%s' % (user_name, random.randint(1, 99999), user_domain)
      body[u'emails'] = [{u'type': u'custom', u'customType': u'former_employee', u'primary': False, u'address': user_primary}]
    sys.stdout.write(u'updating user %s...\n' % user)
    if do_update_user:
      callGAPI(service=cd.users(), function=u'patch', userKey=user, body=body)
    if do_admin_user:
      callGAPI(service=cd.users(), function=u'makeAdmin', userKey=user, body={u'status': is_admin})

def doRemoveUsersAliases(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user_aliases = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'aliases,id,primaryEmail')
    user_id = user_aliases[u'id']
    user_primary = user_aliases[u'primaryEmail']
    if u'aliases' in user_aliases:
      print u'%s has %s aliases' % (user_primary, len(user_aliases[u'aliases']))
      for an_alias in user_aliases[u'aliases']:
        print u' removing alias %s for %s...' % (an_alias, user_primary)
        callGAPI(service=cd.users().aliases(), function=u'delete', userKey=user_id, alias=an_alias)
    else:
      print u'%s has no aliases' % user_primary

def doRemoveUsersGroups(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    user_groups = callGAPIpages(service=cd.groups(), items=u'groups', function=u'list', userKey=user, fields=u'groups(id,email)')
    num_groups = len(user_groups)
    print u'%s is in %s groups' % (user, num_groups)
    i = 1
    for user_group in user_groups:
      print u' removing %s from %s (%s/%s)' % (user, user_group[u'email'], i, num_groups)
      callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=user_group[u'id'], memberKey=user)
      i += 1
    print u''

def doUpdateGroup():
  cd = buildGAPIObject(u'directory')
  group = sys.argv[3]
  if sys.argv[4].lower() in [u'add', u'update', u'sync', u'remove']:
    if group[0:3].lower() == u'uid:':
      group = group[4:]
    elif group.find(u'@') == -1:
      group = u'%s@%s' % (group, GC_Values[GC_DOMAIN])
    if sys.argv[4].lower() in [u'add', u'update']:
      role = sys.argv[5].upper()
      i = 6
      if role not in [u'OWNER', u'MANAGER', u'MEMBER']:
        role = u'MEMBER'
        i = 5
      if sys.argv[i].lower() in usergroup_types:
        users_email = getUsersToModify(entity_type=sys.argv[i], entity=sys.argv[i+1])
      else:
        users_email = [sys.argv[i],]
      for user_email in users_email:
        if user_email != u'*' and user_email.find(u'@') == -1:
          user_email = u'%s@%s' % (user_email, GC_Values[GC_DOMAIN])
        sys.stderr.write(u' %sing %s %s...\n' % (sys.argv[4].lower(), role.lower(), user_email))
        try:
          if sys.argv[4].lower() == u'add':
            body = {u'role': role}
            body[u'email'] = user_email
            callGAPI(service=cd.members(), function=u'insert', soft_errors=True, groupKey=group, body=body)
          elif sys.argv[4].lower() == u'update':
            callGAPI(service=cd.members(), function=u'update', soft_errors=True, groupKey=group, memberKey=user_email, body={u'email': user_email, u'role': role})
        except googleapiclient.errors.HttpError:
          pass
    elif sys.argv[4].lower() == u'sync':
      role = sys.argv[5].upper()
      i = 6
      if role not in [u'OWNER', u'MANAGER', u'MEMBER']:
        role = u'MEMBER'
        i = 5
      users_email = getUsersToModify(entity_type=sys.argv[i], entity=sys.argv[i+1])
      users_email = [x.lower() for x in users_email]
      current_emails = getUsersToModify(entity_type=u'group', entity=group, member_type=role)
      current_emails = [x.lower() for x in current_emails]
      to_add = list(set(users_email) - set(current_emails))
      to_remove = list(set(current_emails) - set(users_email))
      sys.stderr.write(u'Need to add %s %s and remove %s.\n' % (len(to_add), role, len(to_remove)))
      items = []
      for user_email in to_add:
        items.append([u'update', u'group', group, u'add', role, user_email])
      for user_email in to_remove:
        items.append([u'update', u'group', group, u'remove', user_email])
      run_batch(items)
    elif sys.argv[4].lower() == u'remove':
      i = 5
      if sys.argv[i].lower() in [u'member', u'manager', u'owner']:
        i += 1
      if sys.argv[i].lower() in usergroup_types:
        user_emails = getUsersToModify(entity_type=sys.argv[i], entity=sys.argv[i+1])
      else:
        user_emails = [sys.argv[i],]
      for user_email in user_emails:
        if user_email != u'*' and user_email.find(u'@') == -1:
          user_email = u'%s@%s' % (user_email, GC_Values[GC_DOMAIN])
        sys.stderr.write(u' removing %s\n' % user_email)
        callGAPI(service=cd.members(), function=u'delete', soft_errors=True, groupKey=group, memberKey=user_email)
  else:
    i = 4
    use_cd_api = False
    use_gs_api = False
    gs_body = dict()
    cd_body = dict()
    while i < len(sys.argv):
      if sys.argv[i].lower() == u'email':
        use_cd_api = True
        cd_body[u'email'] = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'admincreated':
        use_cd_api = True
        cd_body[u'adminCreated'] = sys.argv[i+1].lower()
        if cd_body[u'adminCreated'] not in [u'true', u'false']:
          print u'ERROR: Value for admincreated must be true or false. Got %s' % cd_body[u'adminCreated']
          sys.exit(2)
        i += 2
      else:
        value = sys.argv[i+1]
        gs_object = buildDiscoveryObject(u'groupssettings')
        matches_gs_setting = False
        for (attrib, params) in gs_object[u'schemas'][u'Groups'][u'properties'].items():
          if attrib in [u'kind', u'etag', u'email']:
            continue
          if sys.argv[i].lower().replace(u'_', u'') == attrib.lower():
            matches_gs_setting = True
            if params[u'type'] == u'integer':
              try:
                if value[-1:].upper() == u'M':
                  value = int(value[:-1]) * 1024 * 1024
                elif value[-1:].upper() == u'K':
                  value = int(value[:-1]) * 1024
                elif value[-1].upper() == u'B':
                  value = int(value[:-1])
                else:
                  value = int(value)
              except ValueError:
                print u'ERROR: %s must be a number ending with M (megabytes), K (kilobytes) or nothing (bytes). Got %s' % value
                sys.exit(2)
            elif params[u'type'] == u'string':
              if params[u'description'].find(value.upper()) != -1: # ugly hack because API wants some values uppercased.
                value = value.upper()
              elif value.lower() in true_values:
                value = u'true'
              elif value.lower() in false_values:
                value = u'false'
            break
        if not matches_gs_setting:
          print u'ERROR: %s is not a valid argument for "gam update group"' % sys.argv[i]
          sys.exit(2)
        gs_body[attrib] = value
        use_gs_api = True
        i += 2
    if group[:4].lower() == u'uid:': # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
      use_cd_api = True
      group = group[4:]
    elif group.find(u'@') == -1:
      group = u'%s@%s' % (group, GC_Values[GC_DOMAIN])
    if use_cd_api:
      try:
        if cd_body[u'email'].find('@') == -1:
          cd_body[u'email'] = u'%s@%s' % (cd_body[u'email'], GC_Values[GC_DOMAIN])
      except KeyError:
        pass
      cd_result = callGAPI(service=cd.groups(), function=u'patch', groupKey=group, body=cd_body)
    if use_gs_api:
      gs = buildGAPIObject(u'groupssettings')
      if use_cd_api:
        group = cd_result[u'email']
      callGAPI(service=gs.groups(), function=u'patch', retry_reasons=[u'serviceLimit'], groupUniqueId=group, body=gs_body)
    print u'updated group %s' % group

def doUpdateAlias():
  cd = buildGAPIObject(u'directory')
  alias = sys.argv[3]
  target_type = sys.argv[4].lower()
  if target_type not in [u'user', u'group', u'target']:
    print u'ERROR: target type should be "user", "group" or "target", got %s' % target_type
    sys.exit(2)
  target_email = sys.argv[5]
  if alias.find(u'@') == -1:
    alias = u'%s@%s' % (alias, GC_Values[GC_DOMAIN])
  if target_email.find(u'@') == -1:
    target_email = u'%s@%s' % (target_email, GC_Values[GC_DOMAIN])
  try:
    callGAPI(service=cd.users().aliases(), function=u'delete', throw_reasons=[u'invalid'], userKey=alias, alias=alias)
  except googleapiclient.errors.HttpError:
    callGAPI(service=cd.groups().aliases(), function=u'delete', groupKey=alias, alias=alias)
  if target_type == u'user':
    callGAPI(service=cd.users().aliases(), function=u'insert', userKey=target_email, body={u'alias': alias})
  elif target_type == u'group':
    callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=target_email, body={u'alias': alias})
  elif target_type == u'target':
    try:
      callGAPI(service=cd.users().aliases(), function=u'insert', throw_reasons=[u'invalid'], userKey=target_email, body={u'alias': alias})
    except googleapiclient.errors.HttpError:
      callGAPI(service=cd.groups().aliases(), function=u'insert', groupKey=target_email, body={u'alias': alias})
  print u'updated alias %s' % alias

def doUpdateResourceCalendar():
  cd = buildGAPIObject(u'directory')
  resId = sys.argv[3]
  body = {}
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'name':
      body[u'resourceName'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'description':
      body[u'resourceDescription'] = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'type':
      body[u'resourceType'] = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam update resource"' % sys.argv[i]
      sys.exit(2)
  # Use patch since it seems to work better.
  # update requires name to be set.
  callGAPI(service=cd.resources().calendars(), function=u'patch',
           customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId, body=body,
           fields=u'')
  print u'updated resource %s' % resId

def doUpdateCros():
  cd = buildGAPIObject(u'directory')
  deviceId = sys.argv[3]
  if deviceId[:6].lower() == u'query:':
    query = deviceId[6:]
    devices_result = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices',
                                   query=query, customerId=GC_Values[GC_CUSTOMER_ID], fields=u'chromeosdevices/deviceId,nextPageToken')
    devices = list()
    for a_device in devices_result:
      devices.append(a_device[u'deviceId'])
  else:
    devices = [deviceId,]
  i = 4
  body = dict()
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'user':
      body[u'annotatedUser'] = sys.argv[i + 1]
      i += 2
    elif sys.argv[i].lower() == u'location':
      body[u'annotatedLocation'] = sys.argv[i + 1]
      i += 2
    elif sys.argv[i].lower() == u'notes':
      body[u'notes'] = sys.argv[i + 1]
      i += 2
    elif sys.argv[i].lower() == u'status':
      body[u'status'] = sys.argv[i + 1].upper()
      #if body['status'] not in ['ACTIVE', 'DEPROVISIONED']:
      #  print 'ERROR: status must be active or deprovisioned, got %s' % body['status']
      #  sys.exit(2)
      i += 2
    elif sys.argv[i].lower() in [u'tag', u'asset', u'assetid']:
      body[u'annotatedAssetId'] = sys.argv[i + 1]
      #annotatedAssetId - Handle Asset Tag Field 2015-04-13
      i += 2
    elif sys.argv[i].lower() in [u'ou', u'org']:
      body[u'orgUnitPath'] = sys.argv[i + 1]
      if body[u'orgUnitPath'][0] != u'/':
        body[u'orgUnitPath'] = u'/%s' % body[u'orgUnitPath']
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam update cros"' % sys.argv[i]
      sys.exit(2)
  device_count = len(devices)
  i = 1
  for this_device in devices:
    print u' updating %s (%s of %s)' % (this_device, i, device_count)
    callGAPI(service=cd.chromeosdevices(), function=u'patch', deviceId=this_device, body=body, customerId=GC_Values[GC_CUSTOMER_ID])
    i += 1

def doUpdateMobile():
  cd = buildGAPIObject(u'directory')
  resourceId = sys.argv[3]
  i = 4
  action_body = patch_body = dict()
  doPatch = doAction = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'action':
      action_body[u'action'] = sys.argv[i+1].lower()
      if action_body[u'action'] == u'wipe':
        action_body[u'action'] = u'admin_remote_wipe'
      elif action_body[u'action'].replace(u'_', '') in [u'accountwipe', u'wipeaccount']:
        action_body[u'action'] = u'admin_account_wipe'
      if action_body[u'action'] not in [u'admin_remote_wipe', u'admin_account_wipe', u'approve', u'block', u'cancel_remote_wipe_then_activate', u'cancel_remote_wipe_then_block']:
        print u'ERROR: action must be wipe, wipeaccount, approve, block, cancel_remote_wipe_then_activate or cancel_remote_wipe_then_block. Got %s' % action_body[u'action']
        sys.exit(2)
      doAction = True
      i += 2
    elif sys.argv[i].lower() == u'model':
      patch_body[u'model'] = sys.argv[i+1]
      i += 2
      doPatch = True
    elif sys.argv[i].lower() == u'os':
      patch_body[u'os'] = sys.argv[i+1]
      i += 2
      doPatch = True
    elif sys.argv[i].lower() == u'useragent':
      patch_body[u'userAgent'] = sys.argv[i+1]
      i += 2
      doPatch = True
    else:
      print u'ERROR: %s is not a valid argument for "gam update mobile"' % sys.argv[i]
      sys.exit(2)
  if doPatch:
    callGAPI(service=cd.mobiledevices(), function=u'patch', resourceId=resourceId, body=patch_body, customerId=GC_Values[GC_CUSTOMER_ID])
  if doAction:
    callGAPI(service=cd.mobiledevices(), function=u'action', resourceId=resourceId, body=action_body, customerId=GC_Values[GC_CUSTOMER_ID])

def doDeleteMobile():
  cd = buildGAPIObject(u'directory')
  resourceId = sys.argv[3]
  callGAPI(service=cd.mobiledevices(), function='delete', resourceId=resourceId, customerId=GC_Values[GC_CUSTOMER_ID])

def doUpdateOrg():
  cd = buildGAPIObject(u'directory')
  orgUnitPath = sys.argv[3]
  if sys.argv[4].lower() in [u'move', u'add']:
    if sys.argv[5].lower() in usergroup_types:
      users = getUsersToModify(entity_type=sys.argv[5].lower(), entity=sys.argv[6])
    else:
      users = getUsersToModify(entity_type=u'user', entity=sys.argv[5])
    if (sys.argv[5].lower() == u'cros') or ((sys.argv[5].lower() == u'all') and (sys.argv[6].lower() == u'cros')):
      cros_count = len(users)
      current_cros = 1
      for cros in users:
        sys.stderr.write(u' moving %s to %s (%s/%s)\n' % (cros, orgUnitPath, current_cros, cros_count))
        callGAPI(service=cd.chromeosdevices(), function=u'patch', soft_errors=True,
                 customerId=GC_Values[GC_CUSTOMER_ID], deviceId=cros, body={u'orgUnitPath': '//%s' % orgUnitPath})
        current_cros += 1
    else:
      user_count = len(users)
      current_user = 1
      if orgUnitPath != u'/' and orgUnitPath[0] != '/': # we do want a / at the beginning for user updates
        orgUnitPath = u'/%s' % orgUnitPath
      for user in users:
        sys.stderr.write(u' moving %s to %s (%s/%s)\n' % (user, orgUnitPath, current_user, user_count))
        try:
          callGAPI(service=cd.users(), function=u'patch', throw_reasons=[u'conditionNotMet'], userKey=user, body={u'orgUnitPath': orgUnitPath})
        except googleapiclient.errors.HttpError:
          pass
        current_user += 1
  else:
    body = dict()
    i = 4
    while i < len(sys.argv):
      if sys.argv[i].lower() == u'name':
        body[u'name'] = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'description':
        body[u'description'] = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'parent':
        body[u'parentOrgUnitPath'] = sys.argv[i+1]
        if body[u'parentOrgUnitPath'][0] != u'/':
          body[u'parentOrgUnitPath'] = '/'+body[u'parentOrgUnitPath']
        i += 2
      elif sys.argv[i].lower() == u'noinherit':
        body[u'blockInheritance'] = True
        i += 1
      elif sys.argv[i].lower() == u'inherit':
        body[u'blockInheritance'] = False
        i += 1
      else:
        print u'ERROR: %s is not a valid argument for "gam update org"' % sys.argv[i]
        sys.exit(2)
    if orgUnitPath[0] == u'/': # we don't want a / at the beginning for OU updates
      orgUnitPath = orgUnitPath[1:]
    callGAPI(service=cd.orgunits(), function=u'update', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=orgUnitPath, body=body)

def doWhatIs():
  cd = buildGAPIObject(u'directory')
  email = sys.argv[2]
  if email.find(u'@') == -1:
    email = u'%s@%s' % (email, GC_Values[GC_DOMAIN])
  try:
    user_or_alias = callGAPI(service=cd.users(), function=u'get', throw_reasons=[u'notFound', u'badRequest', u'invalid'], userKey=email, fields=u'primaryEmail')
    if user_or_alias[u'primaryEmail'].lower() == email.lower():
      sys.stderr.write(u'%s is a user\n\n' % email)
      doGetUserInfo(user_email=email)
      return
    else:
      sys.stderr.write(u'%s is a user alias\n\n' % email)
      doGetAliasInfo(alias_email=email)
      return
  except googleapiclient.errors.HttpError:
    sys.stderr.write(u'%s is not a user...\n' % email)
    sys.stderr.write(u'%s is not a user alias...\n' % email)
  try:
    group = callGAPI(service=cd.groups(), function=u'get', throw_reasons=[u'notFound', u'badRequest'], groupKey=email, fields=u'email')
  except googleapiclient.errors.HttpError:
    sys.stderr.write(u'%s is not a group either!\n\nDoesn\'t seem to exist!\n\n' % email)
    sys.exit(1)
  if group[u'email'].lower() == email.lower():
    sys.stderr.write(u'%s is a group\n\n' % email)
    doGetGroupInfo(group_name=email)
  else:
    sys.stderr.write(u'%s is a group alias\n\n' % email)
    doGetAliasInfo(alias_email=email)

def doGetUserInfo(user_email=None):
  cd = buildGAPIObject(u'directory')
  i = 3
  if user_email == None:
    if len(sys.argv) > 3:
      user_email = sys.argv[3]
      i = 4
    else:
      storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
      credentials = storage.get()
      if credentials is None or credentials.invalid:
        doRequestOAuth()
        credentials = storage.get()
      user_email = credentials.id_token[u'email']
  if user_email[:4].lower() == u'uid:':
    user_email = user_email[4:]
  elif user_email.find(u'@') == -1:
    user_email = u'%s@%s' % (user_email, GC_Values[GC_DOMAIN])
  getSchemas = getAliases = getGroups = getLicenses = True
  projection = u'full'
  customFieldMask = viewType = None
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'noaliases':
      getAliases = False
      i += 1
    elif sys.argv[i].lower() == u'nogroups':
      getGroups = False
      i += 1
    elif sys.argv[i].lower() in [u'nolicenses', u'nolicences']:
      getLicenses = False
      i += 1
    elif sys.argv[i].lower() == u'noschemas':
      getSchemas = False
      projection = u'basic'
      i += 1
    elif sys.argv[i].lower() == u'schemas':
      getSchemas = True
      projection = u'custom'
      customFieldMask = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'userview':
      viewType = u'domain_public'
      getGroups = getLicenses = False
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam info user"' % sys.argv[i]
      sys.exit(2)
  user = callGAPI(service=cd.users(), function=u'get', userKey=user_email, projection=projection, customFieldMask=customFieldMask, viewType=viewType)
  print u'User: %s' % user[u'primaryEmail']
  if u'name' in user and u'givenName' in user[u'name']:
    print convertUTF8(u'First Name: %s' % user[u'name'][u'givenName'])
  if u'name' in user and u'familyName' in user[u'name']:
    print convertUTF8(u'Last Name: %s' % user[u'name'][u'familyName'])
  if u'isAdmin' in user:
    print u'Is a Super Admin: %s' % user[u'isAdmin']
  if u'isDelegatedAdmin' in user:
    print u'Is Delegated Admin: %s' % user[u'isDelegatedAdmin']
  if u'agreedToTerms' in user:
    print u'Has Agreed to Terms: %s' % user[u'agreedToTerms']
  if u'ipWhitelisted' in user:
    print u'IP Whitelisted: %s' % user[u'ipWhitelisted']
  if u'suspended' in user:
    print u'Account Suspended: %s' % user[u'suspended']
  if u'suspensionReason' in user:
    print u'Suspension Reason: %s' % user[u'suspensionReason']
  if u'changePasswordAtNextLogin' in user:
    print u'Must Change Password: %s' % user[u'changePasswordAtNextLogin']
  if u'id' in user:
    print u'Google Unique ID: %s' % user[u'id']
  if u'customerId' in user:
    print u'Customer ID: %s' % user[u'customerId']
  if u'isMailboxSetup' in user:
    print u'Mailbox is setup: %s' % user[u'isMailboxSetup']
  if u'includeInGlobalAddressList' in user:
    print u'Included in GAL: %s' % user[u'includeInGlobalAddressList']
  if u'creationTime' in user:
    print u'Creation Time: %s' % user[u'creationTime']
  if u'lastLoginTime' in user:
    if user[u'lastLoginTime'] == u'1970-01-01T00:00:00.000Z':
      print u'Last login time: Never'
    else:
      print u'Last login time: %s' % user[u'lastLoginTime']
  if u'orgUnitPath' in user:
    print u'Google Org Unit Path: %s\n' % user[u'orgUnitPath']
  if u'thumbnailPhotoUrl' in user:
    print u'Photo URL: %s\n' % user[u'thumbnailPhotoUrl']
  if u'ims' in user:
    print u'IMs:'
    for im in user[u'ims']:
      for key in im:
        print convertUTF8(u' %s: %s' % (key, im[key]))
      print u''
  if u'addresses' in user:
    print u'Addresses:'
    for address in user[u'addresses']:
      for key in address:
        print convertUTF8(u' %s: %s' % (key, address[key]))
      print u''
  if u'organizations' in user:
    print u'Organizations:'
    for org in user[u'organizations']:
      for key in org:
        if key == u'customType' and not org[key]:
          continue
        print convertUTF8(u' %s: %s' % (key, org[key]))
      print u''
  if u'phones' in user:
    print u'Phones:'
    for phone in user[u'phones']:
      for key in phone:
        print convertUTF8(u' %s: %s' % (key, phone[key]))
      print u''
  if u'emails' in user:
    if len(user[u'emails']) > 1:
      print u'Other Emails:'
      for an_email in user[u'emails']:
        if an_email[u'address'].lower() == user[u'primaryEmail'].lower():
          continue
        for key in an_email:
          if key == u'type' and an_email[key] == u'custom':
            continue
          if key == u'customType':
            print convertUTF8(u' type: %s' % an_email[key])
          else:
            print convertUTF8(u' %s: %s' % (key, an_email[key]))
      print u''
  if u'relations' in user:
    print u'Relations:'
    for relation in user[u'relations']:
      for key in relation:
        if key == u'type' and relation[key] == u'custom':
          continue
        elif key == u'customType':
          print convertUTF8(u' %s: %s' % (u'type', relation[key]))
        else:
          print convertUTF8(u' %s: %s' % (key, relation[key]))
      print u''
  if u'externalIds' in user:
    print u'External IDs:'
    for externalId in user[u'externalIds']:
      for key in externalId:
        if key == u'type' and externalId[key] == u'custom':
          continue
        elif key == u'customType':
          print convertUTF8(u' %s: %s' % (u'type', externalId[key]))
        else:
          print convertUTF8(u' %s: %s' % (key, externalId[key]))
      print u''
  if getSchemas:
    if u'customSchemas' in user:
      print u'Custom Schemas:'
      for schema in user[u'customSchemas']:
        print u' Schema: %s' % schema
        for field in user[u'customSchemas'][schema]:
          if type(user[u'customSchemas'][schema][field]) is list:
            print u'  %s:' % field
            for an_item in user[u'customSchemas'][schema][field]:
              print convertUTF8(u'   %s' % an_item[u'value'])
          else:
            print convertUTF8(u'  %s: %s' % (field, user[u'customSchemas'][schema][field]))
        print
  if getAliases:
    if u'aliases' in user:
      print u'Email Aliases:'
      for alias in user[u'aliases']:
        print u'  %s' % alias
    if u'nonEditableAliases' in user:
      print u'Non-Editable Aliases:'
      for alias in user[u'nonEditableAliases']:
        print u'  %s' % alias
  if getGroups:
    groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', userKey=user_email, fields=u'groups(name,email),nextPageToken')
    if len(groups) > 0:
      print u'Groups: (%s)' % len(groups)
      for group in groups:
        print u'   %s <%s>' % (group[u'name'], group[u'email'])
  if getLicenses:
    print u'Licenses:'
    lic = buildGAPIObject(api='licensing')
    for sku in [u'Google-Apps-For-Business', u'Google-Apps-Unlimited', u'Google-Apps-For-Postini',
                u'Google-Apps-Lite', u'Google-Vault', u'Google-Vault-Former-Employee']:
      productId, skuId = getProductAndSKU(sku)
      try:
        result = callGAPI(service=lic.licenseAssignments(), function=u'get', throw_reasons=['notFound'], userId=user_email, productId=productId, skuId=skuId)
      except googleapiclient.errors.HttpError:
        continue
      print u' %s' % result[u'skuId']

def doGetGroupInfo(group_name=None):
  cd = buildGAPIObject(u'directory')
  gs = buildGAPIObject(u'groupssettings')
  getAliases = getUsers = True
  getGroups = False
  if group_name == None:
    group_name = sys.argv[3]
    i = 4
  else:
    i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'nousers':
      getUsers = False
      i += 1
    elif sys.argv[i].lower() == u'noaliases':
      getAliases = False
      i += 1
    elif sys.argv[i].lower() == u'groups':
      getGroups = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam info group"' % sys.argv[i]
      sys.exit(2)
  if group_name[:4].lower() == u'uid:':
    group_name = group_name[4:]
  elif group_name.find(u'@') == -1:
    group_name = group_name+u'@'+GC_Values[GC_DOMAIN]
  basic_info = callGAPI(service=cd.groups(), function=u'get', groupKey=group_name)
  try:
    settings = callGAPI(service=gs.groups(), function=u'get', retry_reasons=[u'serviceLimit'], throw_reasons=u'authError',
                        groupUniqueId=basic_info[u'email']) # Use email address retrieved from cd since GS API doesn't support uid
  except googleapiclient.errors.HttpError:
    pass
  print u''
  print u'Group Settings:'
  for key, value in basic_info.items():
    if (key in [u'kind', u'etag']) or ((key == u'aliases') and (not getAliases)):
      continue
    if type(value) == type(list()):
      print u' %s:' % key
      for val in value:
        print u'  %s' % val
    else:
      print convertUTF8(u' %s: %s' % (key, value))
  try:
    for key, value in settings.items():
      if key in [u'kind', u'etag', u'description', u'email', u'name']:
        continue
      elif key == u'maxMessageBytes':
        if value > 1024*1024:
          value = u'%sM' % (value / 1024 / 1024)
        elif value > 1024:
          value = u'%sK' % (value / 1024)
      print u' %s: %s' % (key, value)
  except UnboundLocalError:
    pass
  if getGroups:
    groups = callGAPIpages(cd.groups(), u'list', u'groups',
                           userKey=basic_info[u'email'], fields=u'nextPageToken,groups(name,email)')
    if groups:
      print u'Groups: ({0})'.format(len(groups))
      for groupm in groups:
        print u'  %s: %s' % (groupm[u'name'], groupm[u'email'])
  if getUsers:
    members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', groupKey=group_name)
    print u'Members:'
    for member in members:
      try:
        print u' %s: %s (%s)' % (member[u'role'].lower(), member[u'email'], member[u'type'].lower())
      except KeyError:
        try:
          print u' member: %s (%s)' % (member[u'email'], member[u'type'].lower())
        except KeyError:
          print u' member: %s (%s)' % (member[u'id'], member[u'type'].lower())
    print u'Total %s users in group' % len(members)

def doGetAliasInfo(alias_email=None):
  cd = buildGAPIObject(u'directory')
  if alias_email == None:
    alias_email = sys.argv[3]
  if alias_email.find(u'@') == -1:
    alias_email = u'%s@%s' % (alias_email, GC_Values[GC_DOMAIN])
  try:
    result = callGAPI(service=cd.users(), function=u'get', throw_reasons=[u'invalid', u'badRequest'], userKey=alias_email)
  except googleapiclient.errors.HttpError:
    result = callGAPI(service=cd.groups(), function=u'get', groupKey=alias_email)
  print u' Alias Email: %s' % alias_email
  try:
    if result[u'primaryEmail'].lower() == alias_email.lower():
      print u'Error: %s is a primary user email address, not an alias.' % alias_email
      sys.exit(3)
    print u' User Email: %s' % result[u'primaryEmail']
  except KeyError:
    print u' Group Email: %s' % result[u'email']
  print u' Unique ID: %s' % result[u'id']

def doGetResourceCalendarInfo():
  cd = buildGAPIObject(u'directory')
  resId = sys.argv[3]
  resource = callGAPI(service=cd.resources().calendars(), function=u'get',
                      customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId)
  for key, value in resource.items():
    if key in [u'kind', u'etag', u'etags']:
      continue
    print u'%s: %s' % (key, value)

def doGetCrosInfo():
  cd = buildGAPIObject(u'directory')
  deviceId = sys.argv[3]
  info = callGAPI(service=cd.chromeosdevices(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], deviceId=deviceId)
  print_json(None, info)

def doGetMobileInfo():
  cd = buildGAPIObject(u'directory')
  deviceId = sys.argv[3]
  info = callGAPI(service=cd.mobiledevices(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], resourceId=deviceId)
  print_json(None, info)

def print_json(object_name, object_value, spacing=u''):
  if object_name in [u'kind', u'etag', u'etags']:
    return
  if object_name != None:
    sys.stdout.write(u'%s%s: ' % (spacing, object_name))
  if type(object_value) is list:
    if len(object_value) == 1 and type(object_value[0]) in (str, unicode, int):
      sys.stdout.write(u'%s\n' % object_value[0])
      return
    sys.stdout.write(u'\n')
    for a_value in object_value:
      if type(a_value) in (str, unicode):
        print u' %s%s' % (spacing, a_value)
      else:
        print_json(object_name=None, object_value=a_value, spacing=u' %s' % spacing)
  elif type(object_value) is dict:
    for another_object in object_value:
      print_json(object_name=another_object, object_value=object_value[another_object], spacing=spacing)
  else:
    sys.stdout.write(u'%s\n' % (object_value))

def doUpdateNotification():
  cd = buildGAPIObject(u'directory')
  ids = list()
  get_all = False
  i = 3
  isUnread = None
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'unread':
      isUnread = True
      mark_as = u'unread'
      i += 1
    elif sys.argv[i].lower() == u'read':
      isUnread = False
      mark_as = u'read'
      i += 1
    elif sys.argv[i].lower() == u'id':
      if sys.argv[i+1].lower() == u'all':
        get_all = True
      else:
        ids.append(sys.argv[i+1])
      i += 2
    else:
      print 'ERROR: %s is not a valid argument for "gam update notification"' % sys.argv[i]
      sys.exit(2)
  if isUnread == None:
    print u'ERROR: notifications need to be marked as read or unread.'
    sys.exit(2)
  if get_all:
    notifications = callGAPIpages(service=cd.notifications(), function=u'list', customer=GC_Values[GC_CUSTOMER_ID], fields=u'items(notificationId,isUnread),nextPageToken')
    for noti in notifications:
      if noti[u'isUnread'] != isUnread:
        ids.append(noti[u'notificationId'])
  print u'Marking %s notification(s) as %s...' % (len(ids), mark_as)
  for notificationId in ids:
    result = callGAPI(service=cd.notifications(), function=u'patch', customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId, body={u'isUnread': isUnread}, fields=u'notificationId,isUnread')
    if result[u'isUnread']:
      read_result = u'unread'
    else:
      read_result = u'read'
    print u'marked %s as %s' % (result[u'notificationId'], read_result)

def doDeleteNotification():
  cd = buildGAPIObject(u'directory')
  ids = list()
  get_all = False
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'id':
      if sys.argv[i+1].lower() == u'all':
        get_all = True
      else:
        ids.append(sys.argv[i+1])
      i += 2
    else:
      print 'ERROR: %s is not a valid argument for "gam delete notification", expected id' % sys.argv[i]
      sys.exit(2)
  if get_all:
    notifications = callGAPIpages(service=cd.notifications(), function=u'list', customer=GC_Values[GC_CUSTOMER_ID], fields=u'items(notificationId),nextPageToken')
    for noti in notifications:
      ids.append(noti[u'notificationId'])
  print u'Deleting %s notification(s)...' % len(ids)
  for notificationId in ids:
    callGAPI(service=cd.notifications(), function=u'delete', customer=GC_Values[GC_CUSTOMER_ID], notificationId=notificationId)
    print u'deleted %s' % id

def doSiteVerifyShow():
  verif = buildGAPIObject(u'siteVerification')
  a_domain = sys.argv[3]
  txt_record = callGAPI(service=verif.webResource(), function=u'getToken', body={u'site':{u'type':u'INET_DOMAIN', u'identifier':a_domain}, u'verificationMethod':u'DNS_TXT'})
  print u'TXT Record Name:   %s' % a_domain
  print u'TXT Record Value:  %s' % txt_record[u'token']
  print
  cname_record = callGAPI(service=verif.webResource(), function=u'getToken', body={u'site':{u'type':u'INET_DOMAIN', u'identifier':a_domain}, u'verificationMethod':u'DNS_CNAME'})
  cname_token = cname_record[u'token']
  cname_list = cname_token.split(u' ')
  cname_subdomain = cname_list[0]
  cname_value = cname_list[1]
  print u'CNAME Record Name:   %s.%s' % (cname_subdomain, a_domain)
  print u'CNAME Record Value:  %s' % cname_value
  print u''
  webserver_file_record = callGAPI(service=verif.webResource(), function=u'getToken', body={u'site':{u'type':u'SITE', u'identifier':u'http://%s/' % a_domain}, u'verificationMethod':u'FILE'})
  webserver_file_token = webserver_file_record[u'token']
  print u'Saving web server verification file to: %s' % webserver_file_token
  writeFile(webserver_file_token, u'google-site-verification: {0}'.format(webserver_file_token), continueOnError=True)
  print u'Verification File URL: http://%s/%s' % (a_domain, webserver_file_token)
  print
  webserver_meta_record = callGAPI(service=verif.webResource(), function=u'getToken', body={u'site':{u'type':u'SITE', u'identifier':u'http://%s/' % a_domain}, u'verificationMethod':u'META'})
  print u'Meta URL:               http://%s/' % a_domain
  print u'Meta HTML Header Data:  %s' % webserver_meta_record[u'token']
  print

def doGetSiteVerifications():
  verif = buildGAPIObject(u'siteVerification')
  sites = callGAPI(service=verif.webResource(), function=u'list')
  try:
    for site in sites[u'items']:
      print u'Site: %s' % site[u'site'][u'identifier']
      print u'Type: %s' % site[u'site'][u'type']
      print u'Owners:'
      for owner in site[u'owners']:
        print u' %s' % owner
      print
  except KeyError:
    print u'No Sites Verified.'

def doSiteVerifyAttempt():
  verif = buildGAPIObject(u'siteVerification')
  a_domain = sys.argv[3]
  verificationMethod = sys.argv[4].upper()
  if verificationMethod == u'CNAME':
    verificationMethod = u'DNS_CNAME'
  elif verificationMethod in [u'TXT', u'TEXT']:
    verificationMethod = u'DNS_TXT'
  if verificationMethod in [u'DNS_TXT', u'DNS_CNAME']:
    verify_type = u'INET_DOMAIN'
    identifier = a_domain
  else:
    verify_type = u'SITE'
    identifier = u'http://%s/' % a_domain
  body = {u'site':{u'type':verify_type, u'identifier':identifier}, u'verificationMethod':verificationMethod}
  try:
    verify_result = callGAPI(service=verif.webResource(), function=u'insert', throw_reasons=[u'badRequest'], verificationMethod=verificationMethod, body=body)
  except googleapiclient.errors.HttpError, e:
    error = json.loads(e.content)
    message = error[u'error'][u'errors'][0][u'message']
    print u'ERROR: %s' % message
    verify_data = callGAPI(service=verif.webResource(), function=u'getToken', body=body)
    print u'Method:  %s' % verify_data[u'method']
    print u'Token:      %s' % verify_data[u'token']
    if verify_data[u'method'] == u'DNS_CNAME':
      try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [u'8.8.8.8', u'8.8.4.4']
        cname_token = verify_data[u'token']
        cname_list = cname_token.split(u' ')
        cname_subdomain = cname_list[0]
        try:
          answers = resolver.query(u'%s.%s' % (cname_subdomain, a_domain), u'A')
          for answer in answers:
            print u'DNS Record: %s' % answer
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
          print u'ERROR: No such domain found in DNS!'
      except ImportError:
        pass
    elif verify_data[u'method'] == u'DNS_TXT':
      try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [u'8.8.8.8', u'8.8.4.4']
        try:
          answers = resolver.query(a_domain, u'TXT')
          for answer in answers:
            print u'DNS Record: %s' % str(answer).replace(u'"', u'')
        except dns.resolver.NXDOMAIN:
          print u'ERROR: no such domain found in DNS!'
      except ImportError:
        pass
    return
  print u'SUCCESS!'
  print u'Verified:  %s' % verify_result[u'site'][u'identifier']
  print u'ID:  %s' % verify_result[u'id']
  print u'Type: %s' % verify_result[u'site'][u'type']
  print u'All Owners:'
  try:
    for owner in verify_result[u'owners']:
      print u' %s' % owner
  except KeyError:
    pass
  print
  print u'You can now add %s or it\'s subdomains as secondary or domain aliases of the %s Google Apps Account.' % (a_domain, GC_Values[GC_DOMAIN])

def doGetNotifications():
  cd = buildGAPIObject(u'directory')
  i = 3
  unread_only = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'unreadonly':
      unread_only = True
    else:
      print 'ERROR: %s is not a valid argument for "gam info notification", expected unreadonly' % sys.argv[i]
      sys.exit(2)
    i += 1
  notifications = callGAPIpages(service=cd.notifications(), function=u'list', customer=GC_Values[GC_CUSTOMER_ID])
  for notification in notifications:
    if unread_only and not notification[u'isUnread']:
      continue
    print u'From: %s' % notification[u'fromAddress']
    print u'Subject: %s' % notification[u'subject']
    print u'Date: %s' % notification[u'sendTime']
    print u'ID: %s' % notification[u'notificationId']
    if notification[u'isUnread']:
      print u'Read Status: UNREAD'
    else:
      print u'Read Status: READ'
    print u''
    print dehtml(notification[u'body'])
    print u''
    print u'--------------'
    print u''

def doGetOrgInfo():
  cd = buildGAPIObject(u'directory')
  name = sys.argv[3]
  get_users = True
  show_children = False
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'nousers':
      get_users = False
      i += 1
    elif sys.argv[i].lower() in [u'children', u'child']:
      show_children = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam info org"' % sys.argv[i]
      sys.exit(2)
  if name == u'/':
    orgs = callGAPI(service=cd.orgunits(), function=u'list',
                    customerId=GC_Values[GC_CUSTOMER_ID], type=u'children',
                    fields=u'organizationUnits/parentOrgUnitId')
    name = orgs[u'organizationUnits'][0][u'parentOrgUnitId']
  if len(name) > 1 and name[0] == u'/':
    name = name[1:]
  result = callGAPI(service=cd.orgunits(), function=u'get', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=name)
  print_json(None, result)
  if get_users:
    name = result[u'orgUnitPath']
    print u'Users: '
    page_message = u'Got %%total_items%% users: %%first_item%% - %%last_item%%\n'
    users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                          message_attribute=u'primaryEmail', customer=GC_Values[GC_CUSTOMER_ID], query=u"orgUnitPath='%s'" % name,
                          fields=u'users(primaryEmail,orgUnitPath),nextPageToken', maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for user in users:
      if show_children or (name.lower() == user[u'orgUnitPath'].lower()):
        sys.stdout.write(u' %s' % user[u'primaryEmail'])
        if name.lower() != user[u'orgUnitPath'].lower():
          print u' (child)'
        else:
          print u''

def doGetASPs(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    asps = callGAPI(service=cd.asps(), function=u'list', userKey=user)
    print u'Application-Specific Passwords for %s' % user
    try:
      for asp in asps[u'items']:
        if asp[u'creationTime'] == u'0':
          created_date = u'Unknown'
        else:
          created_date = datetime.datetime.fromtimestamp(int(asp[u'creationTime'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
        if asp[u'lastTimeUsed'] == u'0':
          used_date = u'Never'
        else:
          used_date = datetime.datetime.fromtimestamp(int(asp[u'lastTimeUsed'])/1000).strftime(u'%Y-%m-%d %H:%M:%S')
        print u' ID: %s\n  Name: %s\n  Created: %s\n  Last Used: %s\n' % (asp[u'codeId'], asp[u'name'], created_date, used_date)
    except KeyError:
      print u' no ASPs for %s\n' % user

def doDelASP(users):
  cd = buildGAPIObject(u'directory')
  codeId = sys.argv[5]
  for user in users:
    callGAPI(service=cd.asps(), function=u'delete', userKey=user, codeId=codeId)
    print u'deleted ASP %s for %s' % (codeId, user)

def printBackupCodes(user, codes):
  jcount = len(codes[u'items']) if (codes and (u'items' in codes)) else 0
  print u'Backup verification codes for {0}'.format(user)
  print u''
  if jcount > 0:
    j = 0
    for code in codes[u'items']:
      j += 1
      print u'{0}. {1}'.format(j, code[u'verificationCode'])
    print u''

def doGetBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    try:
      codes = callGAPI(service=cd.verificationCodes(), function=u'list', throw_reasons=[u'invalidArgument', u'invalid'], userKey=user)
    except googleapiclient.errors.HttpError:
      codes = None
    printBackupCodes(user, codes)

def doGenBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    callGAPI(service=cd.verificationCodes(), function=u'generate', userKey=user)
    codes = callGAPI(service=cd.verificationCodes(), function=u'list', userKey=user)
    printBackupCodes(user, codes)

def doDelBackupCodes(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    try:
      callGAPI(service=cd.verificationCodes(), function=u'invalidate', soft_errors=True, throw_reasons=[u'invalid',], userKey=user)
    except googleapiclient.errors.HttpError:
      print u'No 2SV backup codes for %s' % user
      continue
    print u'2SV backup codes for %s invalidated' % user

def commonClientIds(clientId):
  if clientId == u'gasmo':
    return u'1095133494869.apps.googleusercontent.com'
  return clientId

def doGetTokens(users):
  cd = buildGAPIObject(u'directory')
  clientId = None
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'clientid':
      clientId = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for gam <users> show tokens' % sys.argv[i]
      sys.exit(2)
  if clientId:
    clientId = commonClientIds(clientId)
    for user in users:
      try:
        token = callGAPI(service=cd.tokens(), function=u'get', throw_reasons=[u'notFound',], userKey=user, clientId=clientId, fields=u'clientId')
      except googleapiclient.errors.HttpError:
        continue
      print u'%s has allowed this token' % user
    return
  for user in users:
    tokens = callGAPI(service=cd.tokens(), function=u'list', userKey=user)
    print u'Tokens for %s:' % user
    try:
      for token in tokens[u'items']:
        print u' Client ID: %s' % token[u'clientId']
        for item in token:
          if item in [u'etag', u'kind', u'clientId']:
            continue
          if type(token[item]) is list:
            print u' %s:' % item
            for it in token[item]:
              print u'  %s' % it
          if type(token[item]) in (unicode, bool):
            try:
              print u' %s: %s' % (item, token[item])
            except UnicodeEncodeError:
              print u' %s: %s' % (item, token[item][:-1])
        print u''
    except KeyError:
      print u' no tokens for %s' % user
    print u''

def doDelTokens(users):
  cd = buildGAPIObject(u'directory')
  clientId = sys.argv[6]
  clientId = commonClientIds(clientId)
  for user in users:
    callGAPI(service=cd.tokens(), function=u'delete', userKey=user, clientId=clientId)
    print u'Deleted token for %s' % user

def doDeprovUser(users):
  cd = buildGAPIObject(u'directory')
  for user in users:
    print u'Getting Application Specific Passwords for %s' % user
    asps = callGAPI(service=cd.asps(), function=u'list', userKey=user, fields=u'items/codeId')
    i = 1
    try:
      for asp in asps[u'items']:
        print u' deleting ASP %s of %s' % (i, len(asps['items']))
        callGAPI(service=cd.asps(), function=u'delete', userKey=user, codeId=asp[u'codeId'])
        i += 1
    except KeyError:
      print u'No ASPs'
    print u'Invalidating 2SV Backup Codes for %s' % user
    try:
      callGAPI(service=cd.verificationCodes(), function=u'invalidate', soft_errors=True, throw_reasons=[u'invalid'], userKey=user)
    except googleapiclient.errors.HttpError:
      print u'No 2SV Backup Codes'
    print u'Getting tokens for %s...' % user
    tokens = callGAPI(service=cd.tokens(), function=u'list', userKey=user, fields=u'items/clientId')
    i = 1
    try:
      for token in tokens[u'items']:
        print u' deleting token %s of %s' % (i, len(tokens['items']))
        callGAPI(service=cd.tokens(), function=u'delete', userKey=user, clientId=token[u'clientId'])
        i += 1
    except KeyError:
      print u'No Tokens'
    print u'Done deprovisioning %s' % user

def doUpdateInstance():
  adminObj = getAdminSettingsObject()
  cd = buildGAPIObject(u'directory')
  body = {}
  if GC_Values[GC_CUSTOMER_ID] != MY_CUSTOMER:
    customerKey = GC_Values[GC_CUSTOMER_ID]
  else:
    customerKey = MY_CUSTOMER
  command = sys.argv[3].lower()
  if command == u'language':
    body[u'language'] = sys.argv[4]
  elif command == u'name':
    body[u'postalAddress'] = {u'organizationName': sys.argv[4]}
  elif command == u'admin_secondary_email':
    body[u'alternateEmail'] = sys.argv[4]
  elif command == u'phone':
    body[u'phoneNumber'] = sys.argv[4]
  elif command == u'contact_name':
    body[u'postalAddress'] = {u'contactName': sys.argv[4]}
  elif command == u'locality':
    body[u'postalAddress'] = {u'locality': sys.argv[4]}
  elif command == u'region':
    body[u'postalAddress'] = {u'region': sys.argv[4]}
  elif command == u'country':
    body[u'postalAddress'] = {u'countryCode': sys.argv[4]}
  elif command == u'postal_code':
    body[u'postalAddress'] = {u'postalCode': sys.argv[4]}
  elif command == u'address1':
    body[u'postalAddress'] = {u'addressLine1': sys.argv[4]}
  elif command == u'address2':
    body[u'postalAddress'] = {u'addressLine2': sys.argv[4]}
  elif command == u'address3':
    body[u'postalAddress'] = {u'addressLine3': sys.argv[4]}
  elif command == u'logo':
    logoFile = sys.argv[4]
    logoImage = readFile(logoFile)
    callGData(service=adminObj, function=u'UpdateDomainLogo', logoImage=logoImage)
  elif command == u'sso_settings':
    enableSSO = samlSignonUri = samlLogoutUri = changePasswordUri = ssoWhitelist = useDomainSpecificIssuer = None
    i = 4
    while i < len(sys.argv):
      if sys.argv[i].lower() == u'enabled':
        if sys.argv[i+1].lower() == u'true':
          enableSSO = True
        elif sys.argv[i+1].lower() == u'false':
          enableSSO = False
        else:
          print u'ERROR: value for enabled must be true or false, got %s' % sys.argv[i+1]
          sys.exit(2)
        i += 2
      elif sys.argv[i].lower() == u'sign_on_uri':
        samlSignonUri = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'sign_out_uri':
        samlLogoutUri = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'password_uri':
        changePasswordUri = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'whitelist':
        ssoWhitelist = sys.argv[i+1]
        i += 2
      elif sys.argv[i].lower() == u'use_domain_specific_issuer':
        if sys.argv[i+1].lower() == u'true':
          useDomainSpecificIssuer = True
        elif sys.argv[i+1].lower() == u'false':
          useDomainSpecificIssuer = False
        else:
          print u'ERROR: value for use_domain_specific_issuer must be true or false, got %s' % sys.argv[i+1]
          sys.exit(2)
        i += 2
      else:
        print u'ERROR: unknown option for "gam update domain sso_settings...": %s' % sys.argv[i]
        sys.exit(2)
    callGData(service=adminObj, function=u'UpdateSSOSettings', enableSSO=enableSSO,
              samlSignonUri=samlSignonUri, samlLogoutUri=samlLogoutUri,
              changePasswordUri=changePasswordUri, ssoWhitelist=ssoWhitelist,
              useDomainSpecificIssuer=useDomainSpecificIssuer)
  elif command == u'sso_key':
    keyFile = sys.argv[4]
    keyData = readFile(keyFile)
    callGData(service=adminObj, function=u'UpdateSSOKey', signingKey=keyData)
  else:
    print u'ERROR: %s is not a valid argument for "gam update instance"' % command
    sys.exit(2)
  if body != {}:
    callGAPI(cd.customers(), u'update', customerKey=customerKey, body=body)

def doGetInstanceInfo():
  adm = buildGAPIObject(u'admin-settings')
  if len(sys.argv) > 4 and sys.argv[3].lower() == u'logo':
    target_file = sys.argv[4]
    url = 'http://www.google.com/a/cpanel/%s/images/logo.gif' % (GC_Values[GC_DOMAIN])
    geturl(url, target_file)
    sys.exit(0)
  cd = buildGAPIObject(u'directory')
  if GC_Values[GC_CUSTOMER_ID] != MY_CUSTOMER:
    customerKey = GC_Values[GC_CUSTOMER_ID]
  else:
    customerKey = MY_CUSTOMER
  customer_info = callGAPI(cd.customers(), u'get', customerKey=customerKey)
  customerId = customer_info[u'id']
  primaryDomain = customer_info[u'customerDomain']
  print u'Customer ID: %s' % customerId
  print u'Primary Domain: %s' % primaryDomain
  print u'Customer Creation Time: %s' % customer_info[u'customerCreationTime']
  verified = callGAPI(cd.domains(), u'get', fields=u'verified', customer=customerId, domainName=primaryDomain)[u'verified']
  print u'Primary Domain Verified: %s' % verified
  print u'Default Language: %s' % customer_info[u'language']
  if u'postalAddress' in customer_info:
    print u'Address:'
    for (key, value) in customer_info[u'postalAddress'].items():
      print u' %s: %s' % (key, value)
  if u'phoneNumber' in customer_info:
    print u'Phone: %s' % customer_info[u'phoneNumber']
  print u'Admin Secondary Email: %s' % customer_info[u'alternateEmail']
  max_users = callGAPI(service=adm.maximumNumberOfUsers(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Maximum Users: %s' % max_users[u'entry'][u'apps$property'][0][u'value']
  current_users = callGAPI(service=adm.currentNumberOfUsers(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Current Users: %s' % current_users[u'entry'][u'apps$property'][0][u'value']
  domain_edition = callGAPI(service=adm.edition(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Domain Edition: %s' % domain_edition[u'entry'][u'apps$property'][0][u'value']
  customer_pin = callGAPI(service=adm.customerPIN(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  print u'Customer PIN: %s' % customer_pin[u'entry'][u'apps$property'][0][u'value']
  ssosettings = callGAPI(service=adm.ssoGeneral(), function=u'get', domainName=GC_Values[GC_DOMAIN])
  for entry in ssosettings[u'entry'][u'apps$property']:
    if entry[u'name'] == u'enableSSO':
      print u'SSO Enabled: %s' % entry[u'value']
    elif entry[u'name'] == u'samlSignonUri':
      print u'SSO Signon Page: %s' % entry[u'value']
    elif entry[u'name'] == u'samlLogoutUri':
      print u'SSO Logout Page: %s' % entry[u'value']
    elif entry[u'name'] == u'changePasswordUri':
      print u'SSO Password Page: %s' % entry[u'value']
    elif entry[u'name'] == u'ssoWhitelist':
      print u'SSO Whitelist IPs: %s' % entry[u'value']
    elif entry[u'name'] == u'useDomainSpecificIssuer':
      print u'SSO Use Domain Specific Issuer: %s' % entry[u'value']
  ssokey = callGAPI(service=adm.ssoSigningKey(), function=u'get', silent_errors=True, soft_errors=True, domainName=GC_Values[GC_DOMAIN])
  try:
    for entry in ssokey[u'entry'][u'apps$property']:
      if entry[u'name'] == u'algorithm':
        print u'SSO Key Algorithm: %s' % entry[u'value']
      elif entry[u'name'] == u'format':
        print u'SSO Key Format: %s' % entry[u'value']
      elif entry[u'name'] == u'modulus':
        print u'SSO Key Modulus: %s' % entry[u'value']
      elif entry[u'name'] == u'exponent':
        print u'SSO Key Exponent: %s' % entry[u'value']
      elif entry[u'name'] == u'yValue':
        print u'SSO Key yValue: %s' % entry[u'value']
      elif entry[u'name'] == u'signingKey':
        print u'Full SSO Key: %s' % entry[u'value']
  except TypeError:
    pass

def doDeleteUser():
  cd = buildGAPIObject(u'directory')
  user_email = sys.argv[3]
  if user_email[:4].lower() == u'uid:':
    user_email = user_email[4:]
  elif user_email.find(u'@') == -1:
    user_email = u'%s@%s' % (user_email, GC_Values[GC_DOMAIN])
  print u"Deleting account for %s" % (user_email)
  callGAPI(service=cd.users(), function=u'delete', userKey=user_email)

def doUndeleteUser():
  cd = buildGAPIObject(u'directory')
  user = sys.argv[3].lower()
  user_uid = False
  orgUnit = u'/'
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() in [u'ou', u'org']:
      orgUnit = sys.argv[i+1]
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam undelete user"' % sys.argv[i]
      sys.exit(2)
  if user[:4].lower() == u'uid:':
    user_uid = user[4:]
  elif user.find(u'@') == -1:
    user = u'%s@%s' % (user, GC_Values[GC_DOMAIN])
  if not user_uid:
    print u'Looking up UID for %s...' % user
    deleted_users = callGAPIpages(service=cd.users(), function=u'list',
                                  items=u'users', customer=GC_Values[GC_CUSTOMER_ID], showDeleted=True, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    matching_users = list()
    for deleted_user in deleted_users:
      if str(deleted_user[u'primaryEmail']).lower() == user:
        matching_users.append(deleted_user)
    if len(matching_users) < 1:
      print u'ERROR: could not find deleted user with that address.'
      sys.exit(3)
    elif len(matching_users) > 1:
      print u'ERROR: more than one matching deleted %s user. Please select the correct one to undelete and specify with "gam undelete user uid:<uid>"' % user
      print u''
      for matching_user in matching_users:
        print u' uid:%s ' % matching_user[u'id']
        for attr_name in [u'creationTime', u'lastLoginTime', u'deletionTime']:
          try:
            if matching_user[attr_name] == u'1970-01-01T00:00:00.000Z':
              matching_user[attr_name] = u'Never'
            print u'   %s: %s ' % (attr_name, matching_user[attr_name])
          except KeyError:
            pass
        print
      sys.exit(3)
    else:
      user_uid = matching_users[0][u'id']
  print u"Undeleting account for %s" % user
  callGAPI(service=cd.users(), function=u'undelete', userKey=user_uid, body={u'orgUnitPath': orgUnit})

def doDeleteGroup():
  cd = buildGAPIObject(u'directory')
  group = sys.argv[3]
  if group[:4].lower() == u'uid:':
    group = group[4:]
  elif group.find(u'@') == -1:
    group = u'%s@%s' % (group, GC_Values[GC_DOMAIN])
  print u"Deleting group %s" % group
  callGAPI(service=cd.groups(), function=u'delete', groupKey=group)

def doDeleteAlias(alias_email=None):
  cd = buildGAPIObject(u'directory')
  is_user = is_group = False
  if alias_email == None:
    alias_email = sys.argv[3]
  if alias_email.lower() == u'user':
    is_user = True
    alias_email = sys.argv[4]
  elif alias_email.lower() == u'group':
    is_group = True
    alias_email = sys.argv[4]
  if alias_email.find(u'@') == -1:
    alias_email = u'%s@%s' % (alias_email, GC_Values[GC_DOMAIN])
  print u"Deleting alias %s" % alias_email
  if is_user or (not is_user and not is_group):
    try:
      callGAPI(service=cd.users().aliases(), function=u'delete', throw_reasons=[u'invalid', u'badRequest', u'notFound'], userKey=alias_email, alias=alias_email)
      return
    except googleapiclient.errors.HttpError, e:
      error = json.loads(e.content)
      reason = error[u'error'][u'errors'][0][u'reason']
      if reason == u'notFound':
        print u'Error: The alias %s does not exist' % alias_email
        sys.exit(4)
  if not is_user or (not is_user and not is_group):
    callGAPI(service=cd.groups().aliases(), function=u'delete', groupKey=alias_email, alias=alias_email)

def doDeleteResourceCalendar():
  resId = sys.argv[3]
  cd = buildGAPIObject(u'directory')
  print u"Deleting resource calendar %s" % resId
  callGAPI(service=cd.resources().calendars(), function=u'delete',
           customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId)

def doDeleteOrg():
  cd = buildGAPIObject(u'directory')
  name = sys.argv[3]
  if name[0] == u'/':
    name = name[1:]
  print u"Deleting organization %s" % name
  callGAPI(service=cd.orgunits(), function=u'delete', customerId=GC_Values[GC_CUSTOMER_ID], orgUnitPath=name)

def output_csv(csv_list, titles, list_type, todrive):
  csv.register_dialect(u'nixstdout', lineterminator=u'\n')
  if todrive:
    string_file = StringIO.StringIO()
    writer = csv.DictWriter(string_file, fieldnames=titles, dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  else:
    writer = csv.DictWriter(sys.stdout, fieldnames=titles, dialect=u'nixstdout', quoting=csv.QUOTE_MINIMAL)
  writer.writerows(csv_list)
  if todrive:
    columns = len(csv_list[0])
    rows = len(csv_list)
    cell_count = rows * columns
    convert = True
    if cell_count > 500000 or columns > 256:
      print u'{0}{1}'.format(WARNING_PREFIX, MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET)
      convert = False
    drive = buildGAPIObject(u'drive')
    result = callGAPI(service=drive.files(), function=u'insert', convert=convert,
                      body={u'description': u' '.join(sys.argv), u'title': u'%s - %s' % (GC_Values[GC_DOMAIN], list_type), u'mimeType': u'text/csv'},
                      media_body=googleapiclient.http.MediaInMemoryUpload(string_file.getvalue(), mimetype=u'text/csv'))
    file_url = result[u'alternateLink']
    if GC_Values[GC_NO_BROWSER]:
      msg_txt = u'Drive file uploaded to:\n %s' % file_url
      msg_subj = u'%s - %s' % (GC_Values[GC_DOMAIN], list_type)
      send_email(msg_subj, msg_txt)
      print msg_txt
    else:
      import webbrowser
      webbrowser.open(file_url)

def flatten_json(structure, key="", path="", flattened=None, listLimit=None):
  if flattened == None:
    flattened = {}
  if not isinstance(structure, (dict, list)):
    flattened[((path + ".") if path else "") + key] = structure
  elif isinstance(structure, list):
    for i, item in enumerate(structure):
      if listLimit and (i >= listLimit):
        break
      flatten_json(item, "%d" % i, ".".join(filter(None, [path, key])), flattened=flattened, listLimit=listLimit)
  else:
    for new_key, value in structure.items():
      if new_key in [u'kind', u'etag']:
        continue
      if value == u'1970-01-01T00:00:00.000Z':
        value = u'Never'
      flatten_json(value, new_key, ".".join(filter(None, [path, key])), flattened=flattened, listLimit=listLimit)
  return flattened

def doPrintUsers():
  cd = buildGAPIObject(u'directory')
  user_fields = [u'primaryEmail',]
  fields = u''
  customer = GC_Values[GC_CUSTOMER_ID]
  domain = None
  query = None
  projection = u'basic'
  customFieldMask = None
  getGroupFeed = getLicenseFeed = email_parts = False
  todrive = False
  viewType = deleted_only = orderBy = sortOrder = None
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'allfields':
      fields = None
      i += 1
    elif sys.argv[i].lower() == u'custom':
      user_fields.append(u'customSchemas')
      if sys.argv[i+1].lower() == u'all':
        projection = u'full'
      else:
        projection = u'custom'
        customFieldMask = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() in [u'deleted_only', u'only_deleted']:
      deleted_only = True
      i += 1
    elif sys.argv[i].lower() == u'orderby':
      orderBy = sys.argv[i+1]
      if orderBy.lower() not in [u'email', u'familyname', u'givenname', u'firstname', u'lastname']:
        print u'ERROR: orderby should be email, familyName or givenName. Got %s' % orderBy
        sys.exit(2)
      elif orderBy.lower() in [u'familyname', u'lastname']:
        orderBy = u'familyName'
      elif orderBy.lower() in [u'givenname', u'firstname']:
        orderBy = u'givenName'
      i += 2
    elif sys.argv[i].lower() == u'userview':
      viewType = u'domain_public'
      i += 1
    elif sys.argv[i].lower() in [u'ascending', u'descending']:
      sortOrder = sys.argv[i].upper()
      i += 1
    elif sys.argv[i].lower() == u'domain':
      domain = sys.argv[i+1]
      customer = None
      i += 2
    elif sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() in [u'firstname', u'givenname', u'lastname', u'familyName', u'fullname', u'name']:
      user_fields.append(u'name')
      i += 1
    elif sys.argv[i].lower() == u'ou':
      user_fields.append(u'orgUnitPath')
      i += 1
    elif sys.argv[i].lower() == u'suspended':
      user_fields.append(u'suspended')
      user_fields.append(u'suspensionReason')
      i += 1
    elif sys.argv[i].lower() == u'ismailboxsetup':
      user_fields.append(u'isMailboxSetup')
      i += 1
    elif sys.argv[i].lower() == u'changepassword':
      user_fields.append(u'changePasswordAtNextLogin')
      i += 1
    elif sys.argv[i].lower() == u'agreed2terms':
      user_fields.append(u'agreedToTerms')
      i += 1
    elif sys.argv[i].lower() == u'admin':
      user_fields.append(u'isAdmin')
      user_fields.append(u'isDelegatedAdmin')
      i += 1
    elif sys.argv[i].lower() == u'gal':
      user_fields.append(u'includeInGlobalAddressList')
      i += 1
    elif sys.argv[i].lower() in ['photo', 'photourl']:
      user_fields.append(u'thumbnailPhotoUrl')
      i += 1
    elif sys.argv[i].lower() == u'id':
      user_fields.append(u'id')
      i += 1
    elif sys.argv[i].lower() == u'creationtime':
      user_fields.append(u'creationTime')
      i += 1
    elif sys.argv[i].lower() == u'lastlogintime':
      user_fields.append(u'lastLoginTime')
      i += 1
    elif sys.argv[i].lower() in [u'nicknames', u'aliases']:
      user_fields.append(u'aliases')
      user_fields.append(u'nonEditableAliases')
      i += 1
    elif sys.argv[i].lower() in [u'im', u'ims']:
      user_fields.append(u'ims')
      i += 1
    elif sys.argv[i].lower() in [u'emails', u'email']:
      user_fields.append(u'emails')
      i += 1
    elif sys.argv[i].lower().replace(u'_', u'') in [u'externalids', u'externalid']:
      user_fields.append(u'externalIds')
      i += 1
    elif sys.argv[i].lower() in [u'relation', u'relations']:
      user_fields.append(u'relations')
      i += 1
    elif sys.argv[i].lower() in [u'address', u'addresses']:
      user_fields.append(u'addresses')
      i += 1
    elif sys.argv[i].lower() in [u'organization', u'organizations']:
      user_fields.append(u'organizations')
      i += 1
    elif sys.argv[i].lower() in [u'phone', u'phones']:
      user_fields.append(u'phones')
      i += 1
    elif sys.argv[i].lower() == u'groups':
      getGroupFeed = True
      i += 1
    elif sys.argv[i].lower() in [u'license', u'licenses', u'licence', u'licences']:
      getLicenseFeed = True
      i += 1
    elif sys.argv[i].lower() in [u'emailpart', u'emailparts', u'username']:
      email_parts = True
      i += 1
    else:
      print 'ERROR: %s is not a valid argument for "gam print users"' % sys.argv[i]
      sys.exit(2)
  if fields != None:
    user_fields = set(user_fields)
    fields = u'nextPageToken,users(%s)' % u','.join(user_fields)
  sys.stderr.write(u"Getting all users in Google Apps account (may take some time on a large account)...\n")
  page_message = u'Got %%total_items%% users: %%first_item%% - %%last_item%%\n'
  all_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            message_attribute=u'primaryEmail', customer=customer, domain=domain, fields=fields,
                            showDeleted=deleted_only, orderBy=orderBy, sortOrder=sortOrder, viewType=viewType,
                            query=query, projection=projection, customFieldMask=customFieldMask, maxResults=GC_Values[GC_USER_MAX_RESULTS])
  titles = [u'primaryEmail',]
  attributes = []
  for user in all_users:
    if email_parts:
      try:
        user_email = user[u'primaryEmail']
        if user_email.find(u'@') != -1:
          user[u'primaryEmailLocal'] = user_email[:user_email.find(u'@')]
          user[u'primaryEmailDomain'] = user_email[user_email.find(u'@')+1:]
      except KeyError:
        pass
    attributes.append(flatten_json(user))
    for item in attributes[-1]:
      if item not in titles:
        titles.append(item)
  titles.remove(u'primaryEmail')
  titles = sorted(titles)
  titles = [u'primaryEmail'] + titles
  header = {}
  for title in titles:
    header[title] = title
  attributes.insert(0, header)
  if getGroupFeed:
    total_users = len(attributes) - 1
    user_count = 1
    titles.append(u'Groups')
    attributes[0].update(Groups=u'Groups')
    for user in attributes[1:]:
      user_email = user[u'primaryEmail']
      sys.stderr.write(u"Getting Group Membership for %s (%s/%s)\r\n" % (user_email, user_count, total_users))
      groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', userKey=user_email)
      grouplist = u''
      for groupname in groups:
        grouplist += groupname[u'email']+' '
      if grouplist[-1:] == u' ':
        grouplist = grouplist[:-1]
      user.update(Groups=grouplist)
      user_count += 1
  if getLicenseFeed:
    titles.append(u'Licenses')
    attributes[0].update(Licenses=u'Licenses')
    licenses = doPrintLicenses(return_list=True)
    if len(licenses) > 1:
      for user in attributes[1:]:
        user_licenses = []
        for u_license in licenses:
          if u_license[u'userId'].lower() == user[u'primaryEmail'].lower():
            user_licenses.append(u_license[u'skuId'])
        user.update(Licenses=u' '.join(user_licenses))
  output_csv(attributes, titles, u'Users', todrive)

def doPrintGroups():
  cd = buildGAPIObject(u'directory')
  i = 3
  printname = printdesc = printid = members = owners = managers = settings = admin_created = aliases = todrive = False
  customer = GC_Values[GC_CUSTOMER_ID]
  usedomain = usemember = None
  listDelimiter = u'\n'
  group_attributes = [{u'Email': u'Email'}]
  titles = [u'Email']
  fields = u'nextPageToken,groups(email)'
  maxResults = None
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'domain':
      usedomain = sys.argv[i+1].lower()
      customer = None
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'maxresults':
      maxResults = int(sys.argv[i+1])
      i += 2
    elif sys.argv[i].lower() == u'delimiter':
      listDelimiter = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'member':
      usemember = sys.argv[i+1].lower()
      customer = None
      i += 2
    elif sys.argv[i].lower() == u'name':
      fields += u',groups(name)'
      printname = True
      group_attributes[0].update(Name=u'Name')
      titles.append(u'Name')
      i += 1
    elif sys.argv[i].lower() == u'admincreated':
      fields += u',groups(adminCreated)'
      admin_created = True
      group_attributes[0].update(Admin_Created=u'Admin_Created')
      titles.append(u'Admin_Created')
      i += 1
    elif sys.argv[i].lower() == u'description':
      fields += u',groups(description)'
      group_attributes[0].update(Description=u'Description')
      titles.append(u'Description')
      printdesc = True
      i += 1
    elif sys.argv[i].lower() == u'id':
      fields += u',groups(id)'
      group_attributes[0].update(ID=u'ID')
      titles.append(u'ID')
      printid = True
      i += 1
    elif sys.argv[i].lower() == u'aliases':
      fields += u',groups(aliases,nonEditableAliases)'
      group_attributes[0].update(Aliases=u'Aliases')
      group_attributes[0].update(NonEditableAliases=u'NonEditableAliases')
      titles.append(u'Aliases')
      titles.append(u'NonEditableAliases')
      aliases = True
      i += 1
    elif sys.argv[i].lower() == u'members':
      group_attributes[0].update(Members=u'Members')
      titles.append(u'Members')
      members = True
      i += 1
    elif sys.argv[i].lower() == u'owners':
      group_attributes[0].update(Owners=u'Owners')
      titles.append(u'Owners')
      owners = True
      i += 1
    elif sys.argv[i].lower() == u'managers':
      group_attributes[0].update(Managers=u'Managers')
      titles.append(u'Managers')
      managers = True
      i += 1
    elif sys.argv[i].lower() == u'settings':
      settings = True
      i += 1
    else:
      print 'ERROR: %s is not a valid argument for "gam print groups"' % sys.argv[i]
      sys.exit(2)
  sys.stderr.write(u"Retrieving All Groups for Google Apps account (may take some time on a large account)...\n")
  page_message = u'Got %%num_items%% groups: %%first_item%% - %%last_item%%\n'
  all_groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', page_message=page_message, maxResults=maxResults,
                             message_attribute=u'email', customer=customer, domain=usedomain, userKey=usemember, fields=fields)
  total_groups = len(all_groups)
  count = 0
  for group_vals in all_groups:
    count += 1
    group = {}
    group.update({u'Email': group_vals[u'email']})
    if printname:
      try:
        group.update({u'Name': group_vals[u'name']})
      except KeyError:
        pass
    if printdesc:
      try:
        group.update({u'Description': group_vals[u'description']})
      except KeyError:
        pass
    if printid:
      try:
        group.update({u'ID': group_vals[u'id']})
      except KeyError:
        pass
    if admin_created:
      try:
        group.update({u'Admin_Created': group_vals[u'adminCreated']})
      except KeyError:
        pass
    if aliases:
      try:
        group.update({u'Aliases': ' '.join(group_vals[u'aliases'])})
      except KeyError:
        pass
      try:
        group.update({u'NonEditableAliases': ' '.join(group_vals[u'nonEditableAliases'])})
      except KeyError:
        pass
    if members or owners or managers:
      roles = list()
      if members:
        roles.append(u'members')
      if owners:
        roles.append(u'owners')
      if managers:
        roles.append(u'managers')
      roles = u','.join(roles)
      sys.stderr.write(u' Getting %s for %s (%s of %s)\n' % (roles, group_vals[u'email'], count, total_groups))
      page_message = u'Got %%num_items%% members: %%first_item%% - %%last_item%%\n'
      all_group_members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', page_message=page_message,
                                        message_attribute=u'email', groupKey=group_vals[u'email'], roles=roles, fields=u'nextPageToken,members(email,role)')
      if members:
        all_true_members = list()
      if managers:
        all_managers = list()
      if owners:
        all_owners = list()
      for member in all_group_members:
        try:
          member_email = member[u'email']
        except KeyError:
          sys.stderr.write(u' Not sure to do with: %s' % member)
          continue
        try:
          if members and member[u'role'] == u'MEMBER':
            all_true_members.append(member_email)
          elif managers and member[u'role'] == u'MANAGER':
            all_managers.append(member_email)
          elif owners and member[u'role'] == u'OWNER':
            all_owners.append(member_email)
        except KeyError:
          all_true_members.append(member_email)
      if members:
        group.update({u'Members': listDelimiter.join(all_true_members)})
      if managers:
        group.update({u'Managers': listDelimiter.join(all_managers)})
      if owners:
        group.update({u'Owners': listDelimiter.join(all_owners)})
    if settings:
      sys.stderr.write(u" Retrieving Settings for group %s (%s of %s)...\r\n" % (group_vals[u'email'], count, total_groups))
      gs = buildGAPIObject(u'groupssettings')
      settings = callGAPI(service=gs.groups(), function=u'get', retry_reasons=[u'serviceLimit'], groupUniqueId=group_vals[u'email'])
      for key in settings:
        if key in [u'email', u'name', u'description', u'kind', u'etag']:
          continue
        setting_value = settings[key]
        if setting_value == None:
          setting_value = u''
        if key not in titles:
          group_attributes[0][key] = key
          titles.append(key)
        group.update({key: setting_value})
    group_attributes.append(group)
  output_csv(group_attributes, titles, u'Groups', todrive)

def doPrintOrgs():
  cd = buildGAPIObject(u'directory')
  i = 3
  printname = printdesc = printparent = printinherit = todrive = False
  listType = u'all'
  orgUnitPath = u"/"
  org_attributes = [{}]
  fields = u'organizationUnits(orgUnitPath)'
  titles = []
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'allfields':
      fields = None
      i += 1
    elif sys.argv[i].lower() == u'name':
      printname = True
      org_attributes[0].update(Name=u'Name')
      fields += u',organizationUnits(name)'
      titles.append(u'Name')
      i += 1
    elif sys.argv[i].lower() == u'toplevelonly':
      listType = u'children'
      i += 1
    elif sys.argv[i].lower() == u'from_parent':
      orgUnitPath = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'description':
      printdesc = True
      fields += u',organizationUnits(description)'
      org_attributes[0].update(Description=u'Description')
      titles.append(u'Description')
      i += 1
    elif sys.argv[i].lower() == u'parent':
      printparent = True
      fields += u',organizationUnits(parentOrgUnitPath)'
      org_attributes[0].update(Parent=u'Parent')
      titles.append(u'Parent')
      i += 1
    elif sys.argv[i].lower() == u'inherit':
      printinherit = True
      fields += u',organizationUnits(blockInheritance)'
      org_attributes[0].update(InheritanceBlocked=u'InheritanceBlocked')
      titles.append(u'InheritanceBlocked')
      i += 1
    else:
      print 'ERROR: %s is not a valid argument for "gam print orgs"' % sys.argv[i]
      sys.exit(2)
  if fields:
    org_attributes[0][u'Path'] = u'Path'
    titles.append(u'Path')
  sys.stderr.write(u"Retrieving All Organizational Units for your account (may take some time on large domain)...")
  orgs = callGAPI(service=cd.orgunits(), function=u'list', customerId=GC_Values[GC_CUSTOMER_ID], fields=fields, type=listType, orgUnitPath=orgUnitPath)
  sys.stderr.write(u"done\n")
  if not u'organizationUnits' in orgs:
    print u'0 org units in this Google Apps instance...'
    return
  for org_vals in orgs[u'organizationUnits']:
    orgUnit = {}
    if not fields:
      orgUnit = flatten_json(org_vals)
      for row in orgUnit:
        if row not in titles:
          titles.append(row)
          org_attributes[0][row] = row
    else:
      orgUnit.update({u'Path': org_vals[u'orgUnitPath']})
      if printname:
        name = org_vals[u'name']
        if name == None:
          name = u''
        orgUnit.update({u'Name': name})
      if printdesc:
        try:
          desc = org_vals[u'description']
          if desc == None:
            desc = u''
        except KeyError:
          pass
        orgUnit.update({u'Description': desc})
      if printparent:
        parent = org_vals[u'parentOrgUnitPath']
        if parent == None:
          parent = ''
        orgUnit.update({u'Parent': parent})
      if printinherit:
        try:
          orgUnit.update({u'InheritanceBlocked': org_vals[u'blockInheritance']})
        except KeyError:
          pass
    org_attributes.append(orgUnit)
  output_csv(org_attributes, titles, u'Orgs', todrive)

def doPrintAliases():
  cd = buildGAPIObject(u'directory')
  todrive = False
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    else:
      print u'ERROR: %s is not a valid argument for "gam print aliases"' % sys.argv[i]
      sys.exit(2)
  alias_attributes = []
  alias_attributes.append({u'Alias': u'Alias'})
  alias_attributes[0].update(Target=u'Target')
  alias_attributes[0].update(TargetType=u'TargetType')
  titles = [u'Alias', u'Target', u'TargetType']
  sys.stderr.write(u"Retrieving All User Aliases for %s organization (may take some time on large domain)...\n" % GC_Values[GC_DOMAIN])
  page_message = u'Got %%num_items%% users %%first_item%% - %%last_item%%\n'
  all_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            message_attribute=u'primaryEmail', customer=GC_Values[GC_CUSTOMER_ID],
                            fields=u'users(primaryEmail,aliases),nextPageToken', maxResults=GC_Values[GC_USER_MAX_RESULTS])
  for user in all_users:
    try:
      for alias in user[u'aliases']:
        alias_attributes.append({u'Alias': alias, u'Target': user[u'primaryEmail'], u'TargetType': u'User'})
    except KeyError:
      continue
  sys.stderr.write(u"Retrieving All User Aliases for %s organization (may take some time on large domain)...\n" % GC_Values[GC_DOMAIN])
  page_message = u'Got %%num_items%% groups %%first_item%% - %%last_item%%\n'
  all_groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', page_message=page_message,
                             message_attribute=u'email', customer=GC_Values[GC_CUSTOMER_ID],
                             fields=u'groups(email,aliases),nextPageToken')
  for group in all_groups:
    try:
      for alias in group[u'aliases']:
        alias_attributes.append({u'Alias': alias, u'Target': group[u'email'], u'TargetType': u'Group'})
    except KeyError:
      continue
  output_csv(alias_attributes, titles, u'Aliases', todrive)

def doPrintGroupMembers():
  cd = buildGAPIObject(u'directory')
  todrive = all_groups = False
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'group':
      all_groups = [{u'email': sys.argv[i+1].lower()}]
      i += 2
    else:
      print 'ERROR: %s is not a valid argument for "gam print group-members"' % sys.argv[i]
      sys.exit(2)
  member_attributes = [{u'group': u'group'},]
  if not all_groups:
    all_groups = callGAPIpages(service=cd.groups(), function=u'list', items=u'groups', message_attribute=u'email',
                               customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,groups(email)')
  total_groups = len(all_groups)
  i = 1
  for group in all_groups:
    group_email = group[u'email']
    sys.stderr.write(u'Getting members for %s (%s/%s)\n' % (group_email, i, total_groups))
    group_members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', message_attribute=u'email', groupKey=group_email)
    for member in group_members:
      member_attr = {u'group': group_email}
      for title in member:
        if title in [u'kind', u'etag']:
          continue
        try:
          member_attributes[0][title]
        except KeyError:
          member_attributes[0][title] = title
        member_attr[title] = member[title]
      member_attributes.append(member_attr)
    i += 1
  titles = member_attributes[0].keys()
  output_csv(member_attributes, titles, u'Group Members', todrive)

def doPrintMobileDevices():
  cd = buildGAPIObject(u'directory')
  mobile_attributes = [{}]
  titles = []
  todrive = False
  query = orderBy = sortOrder = None
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'query':
      query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'orderby':
      orderBy = sys.argv[i+1].lower()
      allowed_values = [u'deviceid', u'email', u'lastsync', u'model', u'name', u'os', u'status', u'type']
      if orderBy.lower() not in allowed_values:
        print u'ERROR: orderBy must be one of %s. Got %s' % (u', '.join(allowed_values), orderBy)
        sys.exit(2)
      elif orderBy == u'lastsync':
        orderBy = u'lastSync'
      elif orderBy == u'deviceid':
        orderBy = u'deviceId'
      i += 2
    elif sys.argv[i].lower() in [u'ascending', u'descending']:
      sortOrder = sys.argv[i].upper()
      i += 1
    else:
      print 'ERROR: %s is not a valid argument for "gam print mobile"' % sys.argv[i]
      sys.exit(2)
  sys.stderr.write(u'Retrieving All Mobile Devices for organization (may take some time for large accounts)...\n')
  page_message = u'Got %%num_items%% mobile devices...\n'
  all_mobile = callGAPIpages(service=cd.mobiledevices(), function=u'list', items=u'mobiledevices', page_message=page_message,
                             customerId=GC_Values[GC_CUSTOMER_ID], query=query,
                             orderBy=orderBy, sortOrder=sortOrder, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
  for mobile in all_mobile:
    mobiledevice = dict()
    for title in mobile:
      try:
        if title in [u'kind', u'etag', u'applications']:
          continue
        try:
          mobile_attributes[0][title]
        except KeyError:
          mobile_attributes[0][title] = title
          titles.append(title)
        if title in [u'name', u'email']:
          mobiledevice[title] = mobile[title][0]
        else:
          mobiledevice[title] = mobile[title]
      except KeyError:
        pass
    mobile_attributes.append(mobiledevice)
  output_csv(mobile_attributes, titles, u'Mobile', todrive)

def doPrintCrosDevices():
  cd = buildGAPIObject(u'directory')
  cros_attributes = [{u'deviceId': u'deviceId'}]
  titles = [u'deviceId',]
  todrive = False
  query = projection = orderBy = sortOrder = None
  noLists = False
  listLimit = selectAttrib = None
  i = 3
  while i < len(sys.argv):
    my_arg = sys.argv[i].lower().replace(u'_', u'')
    if my_arg == u'query':
      query = sys.argv[i+1]
      i += 2
    elif my_arg == u'todrive':
      todrive = True
      i += 1
    elif my_arg == u'nolists':
      noLists = True
      selectAttrib = None
      i += 1
    elif my_arg == u'recentusers':
      selectAttrib = u'recentUsers'
      noLists = False
      i += 1
    elif my_arg in [u'timeranges', u'activetimeranges']:
      selectAttrib = u'activeTimeRanges'
      noLists = False
      i += 1
    elif my_arg == u'listlimit':
      listLimit = int(sys.argv[i+1])
      i += 2
    elif my_arg == u'orderby':
      orderBy = sys.argv[i+1].lower().replace(u'_', u'')
      allowed_values = [u'location', u'user', u'lastsync', u'notes', u'serialnumber', u'status', u'supportenddate']
      if orderBy not in allowed_values:
        print u'ERROR: orderBy must be one of %s. Got %s' % (u', '.join(allowed_values), orderBy)
        sys.exit(2)
      elif orderBy == u'location':
        orderBy = u'annotatedLocation'
      elif orderBy == u'user':
        orderBy = u'annotatedUser'
      elif orderBy == u'lastsync':
        orderBy = u'lastSync'
      elif orderBy == u'serialnumber':
        orderBy = u'serialNumber'
      elif orderBy == u'supportEndDate':
        orderBy = u'supportEndDate'
      i += 2
    elif my_arg in [u'ascending', u'descending']:
      sortOrder = my_arg.upper()
      i += 1
    elif my_arg in [u'basic', u'full']:
      projection = my_arg.upper()
      i += 1
    else:
      print 'ERROR: %s is not a valid argument for "gam print cros"' % sys.argv[i]
      sys.exit(2)
  if selectAttrib:
    projection = u'FULL'
  sys.stderr.write(u'Retrieving All Chrome OS Devices for organization (may take some time for large accounts)...\n')
  page_message = u'Got %%num_items%% Chrome devices...\n'
  all_cros = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices', page_message=page_message,
                           query=query, customerId=GC_Values[GC_CUSTOMER_ID], projection=projection,
                           orderBy=orderBy, sortOrder=sortOrder, maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
  if all_cros:
    if (not noLists) and (not selectAttrib):
      for cros in all_cros:
        cros_attributes.append(flatten_json(cros, listLimit=listLimit))
        for item in cros_attributes[-1]:
          if item not in cros_attributes[0]:
            cros_attributes[0][item] = item
            titles.append(item)
    else:
      attribMap = dict()
      for cros in all_cros:
        row = dict()
        for attrib in cros:
          if attrib in [u'kind', u'etag', u'recentUsers', u'activeTimeRanges']:
            continue
          if attrib not in cros_attributes[0]:
            cros_attributes[0][attrib] = attrib
            titles.append(attrib)
          row[attrib] = cros[attrib]
        if noLists or (selectAttrib not in cros) or (not cros[selectAttrib]):
          cros_attributes.append(row)
        else:
          if not attribMap:
            for attrib in cros[selectAttrib][0]:
              xattrib = u'%s.%s' % (selectAttrib, attrib)
              if xattrib not in cros_attributes[0]:
                cros_attributes[0][xattrib] = xattrib
                titles.append(xattrib)
              attribMap[attrib] = xattrib
          for i, item in enumerate(cros[selectAttrib]):
            if listLimit and(i >= listLimit):
              break
            new_row = row.copy()
            for attrib in item:
              if isinstance(item[attrib], (bool, int)):
                new_row[attribMap[attrib]] = str(item[attrib])
              else:
                new_row[attribMap[attrib]] = item[attrib]
            cros_attributes.append(new_row)
  output_csv(cros_attributes, titles, 'CrOS', todrive)

def doPrintLicenses(return_list=False, skus=None):
  lic = buildGAPIObject(u'licensing')
  products = [u'Google-Apps', u'Google-Vault']
  licenses = []
  lic_attributes = [{}]
  todrive = False
  i = 3
  while i < len(sys.argv) and not return_list:
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() in [u'products', u'product']:
      products = sys.argv[i+1].split(',')
      i += 2
    elif sys.argv[i].lower() in [u'sku', u'skus']:
      skus = sys.argv[i+1].split(',')
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam print licenses"' % sys.argv[i]
      sys.exit(2)
  if skus:
    for sku in skus:
      product, sku = getProductAndSKU(sku)
      page_message = u'Got %%%%total_items%%%% Licenses for %s...\n' % sku
      try:
        licenses += callGAPIpages(service=lic.licenseAssignments(), function=u'listForProductAndSku', throw_reasons=[u'invalid', u'forbidden'], page_message=page_message,
                                  customerId=GC_Values[GC_DOMAIN], productId=product, skuId=sku, fields=u'items(productId,skuId,userId),nextPageToken')
      except googleapiclient.errors.HttpError:
        licenses += []
  else:
    for productId in products:
      page_message = u'Got %%%%total_items%%%% Licenses for %s...\n' % productId
      try:
        licenses += callGAPIpages(service=lic.licenseAssignments(), function=u'listForProduct', throw_reasons=[u'invalid', u'forbidden'], page_message=page_message,
                                  customerId=GC_Values[GC_DOMAIN], productId=productId, fields=u'items(productId,skuId,userId),nextPageToken')
      except googleapiclient.errors.HttpError:
        licenses = +[]
  for u_license in licenses:
    a_license = dict()
    for title in u_license:
      if title in [u'kind', u'etags', u'selfLink']:
        continue
      if title not in lic_attributes[0]:
        lic_attributes[0][title] = title
      a_license[title] = u_license[title]
    lic_attributes.append(a_license)
  if return_list:
    return lic_attributes
  output_csv(lic_attributes, lic_attributes[0], u'Licenses', todrive)

def doPrintTokens():
  cd = buildGAPIObject(u'directory')
  todrive = False
  i = 3
  entity_type = u'all'
  entity = u'users'
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() in usergroup_types:
      entity_type = sys.argv[i].lower()
      entity = sys.argv[i+1].lower()
      i += 2
    else:
      print u'ERROR: %s is not a valid argument for "gam print tokens"' % sys.argv[i]
      sys.exit(2)
  all_users = getUsersToModify(entity_type=entity_type, entity=entity, silent=False)
  titles = [u'user', u'displayText', u'clientId', u'nativeApp', u'anonymous', u'scopes']
  token_attributes = [{}]
  for title in titles:
    token_attributes[0][title] = title
  for user in all_users:
    sys.stderr.write(u' getting tokens for %s\n' % user)
    user_tokens = callGAPI(service=cd.tokens(), function='list', userKey=user)
    try:
      for user_token in user_tokens[u'items']:
        this_token = dict()
        this_token[u'user'] = user
        this_token[u'scopes'] = ' '.join(user_token[u'scopes'])
        for token_item in user_token:
          if token_item in [u'kind', u'etag', u'scopes']:
            continue
          this_token[token_item] = user_token[token_item]
          if token_item not in titles:
            titles.append(token_item)
            token_attributes[0][token_item] = token_item
        token_attributes.append(this_token)
    except KeyError:
      pass
  output_csv(token_attributes, titles, u'OAuth Tokens', todrive)

def doPrintResourceCalendars():
  cd = buildGAPIObject(u'directory')
  todrive = False
  fields = [u'resourceId', u'resourceName', u'resourceEmail']
  i = 3
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'allfields':
      fields = None
      i += 1
    elif sys.argv[i].lower() == u'todrive':
      todrive = True
      i += 1
    elif sys.argv[i].lower() == u'id':
      i += 1
    elif sys.argv[i].lower() == u'description':
      fields.append(u'resourceDescription')
      i += 1
    elif sys.argv[i].lower() == u'email':
      i += 1
    elif sys.argv[i].lower() == u'type':
      fields.append(u'resourceType')
      i += 1
    else:
      print 'ERROR: %s is not a valid argument for "gam print resources"' % sys.argv[i]
      sys.exit(2)
  if fields:
    fields = u'nextPageToken,items(%s)' % u','.join(fields)
  sys.stderr.write(u"Retrieving All Resource Calendars for your account (may take some time on a large domain)\n")
  page_message = u'Got %%total_items%% resources: %%first_item%% - %%last_item%%\n'
  resources = callGAPIpages(service=cd.resources().calendars(), function=u'list', items=u'items',
                            page_message=page_message, message_attribute=u'resourceId',
                            customer=GC_Values[GC_CUSTOMER_ID], fields=fields, maxResults=500)
  resources_attrib = [{u'resourceId':u'resourceId',
                       u'resourceEmail': u'resourceEmail',
                       u'resourceName': u'resourceName'}]
  for resource in resources:
    resource_attrib = {}
    for key, value in resource.items():
      if key in [u'kind', u'etags']:
        continue
      if key not in resources_attrib[0]:
        resources_attrib[0][key] = key
      resource_attrib[key] = value
    resources_attrib.append(resource_attrib)
  output_csv(resources_attrib, resources_attrib[0], u'Resources', todrive)

def doCreateMonitor():
  source_user = sys.argv[4].lower()
  destination_user = sys.argv[5].lower()
  #end_date defaults to 30 days in the future...
  end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime(u"%Y-%m-%d %H:%M")
  begin_date = None
  incoming_headers_only = outgoing_headers_only = drafts_headers_only = chats_headers_only = False
  drafts = chats = True
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'end':
      end_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'begin':
      begin_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'incoming_headers':
      incoming_headers_only = True
      i += 1
    elif sys.argv[i].lower() == u'outgoing_headers':
      outgoing_headers_only = True
      i += 1
    elif sys.argv[i].lower() == u'nochats':
      chats = False
      i += 1
    elif sys.argv[i].lower() == u'nodrafts':
      drafts = False
      i += 1
    elif sys.argv[i].lower() == u'chat_headers':
      chats_headers_only = True
      i += 1
    elif sys.argv[i].lower() == u'draft_headers':
      drafts_headers_only = True
      i += 1
    else:
      print 'ERROR: %s is not a valid argument for "gam create monitor"' % sys.argv[i]
      sys.exit(2)
  audit = getAuditObject()
  if source_user.find('@') > 0:
    audit.domain = source_user[source_user.find(u'@')+1:]
    source_user = source_user[:source_user.find(u'@')]
  callGData(service=audit, function=u'createEmailMonitor', source_user=source_user, destination_user=destination_user, end_date=end_date, begin_date=begin_date,
            incoming_headers_only=incoming_headers_only, outgoing_headers_only=outgoing_headers_only,
            drafts=drafts, drafts_headers_only=drafts_headers_only, chats=chats, chats_headers_only=chats_headers_only)

def doShowMonitors():
  user = sys.argv[4].lower()
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  results = callGData(service=audit, function=u'getEmailMonitors', user=user)
  print sys.argv[4].lower()+u' has the following monitors:'
  print u''
  for monitor in results:
    print u' Destination: '+monitor['destUserName']
    try:
      print u'  Begin: '+monitor['beginDate']
    except KeyError:
      print u'  Begin: immediately'
    print u'  End: '+monitor['endDate']
    print u'  Monitor Incoming: '+monitor['outgoingEmailMonitorLevel']
    print u'  Monitor Outgoing: '+monitor['incomingEmailMonitorLevel']
    print u'  Monitor Chats: '+monitor['chatMonitorLevel']
    print u'  Monitor Drafts: '+monitor['draftMonitorLevel']
    print u''

def doDeleteMonitor():
  source_user = sys.argv[4].lower()
  destination_user = sys.argv[5].lower()
  audit = getAuditObject()
  if source_user.find(u'@') > 0:
    audit.domain = source_user[source_user.find(u'@')+1:]
    source_user = source_user[:source_user.find(u'@')]
  callGData(service=audit, function=u'deleteEmailMonitor', source_user=source_user, destination_user=destination_user)

def doRequestActivity():
  user = sys.argv[4].lower()
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find('@')]
  results = callGData(service=audit, function=u'createAccountInformationRequest', user=user)
  print u'Request successfully submitted:'
  print u' Request ID: '+results[u'requestId']
  print u' User: '+results[u'userEmailAddress']
  print u' Status: '+results[u'status']
  print u' Request Date: '+results[u'requestDate']
  print u' Requested By: '+results[u'adminEmailAddress']

def doStatusActivityRequests():
  audit = getAuditObject()
  try:
    user = sys.argv[4].lower()
    if user.find(u'@') > 0:
      audit.domain = user[user.find('@')+1:]
      user = user[:user.find(u'@')]
    request_id = sys.argv[5].lower()
    results = callGData(service=audit, function=u'getAccountInformationRequestStatus', user=user, request_id=request_id)
    print u''
    print u'  Request ID: '+results[u'requestId']
    print u'  User: '+results[u'userEmailAddress']
    print u'  Status: '+results[u'status']
    print u'  Request Date: '+results[u'requestDate']
    print u'  Requested By: '+results[u'adminEmailAddress']
    try:
      print u'  Number Of Files: '+results[u'numberOfFiles']
      for i in range(int(results[u'numberOfFiles'])):
        print u'  Url%s: %s' % (i, results[u'fileUrl%s' % i])
    except KeyError:
      pass
    print u''
  except IndexError:
    results = callGData(service=audit, function=u'getAllAccountInformationRequestsStatus')
    print u'Current Activity Requests:'
    print u''
    for request in results:
      print u' Request ID: '+request[u'requestId']
      print u'  User: '+request[u'userEmailAddress']
      print u'  Status: '+request[u'status']
      print u'  Request Date: '+request[u'requestDate']
      print u'  Requested By: '+request[u'adminEmailAddress']
      try:
        print u'  Number Of Files: '+request[u'numberOfFiles']
        for i in range(int(request[u'numberOfFiles'])):
          print u'  Url%s: %s' % (i, request[u'fileUrl%s' % i])
      except KeyError:
        pass
      print u''

def doDownloadActivityRequest():
  user = sys.argv[4].lower()
  request_id = sys.argv[5].lower()
  audit = getAuditObject()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  results = callGData(service=audit, function=u'getAccountInformationRequestStatus', user=user, request_id=request_id)
  if results[u'status'] != u'COMPLETED':
    systemErrorExit(4, MESSAGE_REQUEST_NOT_COMPLETE.format(results[u'status']))
  if int(results.get(u'numberOfFiles', u'0')) < 1:
    systemErrorExit(4, MESSAGE_REQUEST_COMPLETED_NO_FILES)
  for i in range(0, int(results[u'numberOfFiles'])):
    url = results[u'fileUrl'+str(i)]
    filename = u'activity-'+user+'-'+request_id+'-'+unicode(i)+u'.txt.gpg'
    print u'Downloading '+filename+u' ('+unicode(i+1)+u' of '+results[u'numberOfFiles']+')'
    geturl(url, filename)

def doRequestExport():
  begin_date = end_date = search_query = None
  headers_only = include_deleted = False
  user = sys.argv[4].lower()
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == u'begin':
      begin_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'end':
      end_date = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'search':
      search_query = sys.argv[i+1]
      i += 2
    elif sys.argv[i].lower() == u'headersonly':
      headers_only = True
      i += 1
    elif sys.argv[i].lower() == u'includedeleted':
      include_deleted = True
      i += 1
    else:
      print 'ERROR: %s is not a valid argument for "gam export request"' % sys.argv[i]
      sys.exit(2)
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  results = callGData(service=audit, function=u'createMailboxExportRequest', user=user, begin_date=begin_date, end_date=end_date, include_deleted=include_deleted,
                      search_query=search_query, headers_only=headers_only)
  print u'Export request successfully submitted:'
  print u' Request ID: '+results['requestId']
  print u' User: '+results['userEmailAddress']
  print u' Status: '+results['status']
  print u' Request Date: '+results['requestDate']
  print u' Requested By: '+results['adminEmailAddress']
  print u' Include Deleted: '+results['includeDeleted']
  print u' Requested Parts: '+results['packageContent']
  try:
    print u' Begin: '+results['beginDate']
  except KeyError:
    print u' Begin: account creation date'
  try:
    print u' End: '+results['endDate']
  except KeyError:
    print u' End: export request date'

def doDeleteExport():
  audit = getAuditObject()
  user = sys.argv[4].lower()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  request_id = sys.argv[5].lower()
  callGData(service=audit, function=u'deleteMailboxExportRequest', user=user, request_id=request_id)

def doDeleteActivityRequest():
  audit = getAuditObject()
  user = sys.argv[4].lower()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  request_id = sys.argv[5].lower()
  callGData(service=audit, function=u'deleteAccountInformationRequest', user=user, request_id=request_id)

def doStatusExportRequests():
  audit = getAuditObject()
  try:
    user = sys.argv[4].lower()
    if user.find(u'@') > 0:
      audit.domain = user[user.find(u'@')+1:]
      user = user[:user.find(u'@')]
    request_id = sys.argv[5].lower()
    results = callGData(service=audit, function=u'getMailboxExportRequestStatus', user=user, request_id=request_id)
    print u''
    print u'  Request ID: '+results[u'requestId']
    print u'  User: '+results[u'userEmailAddress']
    print u'  Status: '+results[u'status']
    print u'  Request Date: '+results[u'requestDate']
    print u'  Requested By: '+results[u'adminEmailAddress']
    print u'  Requested Parts: '+results[u'packageContent']
    try:
      print u'  Request Filter: '+results[u'searchQuery']
    except KeyError:
      print u'  Request Filter: None'
    print u'  Include Deleted: '+results[u'includeDeleted']
    try:
      print u'  Number Of Files: '+results[u'numberOfFiles']
      for i in range(int(results[u'numberOfFiles'])):
        print u'  Url%s: %s' % (i, results[u'fileUrl%s' % i])
    except KeyError:
      pass
  except IndexError:
    results = callGData(service=audit, function=u'getAllMailboxExportRequestsStatus')
    print u'Current Export Requests:'
    print u''
    for request in results:
      print u' Request ID: '+request[u'requestId']
      print u'  User: '+request[u'userEmailAddress']
      print u'  Status: '+request[u'status']
      print u'  Request Date: '+request[u'requestDate']
      print u'  Requested By: '+request[u'adminEmailAddress']
      print u'  Requested Parts: '+request[u'packageContent']
      try:
        print u'  Request Filter: '+request[u'searchQuery']
      except KeyError:
        print u'  Request Filter: None'
      print u'  Include Deleted: '+request[u'includeDeleted']
      try:
        print u'  Number Of Files: '+request[u'numberOfFiles']
      except KeyError:
        pass
      print u''

def doWatchExportRequest():
  audit = getAuditObject()
  user = sys.argv[4].lower()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  request_id = sys.argv[5].lower()
  while True:
    results = callGData(service=audit, function=u'getMailboxExportRequestStatus', user=user, request_id=request_id)
    if results[u'status'] != u'PENDING':
      print u'status is %s. Sending email.' % results[u'status']
      msg_txt = u"\n"
      msg_txt += u"  Request ID: %s\n" % results[u'requestId']
      msg_txt += u"  User: %s\n" % results[u'userEmailAddress']
      msg_txt += u"  Status: %s\n" % results[u'status']
      msg_txt += u"  Request Date: %s\n" % results[u'requestDate']
      msg_txt += u"  Requested By: %s\n" % results[u'adminEmailAddress']
      msg_txt += u"  Requested Parts: %s\n" % results[u'packageContent']
      try:
        msg_txt += u"  Request Filter: %s\n" % results[u'searchQuery']
      except KeyError:
        msg_txt += u"  Request Filter: None\n"
      msg_txt += u"  Include Deleted: %s\n" % results[u'includeDeleted']
      try:
        msg_txt += u"  Number Of Files: %s\n" % results[u'numberOfFiles']
        for i in range(int(results['numberOfFiles'])):
          msg_txt += u"  Url%s: %s\n" % (i, results[u'fileUrl%s' % i])
      except KeyError:
        pass
      msg_subj = u'Export #%s for %s status is %s' % (results[u'requestId'], results[u'userEmailAddress'], results[u'status'])
      send_email(msg_subj, msg_txt)
      break
    else:
      print u'status still PENDING, will check again in 5 minutes...'
      time.sleep(300)

def send_email(msg_subj, msg_txt, msg_rcpt=None):
  from email.mime.text import MIMEText
  gmail = buildGAPIObject(u'gmail')
  sender_email = gmail._http.request.credentials.id_token[u'email']
  if not msg_rcpt:
    msg_rcpt = sender_email
  msg = MIMEText(msg_txt)
  msg[u'Subject'] = msg_subj
  msg[u'From'] = sender_email
  msg[u'To'] = msg_rcpt
  msg_string = msg.as_string()
  msg_raw = base64.urlsafe_b64encode(msg_string)
  callGAPI(service=gmail.users().messages(), function=u'send', userId=sender_email, body={u'raw': msg_raw})

def doDownloadExportRequest():
  user = sys.argv[4].lower()
  request_id = sys.argv[5].lower()
  audit = getAuditObject()
  if user.find(u'@') > 0:
    audit.domain = user[user.find(u'@')+1:]
    user = user[:user.find(u'@')]
  results = callGData(service=audit, function=u'getMailboxExportRequestStatus', user=user, request_id=request_id)
  if results[u'status'] != u'COMPLETED':
    systemErrorExit(4, MESSAGE_REQUEST_NOT_COMPLETE.format(results[u'status']))
  if int(results.get(u'numberOfFiles', u'0')) < 1:
    systemErrorExit(4, MESSAGE_REQUEST_COMPLETED_NO_FILES)
  for i in range(0, int(results['numberOfFiles'])):
    url = results[u'fileUrl'+str(i)]
    filename = u'export-'+user+'-'+request_id+'-'+str(i)+u'.mbox.gpg'
    #don't download existing files. This does not check validity of existing local
    #file so partial/corrupt downloads will need to be deleted manually.
    if os.path.isfile(filename):
      continue
    print u'Downloading '+filename+u' ('+unicode(i+1)+u' of '+results[u'numberOfFiles']+')'
    geturl(url, filename)

def doUploadAuditKey():
  auditkey = sys.stdin.read()
  audit = getAuditObject()
  callGData(service=audit, function=u'updatePGPKey', pgpkey=auditkey)

def getUsersToModify(entity_type=None, entity=None, silent=False, return_uids=False, member_type=None):
  got_uids = False
  if entity_type == None:
    entity_type = sys.argv[1].lower()
  if entity == None:
    entity = sys.argv[2]
  cd = buildGAPIObject(u'directory')
  if entity_type == u'user':
    users = [entity,]
  elif entity_type == u'users':
    users = entity.replace(u',', u' ').split()
  elif entity_type == u'group':
    got_uids = True
    group = entity
    if member_type == None:
      member_type_message = u'all members'
    else:
      member_type_message = u'%ss' % member_type.lower()
    if group.find(u'@') == -1:
      group = u'%s@%s' % (group, GC_Values[GC_DOMAIN])
    page_message = None
    if not silent:
      sys.stderr.write(u"Getting %s of %s (may take some time for large groups)...\n" % (member_type_message, group))
      page_message = u'Got %%%%total_items%%%% %s...' % member_type_message
    members = callGAPIpages(service=cd.members(), function=u'list', items=u'members', page_message=page_message,
                            groupKey=group, roles=member_type, fields=u'nextPageToken,members(email,id)')
    users = []
    for member in members:
      if return_uids:
        users.append(member[u'id'])
      else:
        users.append(member[u'email'])
  elif entity_type in [u'ou', u'org']:
    got_uids = True
    ou = entity
    if ou[0] != u'/':
      ou = u'/%s' % ou
    users = []
    page_message = None
    if not silent:
      sys.stderr.write(u"Getting all users in the Google Apps organization (may take some time on a large domain)...\n")
      page_message = u'Got %%total_items%% users...'
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id,orgUnitPath)',
                            query=u"orgUnitPath='%s'" % ou, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for member in members:
      if ou.lower() != member[u'orgUnitPath'].lower():
        continue
      if return_uids:
        users.append(member[u'id'])
      else:
        users.append(member[u'primaryEmail'])
    if not silent:
      sys.stderr.write(u"%s users are directly in the OU.\n" % len(users))
  elif entity_type in [u'ou_and_children', u'ou_and_child']:
    got_uids = True
    ou = entity
    if ou[0] != u'/':
      ou = u'/%s' % ou
    users = []
    page_message = None
    if not silent:
      sys.stderr.write(u"Getting all users in the Google Apps organization (may take some time on a large domain)...\n")
      page_message = u'Got %%total_items%% users..'
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id)',
                            query=u"orgUnitPath='%s'" % ou, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for member in members:
      if return_uids:
        users.append(member[u'id'])
      else:
        users.append(member[u'primaryEmail'])
    if not silent:
      sys.stderr.write(u"done.\r\n")
  elif entity_type in [u'query',]:
    got_uids = True
    users = []
    if not silent:
      sys.stderr.write(u"Getting all users that match query %s (may take some time on a large domain)...\n" % entity)
    page_message = u'Got %%total_items%% users...'
    members = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                            customer=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,users(primaryEmail,id)',
                            query=entity, maxResults=GC_Values[GC_USER_MAX_RESULTS])
    for member in members:
      if return_uids:
        users.append(member[u'id'])
      else:
        users.append(member[u'primaryEmail'])
    if not silent:
      sys.stderr.write(u"done.\r\n")
  elif entity_type in [u'license', u'licenses', u'licence', u'licences']:
    users = []
    licenses = doPrintLicenses(return_list=True, skus=entity.split(u','))
    for row in licenses[1:]: # skip header
      try:
        users.append(row[u'userId'])
      except KeyError:
        pass
  elif entity_type == u'file':
    users = []
    f = openFile(entity)
    for row in f:
      user = row.strip()
      if user:
        users.append(user)
    closeFile(f)
  elif entity_type in [u'csv', u'csvfile']:
    try:
      (filename, column) = entity.split(u':')
    except ValueError:
      filename = column = None
    if (not filename) or (not column):
      systemErrorExit(2, u'Expected {0} FileName:FieldName'.format(entity_type))
    f = openFile(filename)
    input_file = csv.DictReader(f, restval=u'')
    if column not in input_file.fieldnames:
      systemErrorExit(2, MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS.format(column, ','.join(input_file.fieldnames)))
    users = []
    for row in input_file:
      user = row[column].strip()
      if user:
        users.append(user)
    closeFile(f)
  elif entity_type in [u'courseparticipants', u'teachers', u'students']:
    croom = buildGAPIObject(u'classroom')
    users = []
    if not entity.isdigit() and entity[:2] != u'd:':
      entity = u'd:%s' % entity
    if entity_type in [u'courseparticipants', u'teachers']:
      page_message = u'Got %%total_items%% teachers...'
      teachers = callGAPIpages(service=croom.courses().teachers(), function=u'list', items=u'teachers', page_message=page_message, courseId=entity)
      for teacher in teachers:
        email = teacher[u'profile'].get(u'emailAddress', None)
        if email:
          users.append(email)
    if entity_type in [u'courseparticipants', u'students']:
      page_message = u'Got %%total_items%% students...'
      students = callGAPIpages(service=croom.courses().students(), function=u'list', page_message=page_message, items=u'students', courseId=entity)
      for student in students:
        email = student[u'profile'].get(u'emailAddress', None)
        if email:
          users.append(email)
  elif entity_type == u'all':
    got_uids = True
    users = []
    if entity.lower() == u'users':
      if not silent:
        sys.stderr.write(u"Getting all users in Google Apps account (may take some time on a large account)...\n")
      page_message = u'Got %%total_items%% users...'
      all_users = callGAPIpages(service=cd.users(), function=u'list', items=u'users', page_message=page_message,
                                customer=GC_Values[GC_CUSTOMER_ID],
                                fields=u'nextPageToken,users(primaryEmail,suspended,id)', maxResults=GC_Values[GC_USER_MAX_RESULTS])
      for member in all_users:
        if member[u'suspended'] == False:
          if return_uids:
            users.append(member[u'id'])
          else:
            users.append(member[u'primaryEmail'])
      if not silent:
        sys.stderr.write(u"done getting %s users.\r\n" % len(users))
    elif entity.lower() == u'cros':
      if not silent:
        sys.stderr.write(u"Getting all CrOS devices in Google Apps account (may take some time on a large account)...\n")
      all_cros = callGAPIpages(service=cd.chromeosdevices(), function=u'list', items=u'chromeosdevices',
                               customerId=GC_Values[GC_CUSTOMER_ID], fields=u'nextPageToken,chromeosdevices(deviceId)',
                               maxResults=GC_Values[GC_DEVICE_MAX_RESULTS])
      for member in all_cros:
        users.append(member[u'deviceId'])
      if not silent:
        sys.stderr.write(u"done getting %s CrOS devices.\r\n" % len(users))
    else:
      print 'ERROR: %s is not a valid argument for "gam all"' % entity
      sys.exit(3)
  elif entity_type == u'cros':
    users = entity.replace(u',', u' ').split()
    entity = u'cros'
  else:
    print 'ERROR: %s is not a valid argument for "gam"' % entity_type
    sys.exit(2)
  full_users = list()
  if entity != u'cros' and not got_uids:
    for user in users:
      if user[:4] == u'uid:':
        full_users.append(user[4:])
      elif user.find(u'@') == -1:
        full_users.append(u'%s@%s' % (user, GC_Values[GC_DOMAIN]))
      else:
        full_users.append(user)
  else:
    full_users = users
  if return_uids and not got_uids:
    new_full_users = list()
    for user in full_users:
      user_result = callGAPI(service=cd.users(), function=u'get', userKey=user, fields=u'id')
      new_full_users.append(user_result[u'id'])
    full_users = new_full_users
  return full_users

def OAuthInfo():
  if len(sys.argv) > 3:
    access_token = sys.argv[3]
  else:
    storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
    credentials = storage.get()
    if credentials is None or credentials.invalid:
      doRequestOAuth()
      credentials = storage.get()
    credentials.user_agent = GAM_INFO
    http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
    if credentials.access_token_expired:
      credentials.refresh(http)
    access_token = credentials.access_token
    print u"\nOAuth File: %s" % GC_Values[GC_OAUTH2_TXT]
  oa2 = buildGAPIObject(u'oauth2')
  token_info = callGAPI(service=oa2, function=u'tokeninfo', access_token=access_token)
  print u"Client ID: %s" % token_info[u'issued_to']
  try:
    print u"Secret: %s" % credentials.client_secret
  except UnboundLocalError:
    pass
  print u'Scopes:'
  for scope in token_info[u'scope'].split(u' '):
    print u'  %s' % scope
  try:
    print u'Google Apps Admin: %s' % token_info[u'email']
  except KeyError:
    print u'Google Apps Admin: Unknown'

def doDeleteOAuth():
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  try:
    credentials.revoke_uri = oauth2client.GOOGLE_REVOKE_URI
  except AttributeError:
    systemErrorExit(1, u'Authorization doesn\'t exist')
  http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
  sys.stderr.write(u'This OAuth token will self-destruct in 3...')
  time.sleep(1)
  sys.stderr.write(u'2...')
  time.sleep(1)
  sys.stderr.write(u'1...')
  time.sleep(1)
  sys.stderr.write(u'boom!\n')
  try:
    credentials.revoke(http)
  except oauth2client.client.TokenRevokeError, e:
    stderrErrorMsg(e.message)
    os.remove(GC_Values[GC_OAUTH2_TXT])

class cmd_flags(object):
  def __init__(self, noLocalWebserver):
    self.short_url = True
    self.noauth_local_webserver = noLocalWebserver
    self.logging_level = u'ERROR'
    self.auth_host_name = u'localhost'
    self.auth_host_port = [8080, 9090]

possible_scopes = [u'https://www.googleapis.com/auth/admin.directory.group',            # Groups Directory Scope
                   u'https://www.googleapis.com/auth/admin.directory.orgunit',          # Organization Directory Scope
                   u'https://www.googleapis.com/auth/admin.directory.user',             # Users Directory Scope
                   u'https://www.googleapis.com/auth/admin.directory.device.chromeos',  # Chrome OS Devices Directory Scope
                   u'https://www.googleapis.com/auth/admin.directory.device.mobile',    # Mobile Device Directory Scope
                   u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/',          # Email Settings API
                   u'https://www.googleapis.com/auth/admin.directory.resource.calendar',# Resource Calendar API
                   u'https://apps-apis.google.com/a/feeds/compliance/audit/',           # Email Audit API
                   u'https://apps-apis.google.com/a/feeds/domain/',                     # Admin Settings API
                   u'https://www.googleapis.com/auth/apps.groups.settings',             # Group Settings API
                   u'https://www.googleapis.com/auth/calendar',                         # Calendar Data API
                   u'https://www.googleapis.com/auth/admin.reports.audit.readonly',     # Audit Reports
                   u'https://www.googleapis.com/auth/admin.reports.usage.readonly',     # Usage Reports
                   u'https://www.googleapis.com/auth/drive.file',                       # Drive API - Admin user access to files created or opened by the app
                   u'https://www.googleapis.com/auth/apps.licensing',                   # License Manager API
                   u'https://www.googleapis.com/auth/admin.directory.user.security',    # User Security Directory API
                   u'https://www.googleapis.com/auth/admin.directory.notifications',    # Notifications Directory API
                   u'https://www.googleapis.com/auth/siteverification',                 # Site Verification API
                   u'https://mail.google.com/',                                         # IMAP/SMTP authentication for admin notifications
                   u'https://www.googleapis.com/auth/admin.directory.userschema',       # Customer User Schema
                   u'https://www.googleapis.com/auth/classroom.rosters https://www.googleapis.com/auth/classroom.courses https://www.googleapis.com/auth/classroom.profile.emails https://www.googleapis.com/auth/classroom.profile.photos',           # Classroom API
                   u'https://www.googleapis.com/auth/cloudprint',                       # CloudPrint API
                   u'https://www.googleapis.com/auth/admin.datatransfer',		# Data Transfer API
                   u'https://www.googleapis.com/auth/admin.directory.customer',         # Customer API
                   u'https://www.googleapis.com/auth/admin.directory.domain',           # Domain API
                   u'https://www.googleapis.com/auth/admin.directory.rolemanagement',   # Roles API
                  ]

def doRequestOAuth(incremental_auth=False):
  MISSING_CLIENT_SECRETS_MESSAGE = u"""
WARNING: Please configure OAuth 2.0

To make GAM run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console <https://cloud.google.com/console>.

See:

https://github.com/jay0lee/GAM/wiki/CreatingClientSecretsFile

for instructions.

""" % GC_Values[GC_CLIENT_SECRETS_JSON]
  num_scopes = len(possible_scopes)
  menu = u'''Select the authorized scopes for this token. Include a 'r' to grant read-only
access or an 'a' to grant action-only access.

[%%s]  %s)  Group Directory API (supports read-only)
[%%s]  %s)  Organizational Unit Directory API (supports read-only)
[%%s]  %s)  User Directory API (supports read-only)
[%%s]  %s)  Chrome OS Device Directory API (supports read-only)
[%%s]  %s)  Mobile Device Directory API (supports read-only and action)
[%%s]  %s)  User Email Settings API
[%%s]  %s)  Resource Calendar API (supports read-only)
[%%s]  %s)  Audit Monitors, Activity and Mailbox Exports API
[%%s]  %s)  Admin Settings API
[%%s]  %s)  Groups Settings API
[%%s]  %s)  Calendar Data API (supports read-only)
[%%s]  %s)  Audit Reports API
[%%s]  %s)  Usage Reports API
[%%s]  %s)  Drive API (create report documents for admin user only)
[%%s]  %s)  License Manager API
[%%s]  %s)  User Security Directory API
[%%s]  %s)  Notifications Directory API
[%%s]  %s)  Site Verification API
[%%s]  %s)  IMAP/SMTP Access (send notifications to admin)
[%%s]  %s)  User Schemas (supports read-only)
[%%s]  %s)  Classroom API
[%%s]  %s)  Cloud Print API
[%%s]  %s)  Data Transfer API (supports read-only)
[%%s]  %s)  Customer Directory API (supports read-only)
[%%s]  %s)  Domains Directory API (supports read-only)
[%%s]  %s)  Roles API (supports read-only)

      %%s)  Select all scopes
      %%s)  Unselect all scopes
      %%s)  Continue
''' % tuple(range(0, num_scopes))
  selected_scopes = [u'*'] * num_scopes
  selected_scopes[16] = u' '
  select_all_scopes = unicode(str(num_scopes))
  unselect_all_scopes = unicode(str(num_scopes+1))
  authorize_scopes = unicode(str(num_scopes+2))
  scope_choices = (select_all_scopes, unselect_all_scopes, authorize_scopes)

  os.system([u'clear', u'cls'][os.name == u'nt'])
  while True:
    menu_fill = tuple(selected_scopes) + scope_choices
    selection = raw_input(menu % menu_fill)
    try:
      if selection.lower().find(u'r') != -1:
        selection = int(selection.lower().replace(u'r', u''))
        if selection not in [0, 1, 2, 3, 4, 6, 10, 19, 22, 23, 24, 25]:
          os.system([u'clear', u'cls'][os.name == u'nt'])
          print u'THAT SCOPE DOES NOT SUPPORT READ-ONLY MODE!\n'
          continue
        selected_scopes[selection] = u'R'
      elif selection.lower().find(u'a') != -1:
        selection = int(selection.lower().replace(u'a', u''))
        if selection not in [4,]:
          os.system([u'clear', u'cls'][os.name == u'nt'])
          print u'THAT SCOPE DOES NOT SUPPORT ACTION-ONLY MODE!\n'
          continue
        selected_scopes[selection] = u'A'
      elif int(selection) > -1 and int(selection) < num_scopes:
        if selected_scopes[int(selection)] == u' ':
          selected_scopes[int(selection)] = u'*'
        else:
          selected_scopes[int(selection)] = u' '
      elif selection == select_all_scopes:
        for i in xrange(0, num_scopes):
          selected_scopes[i] = u'*'
      elif selection == unselect_all_scopes:
        for i in xrange(0, num_scopes):
          selected_scopes[i] = u' '
      elif selection == authorize_scopes:
        at_least_one = False
        for i in range(0, len(selected_scopes)):
          if selected_scopes[i] in [u'*', u'R', u'A']:
            at_least_one = True
        if at_least_one:
          break
        else:
          os.system([u'clear', u'cls'][os.name == u'nt'])
          print u"YOU MUST SELECT AT LEAST ONE SCOPE!\n"
          continue
      else:
        os.system([u'clear', u'cls'][os.name == u'nt'])
        print u'NOT A VALID SELECTION!'
        continue
      os.system([u'clear', u'cls'][os.name == u'nt'])
    except ValueError:
      os.system([u'clear', u'cls'][os.name == u'nt'])
      print u'Not a valid selection.'
      continue

  if incremental_auth:
    scopes = []
  else:
    scopes = [u'email',] # Email Display Scope, always included
  for i in range(0, len(selected_scopes)):
    if selected_scopes[i] == u'*':
      scopes.append(possible_scopes[i])
    elif selected_scopes[i] == u'R':
      scopes.append(u'%s.readonly' % possible_scopes[i])
    elif selected_scopes[i] == u'A':
      scopes.append(u'%s.action' % possible_scopes[i])
  try:
    FLOW = oauth2client.client.flow_from_clientsecrets(GC_Values[GC_CLIENT_SECRETS_JSON], scope=scopes)
  except oauth2client.client.clientsecrets.InvalidClientSecretsError:
    systemErrorExit(14, MISSING_CLIENT_SECRETS_MESSAGE)
  storage = oauth2client.file.Storage(GC_Values[GC_OAUTH2_TXT])
  credentials = storage.get()
  flags = cmd_flags(noLocalWebserver=GC_Values[GC_NO_BROWSER])
  if credentials is None or credentials.invalid or incremental_auth:
    http = httplib2.Http(disable_ssl_certificate_validation=GC_Values[GC_NO_VERIFY_SSL])
    try:
      credentials = oauth2client.tools.run_flow(flow=FLOW, storage=storage, flags=flags, http=http)
    except httplib2.CertificateValidationUnsupported:
      noPythonSSLExit()

def batch_worker():
  while True:
    item = GM_Globals[GM_BATCH_QUEUE].get()
    subprocess.call(item, stderr=subprocess.STDOUT)
    GM_Globals[GM_BATCH_QUEUE].task_done()

def run_batch(items):
  import Queue, threading
  total_items = len(items)
  current_item = 0
  python_cmd = [sys.executable.lower(),]
  if not getattr(sys, 'frozen', False): # we're not frozen
    python_cmd.append(os.path.realpath(sys.argv[0]))
  num_worker_threads = min(total_items, GC_Values[GC_NUM_THREADS])
  GM_Globals[GM_BATCH_QUEUE] = Queue.Queue(maxsize=num_worker_threads) # GM_Globals[GM_BATCH_QUEUE].put() gets blocked when trying to create more items than there are workers
  print u'starting %s worker threads...' % num_worker_threads
  for i in range(num_worker_threads):
    t = threading.Thread(target=batch_worker)
    t.daemon = True
    t.start()
  for item in items:
    current_item += 1
    if not current_item % 100:
      print u'starting job %s / %s' % (current_item, total_items)
    if item[0] == u'commit-batch':
      sys.stderr.write(u'commit-batch - waiting for running processes to finish before proceeding...')
      GM_Globals[GM_BATCH_QUEUE].join()
      sys.stderr.write(u'done with commit-batch\n')
      continue
    GM_Globals[GM_BATCH_QUEUE].put(python_cmd+item)
  GM_Globals[GM_BATCH_QUEUE].join()

# Main
reload(sys)
sys.setdefaultencoding(u'UTF-8')
try:
  if GM_Globals[GM_WINDOWS]:
    sys.argv = win32_unicode_argv() # cleanup sys.argv on Windows
  SetGlobalVariables()
  if sys.argv[1].lower() == u'batch':
    import shlex
    f = openFile(sys.argv[2])
    items = list()
    for line in f:
      argv = shlex.split(line)
      if not argv:
        continue
      if (argv[0] in [u'#', u' ', u''] or len(argv) < 2) and argv != [u'commit-batch']:
        continue
      elif argv[0] not in [u'gam', u'commit-batch']:
        print u'ERROR: "%s" is not a valid gam command' % line
        continue
      if argv[0] == u'gam':
        argv = argv[1:]
      items.append(argv)
    closeFile(f)
    run_batch(items)
    sys.exit(0)
  elif sys.argv[1].lower() == u'csv':
    if httplib2.debuglevel > 0:
      print u'Sorry, CSV commands are not compatible with debug. Delete debug.gam and try again.'
      sys.exit(1)
    csv_filename = sys.argv[2]
    f = openFile(csv_filename)
    input_file = csv.DictReader(f)
    if sys.argv[3].lower() != 'gam':
      print 'ERROR: "gam csv <filename>" should be followed by a full GAM command...'
      sys.exit(3)
    argv_template = sys.argv[4:]
    substring_replacements = re.findall(r'~~(.*?)~~', u' '.join(argv_template))
    items = list()
    for row in input_file:
      argv = list()
      for arg in argv_template:
        for substring_replacement in substring_replacements:
          try:
            arg = arg.replace(u'~~%s~~' % substring_replacement, row[substring_replacement])
          except KeyError:
            systemErrorExit(3, u'%s is not in %s' % (substring_replacement, row))
        if arg[0] != '~':
          argv.append(arg)
        elif arg[1:] in row:
          argv.append(row[arg[1:]])
        else:
          systemErrorExit(2, MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS.format(arg[1:], ','.join(row.keys())))
      items.append(argv)
    closeFile(f)
    run_batch(items)
    sys.exit(0)
  elif sys.argv[1].lower() == u'version':
    doGAMVersion()
    sys.exit(0)
  elif sys.argv[1].lower() == u'create':
    if sys.argv[2].lower() == u'user':
      doCreateUser()
    elif sys.argv[2].lower() == u'group':
      doCreateGroup()
    elif sys.argv[2].lower() in [u'nickname', u'alias']:
      doCreateAlias()
    elif sys.argv[2].lower() in [u'org', 'ou']:
      doCreateOrg()
    elif sys.argv[2].lower() == u'resource':
      doCreateResourceCalendar()
    elif sys.argv[2].lower() in [u'verify', u'verification']:
      doSiteVerifyShow()
    elif sys.argv[2].lower() in [u'schema']:
      doCreateOrUpdateUserSchema()
    elif sys.argv[2].lower() in [u'course', u'class']:
      doCreateCourse()
    elif sys.argv[2].lower() in [u'transfer', u'datatransfer']:
      doCreateDataTranfer()
    elif sys.argv[2].lower() in [u'domain',]:
      doCreateDomain()
    elif sys.argv[2].lower() in [u'domainalias', u'aliasdomain']:
      doCreateDomainAlias()
    elif sys.argv[2].lower() in [u'admin']:
      doCreateAdmin()
    else:
      print u'ERROR: %s is not a valid argument for "gam create"' % sys.argv[2]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'update':
    if sys.argv[2].lower() == u'user':
      doUpdateUser([sys.argv[3],])
    elif sys.argv[2].lower() == u'group':
      doUpdateGroup()
    elif sys.argv[2].lower() in [u'nickname', u'alias']:
      doUpdateAlias()
    elif sys.argv[2].lower() in [u'ou', u'org']:
      doUpdateOrg()
    elif sys.argv[2].lower() == u'resource':
      doUpdateResourceCalendar()
    elif sys.argv[2].lower() == u'instance':
      doUpdateInstance()
    elif sys.argv[2].lower() == u'cros':
      doUpdateCros()
    elif sys.argv[2].lower() == u'mobile':
      doUpdateMobile()
    elif sys.argv[2].lower() in [u'notification', u'notifications']:
      doUpdateNotification()
    elif sys.argv[2].lower() in [u'verify', u'verification']:
      doSiteVerifyAttempt()
    elif sys.argv[2].lower() in [u'schema', u'schemas']:
      doCreateOrUpdateUserSchema()
    elif sys.argv[2].lower() in [u'course', u'class']:
      doUpdateCourse()
    elif sys.argv[2].lower() in [u'printer', u'print']:
      doUpdatePrinter()
    elif sys.argv[2].lower() in [u'domain',]:
      doUpdateDomain()
    elif sys.argv[2].lower() in [u'customer',]:
      doUpdateCustomer()
    else:
      print u'ERROR: %s is not a valid argument for "gam update"' % sys.argv[2]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'info':
    if sys.argv[2].lower() == u'user':
      doGetUserInfo()
    elif sys.argv[2].lower() == u'group':
      doGetGroupInfo()
    elif sys.argv[2].lower() in [u'nickname', u'alias']:
      doGetAliasInfo()
    elif sys.argv[2].lower() == u'instance':
      doGetInstanceInfo()
    elif sys.argv[2].lower() in [u'org', u'ou']:
      doGetOrgInfo()
    elif sys.argv[2].lower() == u'resource':
      doGetResourceCalendarInfo()
    elif sys.argv[2].lower() == u'cros':
      doGetCrosInfo()
    elif sys.argv[2].lower() == u'mobile':
      doGetMobileInfo()
    elif sys.argv[2].lower() in [u'notifications', u'notification']:
      doGetNotifications()
    elif sys.argv[2].lower() in [u'verify', u'verification']:
      doGetSiteVerifications()
    elif sys.argv[2].lower() in [u'schema', u'schemas']:
      doGetUserSchema()
    elif sys.argv[2].lower() in [u'course', u'class']:
      doGetCourseInfo()
    elif sys.argv[2].lower() in [u'printer', u'print']:
      doGetPrinterInfo()
    elif sys.argv[2].lower() in [u'transfer', u'datatransfer']:
      doGetDataTransferInfo()
    elif sys.argv[2].lower() in [u'customer',]:
      doGetCustomerInfo()
    elif sys.argv[2].lower() in [u'domain',]:
      doGetDomainInfo()
    elif sys.argv[2].lower() in [u'domainalias', u'aliasdomain']:
      doGetDomainAliasInfo()
    else:
      print u'ERROR: %s is not a valid argument for "gam info"' % sys.argv[2]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'delete':
    if sys.argv[2].lower() == u'user':
      doDeleteUser()
    elif sys.argv[2].lower() == u'group':
      doDeleteGroup()
    elif sys.argv[2].lower() in [u'nickname', u'alias']:
      doDeleteAlias()
    elif sys.argv[2].lower() == u'org':
      doDeleteOrg()
    elif sys.argv[2].lower() == u'resource':
      doDeleteResourceCalendar()
    elif sys.argv[2].lower() == u'mobile':
      doDeleteMobile()
    elif sys.argv[2].lower() in [u'notification', u'notifications']:
      doDeleteNotification()
    elif sys.argv[2].lower() in [u'schema', u'schemas']:
      doDelSchema()
    elif sys.argv[2].lower() in [u'course', u'class']:
      doDelCourse()
    elif sys.argv[2].lower() in [u'printer', u'printers']:
      doDelPrinter()
    elif sys.argv[2].lower() in [u'domain',]:
      doDelDomain()
    elif sys.argv[2].lower() in [u'domainalias',]:
      doDelDomainAlias()
    elif sys.argv[2].lower() in [u'admin',]:
      doDelAdmin()
    else:
      print u'ERROR: %s is not a valid argument for "gam delete"' % sys.argv[2]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'undelete':
    if sys.argv[2].lower() == u'user':
      doUndeleteUser()
    else:
      print u'ERROR: %s is not a valid argument for "gam undelete"' % sys.argv[2]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'audit':
    if sys.argv[2].lower() == u'monitor':
      if sys.argv[3].lower() == u'create':
        doCreateMonitor()
      elif sys.argv[3].lower() == u'list':
        doShowMonitors()
      elif sys.argv[3].lower() == u'delete':
        doDeleteMonitor()
      else:
        print u'ERROR: %s is not a valid argument for "gam audit monitor"' % sys.argv[3]
        sys.exit(2)
    elif sys.argv[2].lower() == u'activity':
      if sys.argv[3].lower() == u'request':
        doRequestActivity()
      elif sys.argv[3].lower() == u'status':
        doStatusActivityRequests()
      elif sys.argv[3].lower() == u'download':
        doDownloadActivityRequest()
      elif sys.argv[3].lower() == u'delete':
        doDeleteActivityRequest()
      else:
        print u'ERROR: %s is not a valid argument for "gam audit activity"' % sys.argv[3]
        sys.exit(2)
    elif sys.argv[2].lower() == u'export':
      if sys.argv[3].lower() == u'status':
        doStatusExportRequests()
      elif sys.argv[3].lower() == u'watch':
        doWatchExportRequest()
      elif sys.argv[3].lower() == u'download':
        doDownloadExportRequest()
      elif sys.argv[3].lower() == u'request':
        doRequestExport()
      elif sys.argv[3].lower() == u'delete':
        doDeleteExport()
      else:
        print u'ERROR: %s is not a valid argument for "gam audit export"' % sys.argv[3]
        sys.exit(2)
    elif sys.argv[2].lower() == u'uploadkey':
      doUploadAuditKey()
    else:
      print u'ERROR: %s is not a valid argument for "gam audit"' % sys.argv[2]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'print':
    if sys.argv[2].lower() == u'users':
      doPrintUsers()
    elif sys.argv[2].lower() == u'nicknames' or sys.argv[2].lower() == u'aliases':
      doPrintAliases()
    elif sys.argv[2].lower() == u'groups':
      doPrintGroups()
    elif sys.argv[2].lower() in [u'group-members', u'groups-members']:
      doPrintGroupMembers()
    elif sys.argv[2].lower() in [u'orgs', u'ous']:
      doPrintOrgs()
    elif sys.argv[2].lower() == u'resources':
      doPrintResourceCalendars()
    elif sys.argv[2].lower() == u'cros':
      doPrintCrosDevices()
    elif sys.argv[2].lower() == u'mobile':
      doPrintMobileDevices()
    elif sys.argv[2].lower() in [u'license', u'licenses', u'licence', u'licences']:
      doPrintLicenses()
    elif sys.argv[2].lower() in [u'token', u'tokens']:
      doPrintTokens()
    elif sys.argv[2].lower() in [u'schema', u'schemas']:
      doPrintUserSchemas()
    elif sys.argv[2].lower() in [u'courses', u'classes']:
      doPrintCourses()
    elif sys.argv[2].lower() in [u'course-participants', u'class-participants']:
      doPrintCourseParticipants()
    elif sys.argv[2].lower() in [u'printers']:
      doPrintPrinters()
    elif sys.argv[2].lower() in [u'printjobs']:
      doPrintPrintJobs()
    elif sys.argv[2].lower() in [u'transfers', u'datatransfers']:
      doPrintDataTransfers()
    elif sys.argv[2].lower() in [u'transferapps']:
      doPrintTransferApps()
    elif sys.argv[2].lower() in [u'domains']:
      doPrintDomains()
    elif sys.argv[2].lower() in [u'admins']:
      doPrintAdmins()
    elif sys.argv[2].lower() in [u'roles', u'adminroles']:
      doPrintAdminRoles()
    else:
      print u'ERROR: %s is not a valid argument for "gam print"' % sys.argv[2]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() in [u'oauth', u'oauth2']:
    if sys.argv[2].lower() in [u'request', u'create']:
      doRequestOAuth()
    elif sys.argv[2].lower() == u'info':
      OAuthInfo()
    elif sys.argv[2].lower() in [u'delete', u'revoke']:
      doDeleteOAuth()
    else:
      print u'ERROR: %s is not a valid argument for "gam oauth"' % sys.argv[2]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'calendar':
    if sys.argv[3].lower() == u'showacl':
      doCalendarShowACL()
    elif sys.argv[3].lower() == u'add':
      doCalendarAddACL()
    elif sys.argv[3].lower() in [u'del', u'delete']:
      doCalendarDelACL()
    elif sys.argv[3].lower() == u'update':
      doCalendarUpdateACL()
    elif sys.argv[3].lower() == u'wipe':
      doCalendarWipeData()
    elif sys.argv[3].lower() == u'addevent':
      doCalendarAddEvent()
    else:
      print u'ERROR: %s is not a valid argument for "gam calendar"' % sys.argv[3]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'printer':
    if sys.argv[3].lower() == u'showacl':
      doPrinterShowACL()
    elif sys.argv[3].lower() == u'add':
      doPrinterAddACL()
    elif sys.argv[3].lower() in [u'del', u'delete', u'remove']:
      doPrinterDelACL()
    elif sys.argv[3].lower() == u'register':
      doPrinterRegister()
    else:
      print u'ERROR: invalid argument for "gam printer..."'
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'printjob':
    if sys.argv[3].lower() == u'delete':
      doDeletePrintJob()
    elif sys.argv[3].lower() == u'cancel':
      doCancelPrintJob()
    elif sys.argv[3].lower() == u'submit':
      doPrintJobSubmit()
    elif sys.argv[3].lower() == u'fetch':
      doPrintJobFetch()
    elif sys.argv[3].lower() == u'resubmit':
      doPrintJobResubmit()
    else:
      print u'ERROR: %s is not a valid argument for "gam printjob"' % sys.argv[3]
      sys.exit(2)
    sys.exit(0)
  elif sys.argv[1].lower() == u'report':
    showReport()
    sys.exit(0)
  elif sys.argv[1].lower() == u'whatis':
    doWhatIs()
    sys.exit(0)
  elif sys.argv[1].lower() in [u'course', u'class']:
    if sys.argv[3].lower() in [u'add', u'create']:
      doAddCourseParticipant()
      sys.exit(0)
    elif sys.argv[3].lower() in [u'del', u'delete', u'remove']:
      doDelCourseParticipant()
      sys.exit(0)
    elif sys.argv[3].lower() == u'sync':
      doSyncCourseParticipants()
      sys.exit(0)
    else:
      print u'ERROR: %s is not a valid argument for "gam course"' % sys.argv[3]
      sys.exit(2)
  users = getUsersToModify()
  command = sys.argv[3].lower()
  if command == u'print':
    for user in users:
      print user
    sys.exit(0)
  try:
    if (GC_Values[GC_AUTO_BATCH_MIN] > 0) and (len(users) > GC_Values[GC_AUTO_BATCH_MIN]):
      items = []
      for user in users:
        items.append([u'user', user] + sys.argv[3:])
      run_batch(items)
      sys.exit(0)
  except TypeError:
    pass
  if command == u'transfer':
    transferWhat = sys.argv[4].lower()
    if transferWhat == u'drive':
      transferDriveFiles(users)
    elif transferWhat == u'seccals':
      transferSecCals(users)
    elif transferWhat == u'folder':
      transferDriveFolder(users)
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> transfer"' % sys.argv[4]
      sys.exit(2)
  elif command == u'claim':
    readWhat = sys.argv[4].lower()
    if readWhat == u'folder':
      claimDriveFolder(users)
  elif command == u'show':
    readWhat = sys.argv[4].lower()
    if readWhat in [u'labels', u'label']:
      showLabels(users)
    elif readWhat == u'profile':
      showProfile(users)
    elif readWhat == u'calendars':
      showCalendars(users)
    elif readWhat == u'calsettings':
      showCalSettings(users)
    elif readWhat == u'drivesettings':
      showDriveSettings(users)
    elif readWhat == u'drivefileacl':
      showDriveFileACL(users)
    elif readWhat == u'filelist':
      showDriveFiles(users)
    elif readWhat == u'filetree':
      showDriveFileTree(users)
    elif readWhat == u'fileinfo':
      showDriveFileInfo(users)
    elif readWhat == u'sendas':
      showSendAs(users)
    elif readWhat == u'gmailprofile':
      showGmailProfile(users)
    elif readWhat in [u'sig', u'signature']:
      getSignature(users)
    elif readWhat == u'forward':
      getForward(users)
    elif readWhat in [u'pop', u'pop3']:
      getPop(users)
    elif readWhat in [u'imap', u'imap4']:
      getImap(users)
    elif readWhat == u'vacation':
      getVacation(users)
    elif readWhat in [u'delegate', u'delegates']:
      getDelegates(users)
    elif readWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
      doGetBackupCodes(users)
    elif readWhat in [u'asp', u'asps', u'applicationspecificpasswords']:
      doGetASPs(users)
    elif readWhat in [u'token', u'tokens', u'oauth', u'3lo']:
      doGetTokens(users)
    elif readWhat in [u'driveactivity']:
      doDriveActivity(users)
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> show"' % sys.argv[4]
      sys.exit(2)
  elif command == u'modify':
    if sys.argv[4].lower() in [u'message', u'messages']:
      doProcessMessages(users, u'modify')
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> modify"' % sys.argv[4]
      sys.exit(2)
  elif command == u'trash':
    if sys.argv[4].lower() in [u'message', u'messages']:
      doProcessMessages(users, u'trash')
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> trash"' % sys.argv[4]
      sys.exit(2)
  elif command == u'untrash':
    if sys.argv[4].lower() in [u'message', u'messages']:
      doProcessMessages(users, u'untrash')
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> untrash"' % sys.argv[4]
      sys.exit(2)
  elif command == u'delete' or command == u'del':
    delWhat = sys.argv[4].lower()
    if delWhat == u'delegate':
      deleteDelegate(users)
    elif delWhat == u'calendar':
      deleteCalendar(users)
    elif delWhat == u'label':
      doDeleteLabel(users)
    elif delWhat in [u'message', u'messages']:
      doProcessMessages(users, u'delete')
    elif delWhat == u'photo':
      deletePhoto(users)
    elif delWhat in [u'license', u'licence']:
      doLicense(users, u'delete')
    elif delWhat in [u'backupcode', u'backupcodes', u'verificationcodes']:
      doDelBackupCodes(users)
    elif delWhat in [u'asp', u'asps', u'applicationspecificpasswords']:
      doDelASP(users)
    elif delWhat in [u'token', u'tokens', u'oauth', u'3lo']:
      doDelTokens(users)
    elif delWhat in [u'group', u'groups']:
      doRemoveUsersGroups(users)
    elif delWhat in [u'alias', u'aliases']:
      doRemoveUsersAliases(users)
    elif delWhat in [u'emptydrivefolders']:
      deleteEmptyDriveFolders(users)
    elif delWhat in [u'drivefile']:
      deleteDriveFile(users)
    elif delWhat in [u'drivefileacl', u'drivefileacls']:
      delDriveFileACL(users)
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> delete"' % sys.argv[4]
      sys.exit(2)
  elif command == u'add':
    addWhat = sys.argv[4].lower()
    if addWhat == u'calendar':
      addCalendar(users)
    elif addWhat == u'drivefile':
      createDriveFile(users)
    elif addWhat in [u'license', u'licence']:
      doLicense(users, u'insert')
    elif addWhat in [u'drivefileacl', u'drivefileacls']:
      addDriveFileACL(users)
    elif addWhat in [u'label', u'labels']:
      doLabel(users)
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> add"' % sys.argv[4]
      sys.exit(2)
  elif command == u'update':
    if sys.argv[4].lower() == u'calendar':
      updateCalendar(users)
    elif sys.argv[4].lower() == u'calattendees':
      changeCalendarAttendees(users)
    elif sys.argv[4].lower() == u'photo':
      doPhoto(users)
    elif sys.argv[4].lower() in [u'license', u'licence']:
      doLicense(users, u'patch')
    elif sys.argv[4].lower() == u'user':
      doUpdateUser(users)
    elif sys.argv[4].lower() in [u'backupcode', u'backupcodes', u'verificationcodes']:
      doGenBackupCodes(users)
    elif sys.argv[4].lower() in [u'drivefile']:
      doUpdateDriveFile(users)
    elif sys.argv[4].lower() in [u'drivefileacls', u'drivefileacl']:
      updateDriveFileACL(users)
    elif sys.argv[4].lower() in [u'label', u'labels']:
      renameLabels(users)
    elif sys.argv[4].lower() in [u'labelsettings']:
      updateLabels(users)
    else:
      print u'ERROR: %s is not a valid argument for "gam <users> update"' % sys.argv[4]
      sys.exit(2)
  elif command in [u'deprov', u'deprovision']:
    doDeprovUser(users)
  elif command == u'get':
    if sys.argv[4].lower() == u'photo':
      getPhoto(users)
    elif sys.argv[4].lower() == u'drivefile':
      downloadDriveFile(users)
  elif command == u'profile':
    doProfile(users)
  elif command == u'imap':
    doImap(users)
  elif command in [u'pop', u'pop3']:
    doPop(users)
  elif command == u'sendas':
    doSendAs(users)
  elif command == u'language':
    doLanguage(users)
  elif command in [u'utf', u'utf8', u'utf-8', u'unicode']:
    doUTF(users)
  elif command == u'pagesize':
    doPageSize(users)
  elif command == u'shortcuts':
    doShortCuts(users)
  elif command == u'arrows':
    doArrows(users)
  elif command == u'snippets':
    doSnippets(users)
  elif command == u'label':
    doLabel(users)
  elif command == u'filter':
    doFilter(users)
  elif command == u'forward':
    doForward(users)
  elif command in [u'sig', u'signature']:
    doSignature(users)
  elif command == u'vacation':
    doVacation(users)
  elif command == u'webclips':
    doWebClips(users)
  elif command in [u'delegate', u'delegates']:
    doDelegates(users)
  else:
    print u'ERROR: %s is not a valid argument for "gam"' % command
    sys.exit(2)
except IndexError:
  showUsage()
  sys.exit(2)
except KeyboardInterrupt:
  sys.exit(50)
except socket.error, e:
  stderrErrorMsg(e)
  sys.exit(3)
except MemoryError:
  stderrErrorMsg(MESSAGE_GAM_OUT_OF_MEMORY)
  sys.exit(99)
