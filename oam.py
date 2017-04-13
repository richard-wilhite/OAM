#!/user/bin/env python

### Modules ###
import argparse
import copy
import json
import os.path
import re
import requests
import sys
from okta_api_reference import users_apiRef, groups_apiRef

### Variables ###
SCRIPT_VERSION = '0.3'
CONFIG_FILE = 'config.json' # Must be json
ORG_URL = '' # Placeholder defined in configLoader function
REQHEADERS = '' # Placeholder defined in configLoader function

# Set 1 to use site arg to pick the okta instance you want to manage at run time.
# Set 0 if you only have one site in CONFIG_FILE, and want to type less at run time.
MULTI_SITE = 0

### Functions ###
def configLoader( fh, mySite=None ):
	global ORG_URL, REQHEADERS

	if os.path.isfile( fh ) == True:
		with open( fh ) as objFile:
			try:
				data = json.load( objFile )
			except:
				print "Error loading " + CONFIG_FILE + " check json format"
				sys.exit(1)

		if mySite:
			try:
				data[mySite]["orgURL"]
			except:
				print "Error! Site '" + mySite + "' not found in " + CONFIG_FILE
				sys.exit(1)
			if len(data[mySite]["orgURL"]) > 0 and len(data[mySite]["apiToken"]) > 0:
				ORG_URL = data[mySite]["orgURL"]
				REQHEADERS = { "Accept": "application/json", "Content-Type": "application/json", "Authorization": "SSWS " + data[mySite]["apiToken"] }
			else:
				print "Error! orgURL/apiToken not set for " + mySite + " in " + CONFIG_FILE
				sys.exit(1)
		else:
			if len(data["orgURL"]) > 0 and len(data["apiToken"]) > 0:
				ORG_URL = data["orgURL"]
				REQHEADERS = { "Accept": "application/json", "Content-Type": "application/json", "Authorization": "SSWS " + data["apiToken"] }
			else:
				print "Error! orgURL/apiToken not set in " + CONFIG_FILE
				sys.exit(1)
	else:
		print "Error! " + CONFIG_FILE + " not found. Check CONFIG_FILE variable in oam.py"
		sys.exit(1)

def inputs():
	parser = argparse.ArgumentParser( description='Okta Admin Manager', version=SCRIPT_VERSION )
	parser.add_argument( '--site', action='store', dest='varSite', help='Site as defined in CONFIG_FILE' )
	parser.add_argument( '--csv', dest='csvFileName', help='File containing bulk user data' )
	subparsers = parser.add_subparsers( help='commands', dest='command' )

	userParser = subparsers.add_parser( 'user', help='Perform actions against a single user' )
	userParser.add_argument( 'varUsername', action='store', help='Username for target user' )
	userParser.add_argument( 'varAction', action='store', help='Action to take on the indicated user' )
	userParser.add_argument( '--password', dest='varPassword', action='store', help='Set the users password' )
	userParser.add_argument( '--question', dest='varSecQ', action='store', help='Set the users security question' )
	userParser.add_argument( '--answer', dest='varSecA', action='store', help='Set the users security answer' )
	userParser.add_argument( '--sendEmail', dest='varSendEmail', action='store_true', help='Alert the target user of the change made' )
	userParser.add_argument( '--profile', nargs='+', dest='varProfile', action='store', help='Update profile attributes in Okta' )
	userParser.add_argument( '--activate', dest='varActivate', action='store_true', help='Activate user after creation' )
	userParser.add_argument( '--firstName', dest='varFirstname', action='store', help='Specify firstName attribute when creating a user' )
	userParser.add_argument( '--lastName', dest='varLastname', action='store', help='Specify lastName attribute when creating a user' )
	userParser.add_argument( '--email', dest='varEmail', action='store', help='Specify email attribute when creating a user' )

	groupParser = subparsers.add_parser( 'group', help='Perform actions on Okta groups' )
	groupParser.add_argument( 'varGroupName', action='store', help='Action to take on the indicated group' )
	groupParser.add_argument( 'varAction', action='store', help='Action to take on the indicated group' )
	groupParser.add_argument( '--description', dest='varGroupDesc', action='store', help='Set the group name at creation' )
	groupParser.add_argument( '--user', dest='varUsername', action='store', help='The user login to add or remove from the indicated group' )

	# listParser = subparsers.add_parser( 'list', help='List specified items')
	# listParser.add_argument( 'objectType', action='store', help='The itmes to include in your list (e.g. groups, users, etc)')
	# listParser.add_argument( '--criteria', dest='listcrit', action='store', help='Additional search criteria used to narrow results')

	args = parser.parse_args()
	if not args.varSite and MULTI_SITE == 1:
		parser.error('Missing --site parameter')
	elif not args.varSite and MULTI_SITE == 0:
		configLoader( CONFIG_FILE )
	else:
		configLoader( CONFIG_FILE, args.varSite )

	if args.csvFileName:		
		return csvCommandList( args )
	else:
		return args

