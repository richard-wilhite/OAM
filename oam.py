#!/user/bin/env python

### Modules ###
import argparse
import copy
import json
import os.path
import re
import requests
import sys

### Variables ###
SCRIPT_VERSION = '0.2'
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
	userParser.add_argument( '--firstName', dest='varFirstname', action='store', help='Activate user after creation' )
	userParser.add_argument( '--lastName', dest='varLastname', action='store', help='Activate user after creation' )
	userParser.add_argument( '--email', dest='varEmail', action='store', help='Activate user after creation' )

	groupParser = subparsers.add_parser( 'group', help='Perform actions on Okta groups' )
	groupParser.add_argument( 'varGroupName', action='store', help='Action to take on the indicated group' )
	groupParser.add_argument( 'varAction', action='store', help='Action to take on the indicated group' )
	groupParser.add_argument( '--description', dest='varGroupDesc', action='store', help='Set the group name at creation' )
	groupParser.add_argument( '--user', dest='varUsername', action='store', help='The user login to add or remove from the indicated group' )

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

def findUser( searchParam ):
	apiCall = ORG_URL + '/api/v1/users?filter=profile.login eq "' + searchParam + '"'
	r = requests.get( apiCall, headers=REQHEADERS )

	if len( r.json() ) == 1:
		return r.json()
	else:
		print("Error: User not found")
		sys.exit(0)

def findGroup( searchParam ):
	apiCall = ORG_URL + '/api/v1/groups?q=' + searchParam
	r = requests.get( apiCall, headers=REQHEADERS )

	if len( r.json() ) == 1:
		return r.json()
	else:
		print("Error: Group not found")
		sys.exit(0)

## User & Create API Reference ##
def createUser_postBody( args ):
	if not args['varFirstname'] and not args['varLastname']:
		print("Error! Required field not provided.\nCreate action requires firstName and lastName attributes")
		sys.exit(1)
	else:
		if not args['varEmail']:
			myVarEmail = args['varUsername']
		else:
			myVarEmail = args['varEmail']

		myPostBody = {"profile": {"firstName": args['varFirstname'],"lastName": args['varLastname'],"email": myVarEmail,"login": args['varUsername']}}
		
		## Password Only ##
		if args['varPassword'] and not args['varSecQ']:
			myPostBody.update( password_postBody( args ) )
		## Password and Security Question ##
		elif args['varPassword'] and args['varSecQ']:
			myPostBody.update( password_postBody( args ) )
			myPostBody["credentials"].update( recoveryQ_postBody( args ) )
		## Security Question Only ##
		elif args['varSecQ'] and not args['varPassword']:
			myPostBody.update({"credentials"})
			myPostBody.append( recoveryQ_postBody( args ) )

		return myPostBody

def password_postBody( args ):
	return {"credentials": {"password" : { "value": args['varPassword'] }}}

def recoveryQ_postBody( args ):
	return {"recovery_question": {"question": args['varSecQ'],"answer": args['varSecA']}}

def profileUpdate_postBody( args ):
	if args['varProfile']:
		myPostBody = {}
		myPostBody["profile"] = dict(args['varProfile'][i:i+2] for i in range(0, len(args['varProfile']), 2))

		return myPostBody

def user_curlDict( args, var_userID ):
	return {
		'appLinks': {'RequestType':'GET','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/appLinks'}, 
		'groups': {'RequestType':'GET','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/groups'}, 
		'delete': {'RequestType':'DELETE','APICall':ORG_URL + '/api/v1/users/' + var_userID,'ConfirmationRequired':'Y'}, 
		'clear_user_sessions': {'RequestType':'DELETE','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/sessions','ConfirmationRequired':'Y'}, 
		'forgot_password': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/credentials/forgot_password?sendEmail=' + str( args['varSendEmail'] )},
		'activate': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/activate?sendEmail=' + str( args['varSendEmail'] )},
		'reset_password': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/reset_password?sendEmail=' + str( args['varSendEmail'] )},
		'setTempPassword': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/expire_password?tempPassword=true'},
		'deactivate': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/deactivate','ConfirmationRequired':'Y'},
		'unlock': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/unlock'},
		'expire_password': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/expire_password'},
		'suspend': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/suspend'},
		'reset_factors': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/reset_factors'},
		'unsuspend': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/unsuspend'},
		'setPassword': {'RequestType':'PUT','APICall':ORG_URL + '/api/v1/users/' + var_userID,'PostBody':password_postBody( args )},
		'setQuestion': {'RequestType':'PUT','APICall':ORG_URL + '/api/v1/users/' + var_userID,'PostBody':recoveryQ_postBody( args )},
		'update': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID,'PostBody':profileUpdate_postBody( args )},
	}

