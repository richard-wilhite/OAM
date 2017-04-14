#### OKTA_API_REF
# This module returns the appropriate content for use with python http reqeusts module

### Modules ###

### Classes ###
class users_apiRef:
	"""User"""
	__attr__ = [ 'orgURL' ]

	def __init__( self, orgURL ):
		self.orgURL = orgURL

	def create( self, args ):
		self.RequestType = 'Post'
		self.APICall = self.orgURL + '/api/v1/users?activate=' + str( args['varActivate'] )
		self.PostBody = self.createUser_postBody( args )

	def createUser_postBody( self, args ):
		if not args['varEmail']:
			self.myVarEmail = args['varUsername']
		else:
			self.myVarEmail = args['varEmail']

		self.myPostBody = {"profile": {"firstName": args['varFirstname'],"lastName": args['varLastname'],"email": self.myVarEmail,"login": args['varUsername']}}
		
		if args['varPassword'] or args['varSecQ']:
			self.myPostBody.update({"credentials":{}})
			# Password Only ##
			if args['varPassword'] and not args['varSecQ']:
				self.myPostBody["credentials"].update( self.password_postBody( args['varPassword'] ) )
			## Password and Security Question ##
			elif args['varPassword'] and args['varSecQ']:
				self.myPostBody["credentials"].update( self.password_postBody( args['varPassword'] ) )
				self.myPostBody["credentials"].update( self.recoveryQ_postBody( args['varSecQ'], args['varSecA'] ) )
			## Security Question Only ##
			elif args['varSecQ'] and not args['varPassword']:
				self.myPostBody["credentials"].update( self.recoveryQ_postBody( args['varSecQ'], args['varSecA'] ) )

		return self.myPostBody

	def password_postBody( self, varPassword ):
		return {"password" : { "value": varPassword }}

	def recoveryQ_postBody( self, varSecQ, varSecA ):
		return {"recovery_question": {"question": varSecQ,"answer": varSecA }}

	def profileUpdate_postBody( self, varProfile ):
		self.myPostBody = {}
		self.myPostBody["profile"] = dict( varProfile[i:i+2] for i in range(0, len(varProfile), 2) )

		return self.myPostBody

	def findUser( self, searchParam ):
		self.RequestType = 'GET'
		self.APICall = self.orgURL + '/api/v1/users?filter=profile.login eq "' + searchParam + '"'

	def appLinks( self, var_userID ):
		self.RequestType = 'GET'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/appLinks'

	def groups( self, var_userID ):
		self.RequestType = 'GET'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/groups'

	def delete( self, var_userID ):
		self.RequestType = 'DELETE'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID
		self.ConfirmationRequired = True

	def clear_user_sessions( self, var_userID ):
		self.RequestType = 'DELETE'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/sessions'
		self.ConfirmationRequired = True

	def forgot_password( self, var_userID, varSendEmail ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/credentials/forgot_password?sendEmail=' + str( varSendEmail )

	def activate( self, var_userID, varSendEmail ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/activate?sendEmail=' + str( varSendEmail )

	def reset_password( self, var_userID, varSendEmail ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/reset_password?sendEmail=' + str( varSendEmail )

	def setTempPassword( self, var_userID ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/expire_password?tempPassword=true'

	def deactivate( self, var_userID ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/deactivate'
		self.ConfirmationRequired = True

	def unlock( self, var_userID ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/unlock'

	def expire_password( self, var_userID ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/expire_password'

	def suspend( self, var_userID ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/suspend'
		self.ConfirmationRequired = True

	def reset_factors( self, var_userID ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/reset_factors'

	def unsuspend( self, var_userID ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID + '/lifecycle/unsuspend'
		self.ConfirmationRequired = True

	def setPassword( self, var_userID, varPassword ):
		self.RequestType = 'PUT'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID
		self.PostBody = { "credentials": self.password_postBody( varPassword ) }

	def setQuestion( self, var_userID, varSecQ, varSecA ):
		self.RequestType = 'PUT'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID
		self.PostBody = { "credentials": self.recoveryQ_postBody( varSecQ, varSecA ) }

	def update( self, var_userID, varProfile ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/users/' + var_userID
		self.PostBody = self.profileUpdate_postBody( varProfile )

class groups_apiRef:
	"""Group"""
	__attr__ = [ 'orgURL' ]

	def __init__( self, orgURL ):
		self.orgURL = orgURL

	def findGroup( self, searchParam ):
		self.RequestType = 'GET'
		self.APICall = self.orgURL + '/api/v1/groups?q=' + searchParam

	def create( self, args ):
		self.RequestType = 'POST'
		self.APICall = self.orgURL + '/api/v1/groups'
		self.PostBody = self.group_postBody( args )

	def group_postBody( self, args ):
		return {"profile":{"name": args['varGroupName'],"description": args['varGroupDesc']}}

	def update( self, var_groupID, args ):
		self.RequestType = 'PUT'
		self.APICall = self.orgURL + '/api/v1/groups/' + var_groupID
		self.PostBody = self.group_postBody( args )

	def listUsers( self, var_groupID ): # Needs pagination support for groups larger than 10k
		self.RequestType = 'GET'
		self.APICall = self.orgURL + '/api/v1/groups/' + var_groupID + '/users'

	def listGroups( self ): # Needs pagination support for groups larger than 10k
		self.RequestType = 'GET'
		self.APICall = self.orgURL + '/api/v1/groups/'

	def addUser( self, var_groupID, var_userID ):
		self.RequestType = 'PUT'
		self.APICall = self.orgURL + '/api/v1/groups/' + var_groupID + '/users/' + var_userID

	def removeUser( self, var_groupID, var_userID ):
		self.RequestType = 'DELETE'
		self.APICall = self.orgURL + '/api/v1/groups/' + var_groupID + '/users/' + var_userID
		self.ConfirmationRequired = True

	def delete( self, var_groupID ):
		self.RequestType = 'DELETE'
		self.APICall = self.orgURL + '/api/v1/groups/' + var_groupID
		self.ConfirmationRequired = True