def csvCommandList( args ):
	headerList = []
	colNums = {}
	inputList = []

	for arg in vars(args):
		x = getattr( args, arg )
		if isinstance( x, list ):
			for i in x:
				x = str( i )
				if re.match( '\~', x ):
					headerList.append( re.sub( '\~', '', x ) )
		else:
			x = str( x )
			if re.match( '\~', x ):
				headerList.append( re.sub( '\~', '', x ) )

	with open( args.csvFileName ) as fh:
		myHeaders = fh.readline().rstrip('\n').split(',')
		for x in headerList:
			colNums[x] = myHeaders.index(x)

		for line in fh:
			l = line.rstrip('\n').split(',')
			loopInputs = copy.deepcopy( args.__dict__ )
			for k, v in colNums.items():
				for x, y in loopInputs.items():
					if isinstance( y, list ):
						for i in y:
							if i == '~' + k:
								loopInputs[x][y.index(i)] = l[v]
					else:
						if y  == '~' + k:
							loopInputs[x] = l[v]
			inputList.append( loopInputs )

	return inputList

def httpRequestor( myAction, apiRef ):
	try:
		varContinue = actionConfirm( "This action: " + myAction + "  can not be undone. Are you sure you wish to continue?", apiRef.ConfirmationRequired )
		if varContinue == False:
			return "Action Cancelled"
	except:
		pass

	s = requests.Session()
	try:
		req = requests.Request( apiRef.RequestType,  apiRef.APICall, headers=REQHEADERS, json=apiRef.PostBody )
	except:
		req = requests.Request( apiRef.RequestType,  apiRef.APICall, headers=REQHEADERS )

	prepped = s.prepare_request( req )
	r = s.send( prepped )

	if myAction == 'find':
		if len( r.json() ) == 1:
			return r.json()
		else:
			print "Error: " + apiRef.__doc__ + " not found"
			sys.exit(0)
	else:
		return r

def actionConfirm( varQuestion, confirmRequired ):
	valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
	prompt = " [yes/no] "

	sys.stdout.write( varQuestion + prompt )
	choice = raw_input().lower()
	if choice in valid:
	    return valid[choice]
	else:
	    sys.stdout.write("Please respond with 'yes' or 'no'\n")

