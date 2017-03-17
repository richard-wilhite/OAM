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
SCRIPT_VERSION = '0.1'
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
			data = json.load( objFile )

		if mySite:
			ORG_URL = data[mySite]["orgURL"]
			REQHEADERS = { "Accept": "application/json", "Content-Type": "application/json", "Authorization": "SSWS " + data[mySite]["apiToken"] }
		else:
			ORG_URL = data["orgURL"]
			REQHEADERS = { "Accept": "application/json", "Content-Type": "application/json", "Authorization": "SSWS " + data["apiToken"] }
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

	userCreateParser = subparsers.add_parser( 'create', help='Create a single user' )
	userCreateParser.add_argument( 'varFirstname', action='store', help='User First name' )
	userCreateParser.add_argument( 'varLastname', action='store', help='User Last name' )
	userCreateParser.add_argument( 'varEmail', action='store', help='User email address' )
	userCreateParser.add_argument( '--login', dest='varlogin', action='store', help='User login (Default to same as email)' )
	userCreateParser.add_argument( '--activate', dest='varActivate', action='store_true', help='Activate user after creation' )
	userCreateParser.add_argument( '--password', dest='varPassword', action='store', help='Set the users password at creation' )
	userCreateParser.add_argument( '--question', dest='varSecQ', action='store', help='Set the users security question at creation' )
	userCreateParser.add_argument( '--answer', dest='varSecA', action='store', help='Set the users security answer at creation' )

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

def findUser( myUsername ):
	apiCall = ORG_URL + '/api/v1/users?q=' + myUsername
	r = requests.get( apiCall, headers=REQHEADERS )

	return r

def userIDCapture( myData ):
	if len( myData ) == 1:
		userID = myData[0]["id"]
	elif len( myData ) > 1:
		userID = myData["id"]
	else:
		print("Error! Multiple IDs found!")
		sys.exit(0)

	return userID

def create_postBody( args ):
	if not args['varlogin']:
		myVarLogin = args['varEmail']
	else:
		myVarLogin = args['varlogin']

	myPostBody = {"profile": {"firstName": args['varFirstname'],"lastName": args['varLastname'],"email": args['varEmail'],"login": myVarLogin}}
	
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

def user_httpRequestor( args, var_userID ):
	curlDict = {
		'appLinks': {'RequestType':'GET','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/appLinks'}, 
		'groups': {'RequestType':'GET','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/groups'}, 
		'delete': {'RequestType':'DELETE','APICall':ORG_URL + '/api/v1/users/' + var_userID,'ConfirmationRequired':'Y'}, 
		'clear_user_sessions': {'RequestType':'DELETE','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/sessions','ConfirmationRequired':'Y'}, 
		'forgot_password': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/credentials/forgot_password?sendEmail=' + str( args['varSendEmail'] )},
		# 'activate': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID + '/lifecycle/activate?sendEmail=' + str( args['varSendEmail'] )},
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
		'update': {'RequestType':'POST','APICall':ORG_URL + '/api/v1/users/' + var_userID,'PostBody':profileUpdate_postBody( args )}
	}

	try:
		myAction = curlDict[args['varAction']]
	except UnknownAction:
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
		myData = findUser( args['varUsername'] )

		if args['varAction'] == "find":
			print json.dumps( myData.json(), sort_keys=True, indent=4, separators=( ',', ':' ) )
		else:
			var_userID = userIDCapture( myData.json() )
			r = user_httpRequestor( args, var_userID )
			try:
				r.json()
				print json.dumps( r.json(), indent=4, separators=( ',', ':' ) )
				print r
			except:
				print(r)

	elif args['command'] == 'create':
		apiCall = ORG_URL + '/api/v1/users?activate=' + str( args['varActivate'] )
		r = requests.post( apiCall, headers=REQHEADERS, json=create_postBody( args ) )
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