## Groups API Reference ##
def group_postBody( args ):
	return {"profile":{"name": args['varGroupName'],"description": args['varGroupDesc']}}

def groups_curlDict( args, var_groupID='', var_userID='' ):
	return {
		'create': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/groups','PostBody':group_postBody( args )},
		'update': {'RequestType':'PUT','APICall':ORG_URL + '/api/v1/groups/' + var_groupID,'PostBody':group_postBody( args )},
		'listUsers': {'RequestType':'GET','APICall':ORG_URL + '/api/v1/groups/' + var_groupID + '/users'}, # Needs pagination support for groups larger than 10k
		# 'listGroups': {'RequestType':'GET','APICall':ORG_URL + '/api/v1/groups/'}, # Needs pagination support for lists larger than 10k groups
		'addUser': {'RequestType':'PUT','APICall':ORG_URL + '/api/v1/groups/' + var_groupID + '/users/' + var_userID},
		'removeUser': {'RequestType':'DELETE','APICall':ORG_URL + '/api/v1/groups/' + var_groupID + '/users/' + var_userID,'ConfirmationRequired':'Y'},
		'delete': {'RequestType':'DELETE','APICall':ORG_URL + '/api/v1/groups/' + var_groupID,'ConfirmationRequired':'Y'}
	}

def httpRequestor( args, curlDict ):
	try:
		myAction = curlDict[args['varAction']]
	except:
		print "Action Unknown" + args['varAction']
		sys.exit(1)


	if 'ConfirmationRequired' in myAction:
		varContinue = actionConfirm( "This action: " + args['varAction'] + "  can not be undone. Are you sure you wish to continue?" )
		if varContinue == False:
			return "Action Cancelled"

	s = requests.Session()
	if 'PostBody' in myAction:
		req = requests.Request( myAction['RequestType'],  myAction['APICall'], headers=REQHEADERS, json=myAction['PostBody'] )
	else:
		req = requests.Request( myAction['RequestType'],  myAction['APICall'], headers=REQHEADERS )

	prepped = s.prepare_request( req )
	r = s.send( prepped )

	return r

def actionConfirm( varQuestion ):
	valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
	prompt = " [yes/no] "

	sys.stdout.write( varQuestion + prompt )
	choice = raw_input().lower()
	if choice in valid:
	    return valid[choice]
	else:
	    sys.stdout.write("Please respond with 'yes' or 'no'\n")


def commandProc( args ):
	if args['command'] == 'user':
		if args['varAction'] == 'create':
			apiCall = ORG_URL + '/api/v1/users?activate=' + str( args['varActivate'] )
			r = requests.post( apiCall, headers=REQHEADERS, json=createUser_postBody( args ) )
			print(r)
		else:
			myUser = findUser( args['varUsername'] )

			if args['varAction'] == "find":
				print json.dumps( myUser, sort_keys=True, indent=4, separators=( ',', ':' ) )
			else:
				r = httpRequestor( args, user_curlDict( args, myUser[0]["id"] ) )
				try:
					r.json()
					print json.dumps( r.json(), indent=4, separators=( ',', ':' ) )
					print r
				except:
					print(r)

	elif args['command'] == 'group':
		if args['varAction'] == 'create':
			r = httpRequestor( args, groups_curlDict( args ) )
			print(r)
		else:
			myGroup = findGroup( args['varGroupName'] )

			if args['varAction'] == "find":
				print json.dumps( myGroup, sort_keys=True, indent=4, separators=( ',', ':' ) )
			elif args['varAction'] in ( 'addUser', 'removeUser' ):
				if not args['varUsername']:
					print "Error! Must specify user to add/remove"
					sys.exit(1)
				myUser = findUser( args['varUsername'] )
				r = httpRequestor( args, groups_curlDict( args, myGroup[0]["id"], myUser[0]["id"] ) )
				print(r)
			else:
				r = httpRequestor( args, groups_curlDict( args, myGroup[0]["id"] ) )
				# Should add a CSV option
				try:
					r.json()
					print json.dumps( r.json(), indent=4, separators=( ',', ':' ) )
					print r
				except:
					print(r)

def main():
	myInputs = inputs()
	
	if not isinstance( myInputs, list ):
		inputDict = myInputs.__dict__
		commandProc( inputDict )
	else:
		for i in myInputs:
			commandProc( i )
			
### Main ###
if __name__ == '__main__':
    main()