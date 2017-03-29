# Okta Administration Manager (OAM)

### Summary
The Okta Administration Manager (OAM) allows sys admins to perform REST API calls to Okta from the command line. It also has the ability to perform bulk operations by pulling information from a CSV.

### Current List of Supported Okta APIs
* Users API
* Groups API

### Configuration Steps
1. Download oam.py, config.json, and requirements.txt
2. Install required packages listed in requirements.txt
```pip install -r requirements.txt```
3. Login to Okta as an Administrator with permissions to generate API keys. See full instructions here: [Create an API Token](http://developer.okta.com/docs/api/getting_started/getting_a_token.html)
4. Copy your token and paste it in the config.json file for "apiToken".
5. Set the "orgURL", in config.json, to the URL for your okta domain (Example: "https://acme.okta.com").
6. Save/close config.json
7. Test your setup. Easiest way is to search for a user using the 'find' command.
```python oam.py user foo.bar@acme.com find```
If you get the user's profile, as a json response, in the command window, then you're ready to rock-n-roll!

### Commands
_Syntax may be viewed using the help flag_ ```python oam.py -h```
The main command has two, optional arguments:
```--site [site_name]``` Used to define which Okta instance to call. See Multi-Site configuration setup, below.
```--csv [filename]``` When the csv argument is used the program will pull in data from the indicated csv file based on the values prefaced with a ~ in your command.

Example Command:
```python oam.py --csv test.csv user ~email update --profile primaryPhone ~phone mobilePhone ~cellphone```
This command would loop through the test.csv file for each record in the file, and replace the ~email, ~phone, and ~cellphone variables with the values from the columns containing the same name.

Example CSV file:
```
userID,email,phone,cellphone
1,"foo@bar.com","111-111-1111","222-222-2222"
2,"bar@foo.com","333-333-3333","444-444-4444"
```



#### User API
The user command will perform actions against a single user. The _user_ command has two required, positional arguments:
* Username: Okta username of the target user
* Action: The command action you wish to perform. The following actions are currently supported:
	* find - Returns the full user profile for Username as json in command window
	* appLinks - [Get Assigned App Links](http://developer.okta.com/docs/api/resources/users.html#get-assigned-app-links)
	* groups - [Get Member Groups](http://developer.okta.com/docs/api/resources/users.html#get-member-groups)
	* delete - [Delete User](http://developer.okta.com/docs/api/resources/users.html#delete-user)
	* clear_user_sessions - [Clear User Sessions](http://developer.okta.com/docs/api/resources/users.html#clear-user-sessions)
	* forgot_password - [Forgot Password](http://developer.okta.com/docs/api/resources/users.html#forgot-password) _--sendEmail_ flag will return true and send the user a email notification
	* reset_password - [Reset Password](http://developer.okta.com/docs/api/resources/users.html#reset-password) _--sendEmail_ flag will return true and send the user a email notification
	* setTempPassword - [Set Temporary Password](http://developer.okta.com/docs/api/resources/users.html#expire-password) Sends user temporary password via email
	* deactivate - [Deactivate User](http://developer.okta.com/docs/api/resources/users.html#deactivate-user)
	* unlock - [Unlock User](http://developer.okta.com/docs/api/resources/users.html#unlock-user)
	* expire_password - [Expire Password](http://developer.okta.com/docs/api/resources/users.html#expire-password) Expires password and does _NOT_ send the user a temporary password in email
	* suspend - [Suspend User](http://developer.okta.com/docs/api/resources/users.html#suspend-user)
	* reset_factors - [Reset Factors](http://developer.okta.com/docs/api/resources/users.html#reset-factors)
	* unsuspend - [Unsuspend User](http://developer.okta.com/docs/api/resources/users.html#unsuspend-user)
	* setPassword - [Set User Password](http://developer.okta.com/docs/api/resources/users.html#set-password) _--password_ flag is used to provide password value
	* setQuestion - [Set Recovery Question & Answer](http://developer.okta.com/docs/api/resources/users.html#set-recovery-question--answer) _--question_ and _--answer_ flags are used to provide the desired question and answer values
	* update - [Update Profile](http://developer.okta.com/docs/api/resources/users.html#update-profile-1) _--profile_ flag allows for sending attribute: value pairs. The attribute, as it is shown in okta, should be listed first, and the value you wish to send second. Example:
	```user foo.bar update --profile email foo.bar@acme.com city Lawrence state KS```
    * create - [Create User](http://developer.okta.com/docs/api/resources/users.html#create-user) _--firstName_ & _--lastName_ are required and the Username value is used for the login attribute value. Optional arguments for the create action are:
        * ```--email``` - Specify email address for the user. If not specified email is set to same as login value.
        * ```--activate``` - Activate the user after creation
        * ```--password``` - Specify a password for the new user
        * ```--question``` - Specify a security question for the new user
        * ```--answer``` - Specify a security answer for the new user

##### Groups API
The group command will perform actions against a single group. The _group_ command has two required, positional arguments:
* Group Name: Okta group name of the target group
* Action: The command action you wish to perform. The following actions are currently supported:
    * create - [Add Group](http://developer.okta.com/docs/api/resources/groups.html#add-group) _--description_ is optional and provides the description value for the group
    ```group NewGroup create --description "This is my new group"```
    * update - [Update Group](http://developer.okta.com/docs/api/resources/groups.html#update-group) _--description_ is optional and provides the description value for the group
    * listUsers - [List Group Members](http://developer.okta.com/docs/api/resources/groups.html#list-group-members) Returns list of users in the specified group as json in command window (limit of 10,000 users)
    * addUser - [Add User to Group](http://developer.okta.com/docs/api/resources/groups.html#add-user-to-group) _--user_ is required and provides the login of the user you wish to add to the group
    ```group MyGroup addUser --user foo@acme.com```
    * removeUser - [Remove User from Group](http://developer.okta.com/docs/api/resources/groups.html#remove-user-from-group) _--user_ is required and provides the login of the user you wish to remove from the group
    * delete - [Remove Group](http://developer.okta.com/docs/api/resources/groups.html#remove-group) Prompts for confirmation.

### Multi-site config.json Setup
The config.json file can store multiple Okta sites and API tokens. Such as your key for okta and oktapreview sites. To setup multi-site:
1. Set the MULTI_SITE variable in oam.py equal to 1.
2. Update the config.json as follows:
```{"prod":{"apiToken":"0987654321", "orgURL":"https://acme.okta.com"},"preview":{"apiToken":"1234567890", "orgURL":"https://acme.oktapreview.com"}}```
the site names you specify (_prod_ and _preview_ in the above example) are then what you will need to provide the --site argument each time you perform a command.
Example:
```python oam.py --site prod user foo.bar find```