def user_commandProc( args ):
	usrObj = users_apiRef( orgURL=ORG_URL )
	if args['varAction'] == 'create':
		usrObj.createUser( args )
	else:
		usrObj.findUser( args['varUsername'] )
		myUser = httpRequestor( 'find', usrObj )

		if args['varAction'] == "find":
			print json.dumps( myUser, sort_keys=True, indent=4, separators=( ',', ':' ) )
			sys.exit(0)
		elif args['varAction'] == 'appLinks':
			usrObj.appLinks( myUser[0]["id"] )
		elif args['varAction'] == 'groups':
			usrObj.groups( myUser[0]["id"] )
		elif args['varAction'] == 'delete':
			usrObj.delete( myUser[0]["id"] )
		elif args['varAction'] == 'clear_user_sessions':
			usrObj.clear_user_sessions( myUser[0]["id"] )
		elif args['varAction'] == 'forgot_password':
			usrObj.forgot_password( myUser[0]["id"], args['varSendEmail'] )
		elif args['varAction'] == 'activate':
			usrObj.activate( myUser[0]["id"], args['varSendEmail'] )
		elif args['varAction'] == 'reset_password':
			usrObj.reset_password( myUser[0]["id"], args['varSendEmail'] )
		elif args['varAction'] == 'setTempPassword':
			usrObj.setTempPassword( myUser[0]["id"] )
		elif args['varAction'] == 'deactivate':
			usrObj.deactivate( myUser[0]["id"] )
		elif args['varAction'] == 'unlock':
			usrObj.unlock( myUser[0]["id"] )
		elif args['varAction'] == 'expire_password':
			usrObj.expire_password( myUser[0]["id"] )
		elif args['varAction'] == 'suspend':
			usrObj.suspend( myUser[0]["id"] )
		elif args['varAction'] == 'reset_factors':
			usrObj.reset_factors( myUser[0]["id"] )
		elif args['varAction'] == 'unsuspend':
			usrObj.unsuspend( myUser[0]["id"] )
		elif args['varAction'] == 'setPassword':
			usrObj.setPassword( myUser[0]["id"], args['varPassword'] )
		elif args['varAction'] == 'setQuestion':
			usrObj.setQuestion( myUser[0]["id"], args['varSecQ'], args['varSecA'] )
		elif args['varAction'] == 'update':
			usrObj.update( myUser[0]["id"], args['varProfile'] )
		else:
			print "Error! Action:" + args['varAction'] + " not found"
			sys.exit(1)


	r = httpRequestor( args['varAction'], usrObj )
	return r

def group_commandProc( args ):
	grpObj = groups_apiRef( orgURL=ORG_URL )
	if args['varAction'] == 'create':
		grpObj.createGroup( args )
	else:
		grpObj.findGroup( args['varGroupName'] )
		myGroup = httpRequestor( 'find', grpObj )

		if args['varAction'] == "find":
			print json.dumps( myGroup, sort_keys=True, indent=4, separators=( ',', ':' ) )
		elif args['varAction'] == 'update':
			grpObj.update( myGroup[0]["id"], args )
		elif args['varAction'] == 'listUsers':
			grpObj.listUsers( myGroup[0]["id"] )
		elif args['varAction'] == 'addUser':
			usrObj = users_apiRef( orgURL=ORG_URL )
			usrObj.findUser( args['varUsername'] )
			myUser = httpRequestor( 'find', usrObj )

			grpObj.addUser( myGroup[0]["id"], myUser[0]["id"] )
		elif args['varAction'] == 'removeUser':
			usrObj = users_apiRef( orgURL=ORG_URL )
			usrObj.findUser( args['varUsername'] )
			myUser = httpRequestor( 'find', usrObj )

			grpObj.removeUser( myGroup[0]["id"], myUser[0]["id"] )
		elif args['varAction'] == 'delete':
			grpObj.delete( myGroup[0]["id"] )
		else:
			print "Error! Action:" + args['varAction'] + " not found"
			sys.exit(1)

	r = httpRequestor( args['varAction'], grpObj )
	return r

def list_commandProc( args ):
	if args['objectType'] == 'user':
		usrObj = users_apiRef( orgURL=ORG_URL )
		# pull in search criteria from args
		# create apiRef for listUsers

		r = httpRequestor( args['varAction'], usrObj )
	elif args['objectType'] == 'group':
		grpObj = groups_apiRef( orgURL=ORG_URL )
		# pull in criteria from args
		grpObj.listGroups()

		r = httpRequestor( args['varAction'], grpObj )
	# elif args['objectType'] == 'app':
		# appObj = app_apiRef( orgURL=ORG_URL )
		# pull in search criteria from args
		# create apiRef for listApps

	return r

def commandProc( args ):
	if args['command'] == 'user':
		r = user_commandProc( args )
	elif args['command'] == 'group':
		r = group_commandProc( args )
	elif args['command'] == 'list':
		r = list_commandProc( args )
	else:
		print "Error! Command not found"

	try:
		print json.dumps( r.json(), indent=4, separators=( ',', ':' ) )
	except:
		print(r)


### Main ###
myInputs = inputs()

if not isinstance( myInputs, list ):
	inputDict = myInputs.__dict__
	commandProc( inputDict )
else:
	for i in myInputs:
		commandProc( i )
