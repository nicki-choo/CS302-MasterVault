from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
# from flask_cors import CORS
from forms import RegistrationForm, LoginForm, AnimalSelectionForm, FamilyRegistrationForm
from dotenv import load_dotenv
from encryption import encrypt, decrypt
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
import random, string, csv, os
from bson.objectid import ObjectId


# Constants
ACCOUNT_METADATA_LENGTH = 11
client = MongoClient('mongodb+srv://Conor:M0ng0DB1@mastervaultdb1.lf6e7.mongodb.net/')
db = client.MasterVault
userData = db["userData"]
userPasswords = db["userPasswords"]
familyData = db["familyData"]
temporary_2fa_storage = {} # Temporary storage for 2FA codes



app = Flask(__name__)
# CORS(app)
mail = Mail(app)
load_dotenv()

app.config['SECRET_KEY'] = '47a9cee106fa8c2c913dd385c2be207d'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'nickidummyacc@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
mail = Mail(app)



@app.context_processor
def inject_account_type():
    accountType = session.get('accountType', None)
    return dict(accountType=accountType)



def generate_password(phrase, length, exclude_numbers=False, exclude_symbols=False, replace_vowels=False,
                      remove_vowels=False, randomize=False):
    # Always start with letters as the base characters
    characters = string.ascii_letters

    # Remove spaces from the phrase
    phrase = phrase.replace(" ", "")

    # Add numbers and symbols unless excluded
    if not exclude_numbers:
        characters += string.digits
    if not exclude_symbols:
        characters += string.punctuation

    # Ensure the phrase is shorter or equal to the password length
    if len(phrase) > length:
        phrase = phrase[:length]  # Shorten the phrase

    # Extended vowel map with more phoneme-based replacements
    if replace_vowels:
        vowel_map = {
            'a': ['@', 'A', 'æ', '4', 'â', 'ä'],
            'e': ['3', 'E', '€', 'ê', 'é', 'ë'],
            'i': ['1', 'I', '!', 'î', 'ï', 'í'],
            'o': ['0', 'O', 'ø', 'ô', 'ö', 'ó'],
            'u': ['U', 'u', 'ù', 'û', 'ü', 'ú']
        }
        # Replace vowels in the phrase using the extended vowel map
        phrase = ''.join([random.choice(vowel_map.get(char.lower(), [char])) for char in phrase])

    # Revert numbers and symbols if they are excluded
    if exclude_numbers:
        phrase = phrase.replace('1', 'i').replace('3', 'e').replace('0', 'o')
    if exclude_symbols:
        phrase = phrase.replace('@', 'a').replace('&', 'a').replace('$', 's').replace('#', 'h')

    # Remove vowels if selected
    if remove_vowels:
        phrase = ''.join([char for char in phrase if char.lower() not in 'aeiou'])

    # Randomize the phrase characters if selected
    if randomize:
        phrase = ''.join(random.sample(phrase, len(phrase)))

    # Extended phoneme mapping for letters
    phoneme_map = {
        'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F',
        'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J', 'k': 'K', 'l': 'L',
        'm': 'M', 'n': 'N', 'o': 'O', 'p': 'P', 'q': 'Q', 'r': 'R',
        's': 'S', 't': 'T', 'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X',
        'y': 'Y', 'z': 'Z',
        # Phoneme-based alternatives for additional variety
        'ph': 'F', 'gh': 'G', 'ch': 'C', 'sh': 'S', 'th': 'T'
    }

    # Map the phrase to its phoneme equivalents
    phrase_phoneme = ''.join([phoneme_map.get(char.lower(), char) for char in phrase])

    # # Extend the phrase if it's too short
    # while len(phrase_phoneme) < length:
    #     phrase_phoneme += random.choice(characters)

    # Generate the final password by picking characters from the phrase_phoneme
    password = ''.join(
        [phrase_phoneme[i] if i < len(phrase_phoneme) else random.choice(characters) for i in range(length)])

    return password




def getPasswords(passwordID):
    # Convert passwordID to ObjectId for MongoDB query
    searchPasswords = userPasswords.find_one({'_id': ObjectId(passwordID)})

    userList = []
    currentList = []

    # If no passwords are found for the user, insert a new document
    if searchPasswords is None:
        userPasswords.insert_one({"_id": ObjectId(passwordID)})

    if not searchPasswords:
        print("No password data found for this user")
        return []

    # Process each key-value pair in the user's password data
    for key, value in searchPasswords.items():
        if key == '_id':
            continue  # Skip the '_id' key

        # Decrypt the value if necessary
        # if "createdDate" not in key and "passwordLocked" not in key and value != None:
        #     value = decrypt(value)

        currentList.append(value)  # Store the value to the list

        # If the account reaches the max length, add the list to userList
        if len(currentList) == ACCOUNT_METADATA_LENGTH:
            userList.append(currentList)
            currentList = []

    # Add the remaining items if the last list is not empty
    if currentList:
        userList.append(currentList)

    print("User Accounts: ", userList)
    return userList



def getFamilyMembers(sessionID):
    # Ensure sessionID is an ObjectId
    familyGroup = familyData.find_one({'_id': ObjectId(sessionID)})

    # Check if the familyGroup is None (no record found)
    if not familyGroup:
        print("No family group found for sessionID:", sessionID)
        return []

    currentList = []
    childList = []

    # Iterate through familyGroup items
    for key, value in familyGroup.items():
        if key == '_id' or key == 'familyID':
            continue  # Skip the '_id' and 'familyID' keys

        currentList.append(value)

        if len(currentList) == 2:
            childList.append(currentList)
            currentList = []

    if currentList:
        childList.append(currentList)

    print("Child Accounts: ", childList)
    return childList

  

def check_password_strength(password):
    strength = {'status': 'Weak', 'score': 0, 'color': 'red'}

    # Check if password is None or empty and return weak strength immediately
    if not password:
        return strength

    # Length check: reward longer passwords
    if len(password) >= 15:
        strength['score'] += 2  # Longer than 15 is considered very strong
    elif len(password) >= 12:
        strength['score'] += 1.5
    elif len(password) >= 8:
        strength['score'] += 1
    else:
        strength['score'] += 0.5  # Penalize shorter passwords

    # Check for digits
    if any(char.isdigit() for char in password):
        strength['score'] += 1

    # Check for uppercase and lowercase combination
    if any(char.isupper() for char in password) and any(char.islower() for char in password):
        strength['score'] += 1

    # Check for special characters (symbols)
    if any(char in string.punctuation for char in password):
        strength['score'] += 1

    # Check for a mix of letters, numbers, and symbols
    if (any(char.isalpha() for char in password) and
            (any(char.isdigit() for char in password) or any(char in string.punctuation for char in password))):
        strength['score'] += 1

    # Penalize for common patterns like "123", "abc", or repeating characters
    common_patterns = ['123', 'password', 'abc', 'qwerty']
    if any(pattern in password.lower() for pattern in common_patterns):
        strength['score'] -= 1

    # Penalize for consecutive identical characters
    if any(password[i] == password[i+1] == password[i+2] for i in range(len(password) - 2)):
        strength['score'] -= 1

    # Penalize for too many repeated characters
    char_count = {char: password.count(char) for char in set(password)}
    if any(count > len(password) // 2 for count in char_count.values()):
        strength['score'] -= 1

    # Adjust score boundaries
    strength['score'] = max(0, strength['score'])  # Ensure score doesn't go below 0

    # Update status and color based on score
    if strength['score'] >= 5:
        strength['status'] = 'Very Strong'
        strength['color'] = 'green'
    elif strength['score'] >= 4:
        strength['status'] = 'Strong'
        strength['color'] = 'lightgreen'
    elif strength['score'] >= 3:
        strength['status'] = 'Moderate'
        strength['color'] = 'orange'
    else:
        strength['status'] = 'Weak'
        strength['color'] = 'red'

    return strength



@app.route('/create_password', methods=['GET'])
def create_password():
    # Default values for initial page load
    return render_template('createPassword.html')



@app.route('/familyCreatePassword', methods=['GET', 'POST'])
def family_create_password():
    accountType = session.get('accountType', 'family')
    return render_template('createPassword.html', accountType=accountType)



@app.route('/create_password', methods=['POST'])
def handle_create_password():
    # Initialize variables
    password = ""
    strength = None
    error = None
    phrase = request.form.get('phrase')
    length = int(request.form.get('length', 8))  # Provide a default value in case it's not set
    exclude_numbers = 'exclude_numbers' in request.form
    exclude_symbols = 'exclude_symbols' in request.form
    replace_vowels = 'replace_vowels' in request.form
    randomize = 'randomize' in request.form

    # Validate options and generate password
    if not phrase:
        error = "Please enter a phrase."
    else:
        password = generate_password(phrase, length, exclude_numbers, exclude_symbols, replace_vowels,
                                    randomize)
        strength = check_password_strength(password)
        if not password:
            error = "Failed to generate password. Ensure the phrase is shorter than the desired password length."

    # Render the same template with new data
    return render_template('createPassword.html', password=password, strength=strength, error=error, phrase=phrase,
                           length=length, exclude_numbers=exclude_numbers, exclude_symbols=exclude_symbols,
                           replace_vowels=replace_vowels, randomize=randomize)



@app.route('/', methods=['GET'])
def landing_page():
    return render_template("landingPage.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    cform = LoginForm()

    if request.method == 'POST':
        email = cform.email.data

        if email:
            findPost = userData.find_one({"email": email})

            if findPost:
                postEmail = findPost["email"]

                if email == postEmail:
                    # Set session ID and user details
                    session['sessionID'] = str(findPost['_id'])
                    session['username'] = decrypt(findPost["username"], session['sessionID'])
                    session['email'] = email

                    # Set account type in the session
                    session['accountType'] = findPost.get('accountType', 'personal')

                    # Check if accountType is family
                    if session['accountType'] == 'family':
                        session['familyID'] = findPost.get('familyID', None)

                    # Detect if the user is a child account based on child ID
                    session['is_child_account'] = is_child_account(session['sessionID'])

                    # Check if 2FA is enabled in the user's settings
                    if findPost.get("2FA", False):
                        pin = random.randint(1000, 9999)
                        send_2fa_verification_email(email, pin, purpose='login')
                        store_pin(email, pin)
                        return redirect(url_for('two_fa_verify'))

                    # Redirect to animal ID verification if no 2FA
                    return redirect(url_for('animalIDVerification'))

            flash("Invalid email")
            return render_template("login.html", form=cform)

    return render_template("login.html", form=LoginForm())



@app.route('/extension_login', methods=['POST'])
def login_extension():
    # Check if the request contains JSON data (API or extension login)
    if request.is_json:
        data = request.get_json()

        # Ensure that email and password are provided in the JSON request
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"status": "error", "message": "Email and password are required"}), 400

        email = data.get('email')
        password = data.get('password')

        # Find the user in the database
        findPost = userData.find_one({"email": email})

        if findPost and findPost["email"] == email:
            stored_password = findPost["loginPassword"]

            # Verify the provided password against the stored plain text password
            if password == decrypt(stored_password, findPost['_id']):
                # If the password matches, set session or return a successful login response
                username = findPost["username"]
                session['sessionID'] = str(findPost['_id'])
                session['username'] = username
                session['email'] = email
                session['password'] = password

                # Return a success message and include the username
                return jsonify({"status": "success", "message": "Login successful", "username": username}), 200
            else:
                # If the password does not match
                return jsonify({"status": "error", "message": "Invalid email or password"}), 403
        else:
            return jsonify({"status": "error", "message": "Invalid email or password"}), 403

    return jsonify({"status": "error", "message": "Invalid request format. JSON expected."}), 400



@app.route('/logout')
def logout():
    # Clear the user's session
    session.clear()

    return redirect(url_for('login'))



@app.route('/about', methods=['GET'])
def aboutUs():
    sessionID = session.get('sessionID')

    if not sessionID:
        return redirect(url_for('login'))

    user_data = userData.find_one({"_id": ObjectId(sessionID)})

    if not user_data:
        # Handle case where user data is not found
        return "User not found", 404

    # Get the account type or default to 'personal'
    account_type = user_data.get('accountType', 'personal')

    return render_template('aboutUs.html', accountType=account_type)



@app.route('/animalID_verification', methods=['GET', 'POST'])
def animalIDVerification():
    sessionID = session.get('sessionID')

    if not sessionID:
        return redirect(url_for('login'))

    findPost = userData.find_one({"_id": ObjectId(sessionID)})

    if not findPost:
        return "User not found", 404

    available_animals = ['giraffe', 'dog', 'chicken', 'monkey', 'peacock', 'tiger']
    selected_animal = findPost['animalID']

    # Check if the 'animalID' exists
    encrypted_animal_id = decrypt(findPost.get('animalID'), sessionID)
    if encrypted_animal_id:
        selected_animal = encrypted_animal_id
    else:
        selected_animal = None

    # Ensure selected_animal is valid, otherwise choose a random one
    if not selected_animal or selected_animal not in available_animals:
        selected_animal = random.choice(available_animals)

    if request.method == 'POST':
        password = request.form.get('password')
        security_check = request.form.get('securityCheck')

        if security_check and password == decrypt(findPost['loginPassword'], sessionID):
            userData.update_one({"_id": ObjectId(sessionID)}, {"$set": {"failedAttempt": 0}})
            print("Failed Attempts: ", findPost['failedAttempt'])
            if findPost['masterPassword'] is None:
                return redirect(url_for('master_password'))
            else:
                account_type = findPost.get('accountType', 'personal')
                if account_type == 'family':
                    return redirect(url_for('familyPasswordList'))
                else:
                    return redirect(url_for('passwordList'))

        updateNumber = findPost['failedAttempt'] + 1     
        print("Failed Attempts: ", updateNumber)
        userData.update_one({"_id": ObjectId(sessionID)}, {"$set": {"failedAttempt": updateNumber}})
        if updateNumber == 2:
            firstFailedLogin(findPost['email'])
        elif updateNumber == 5:
            secondFailedLogin(findPost['email'])

            lock_timestamp = datetime.now() + timedelta(minutes=int(60))

            update = {
                "$set": {
                    'lockDuration': 60,
                    'accountLocked': 'Locked',
                    'lockTimestamp': lock_timestamp
                }
            }

            userData.update_one({'_id': ObjectId(sessionID)}, update)

            if lock_account_in_db(60, sessionID):
                session['lock_state'] = 'locked'
                session['unlock_time'] = lock_timestamp

                flash('Incorrect password or security check not confirmed', 'danger')

    return render_template('animal_IDLogin.html', selected_animal=selected_animal)



@app.route('/choose_animal', methods=['GET', 'POST'])
def animal_id():
    form = AnimalSelectionForm()

    sessionID = session.get('sessionID')

    if not sessionID:
        return redirect(url_for('login'))

    if form.validate_on_submit():
        selected_animal = form.animal.data
        userData.update_one({"_id": ObjectId(sessionID)}, {"$set": {"animalID": encrypt(selected_animal, sessionID)}})

        return redirect(url_for('login'))

    return render_template('animal_ID.html', form=form)



def send_2fa_verification_email(email, pin, purpose='login'):
    if purpose == 'login':
        subject = "Your MasterVault 2FA Login PIN"
        body = f'Your 2FA verification PIN for login is: {pin}. Use this PIN to complete your login.'
    elif purpose == 'enable_2fa':
        subject = "Enable 2FA on Your MasterVault Account"
        body = f'You have requested to enable 2FA on your account. Your 2FA PIN is: {pin}. Use this PIN to confirm enabling 2FA.'

    msg = Message(subject,
                  sender='nickidummyacc@gmail.com',
                  recipients=[email])
    msg.body = body
    mail.send(msg)



def send_verification_email(email):
    msg = Message("Welcome to MasterVault",
                  sender='nickidummyacc@gmail.com',
                  recipients=[email])
    msg.body = 'Hello, your account has been registered successfully! Thank you for using MasterVault. (This is a test program for a college project)'
    mail.send(msg)



def send_family_account_request(email, parentID, current_user):
    msg = Message("Family Account Request",
                  sender='nickidummyacc@gmail.com',
                  recipients=[email])
    # URL for the family member to register
    registration_link = url_for('register_family', familyID=parentID, _external=True)
    msg.body = (f'Hello,\n\n{current_user} has requested to add you to their MasterVault family account.\n'
                f'Please click the link below to register:\n\n{registration_link}\n\n'
                f'Thank you for using MasterVault. (This is a test program for a college project)')
    mail.send(msg)



def firstFailedLogin(email):
    msg = Message("Failed Login Attempt",
                  sender='nickidummyacc@gmail.com',
                  recipients=[email])
    msg.body = (f'Hello, we are emailing you to notify you that there has been three failed login attempts to the MasterVault account made with this email address.'
                f'\nIf this account is not yours, please ignore these emails.')
    mail.send(msg)



def secondFailedLogin(email):
    msg = Message("Numerous Failed Login Attempts!",
                    sender='nickidummyacc@gmail.com',
                    recipients=[email])
    # print("User email is: ", email)
    resetPasswordLink = url_for('resetPasswordLocked', emailAddress=email, _external=True)
    msg.body = (f'Hello, we are emailing you to notify you that there has been numerous failed login attempts to the MasterVault account made with this email address.'
                f'\nIn response to this suspicious activity, we have locked the account linked with this email address.'
                f'\nIf these failed attempts are indeed yourself, we appologise for the inconvenience.{resetPasswordLink}')
    mail.send(msg)



@app.route('/register', methods=['GET', 'POST'])
def register():
    cform = RegistrationForm()

    if cform.validate_on_submit():
        # Get the current time and the user's date of birth
        dob = cform.dob.data
        timeNow = datetime.now()
        dobTime = datetime(year=dob.year, month=dob.month, day=dob.day, hour=0, minute=0, second=0)

        # Prepare the user data post
        post = {
            "username": cform.username.data,
            "email": cform.email.data,
            "DOB": dobTime,
            "loginPassword": cform.password.data,
            "animalID": None,
            "accountType": cform.account_type.data,
            "masterPassword": None,
            "2FA": False,
            "failedAttempt": 0,
            "accountLocked": "Unlocked",
            "lockDuration": "empty",
            "lockTimestamp": timeNow
        }

        # Insert the user data into the database
        userData.insert_one(post)

        # Retrieve the inserted document
        findPost = userData.find_one(post)

        # Store the _id in the session as a string
        session['sessionID'] = str(findPost['_id'])
        userData.update_one({'_id': ObjectId(session['sessionID'])},
                            {'$set': {'username': encrypt(cform.username.data, session['sessionID']), 'loginPassword': encrypt(cform.password.data, session['sessionID'])}})
        session['accountType'] = cform.account_type.data  # Store the accountType in the session

        # Insert the user ID into the userPasswords collection
        userPasswords.insert_one({"_id": ObjectId(session['sessionID'])})

        # Check if the user chose the 'family' account type
        if cform.account_type.data == "family":
            # Find the highest familyID, if present, and increment it
            lastFamilyID = familyData.find_one(sort=[("familyID", -1)])  # Find the highest familyID

            # Set the familyID for this family account
            idCounter = lastFamilyID['familyID'] + 1 if lastFamilyID else 1

            # Create a family post for the user
            familyPost = {
                "_id": ObjectId(session['sessionID']),
                "familyID": idCounter
            }

            # Insert family post into familyData collection
            familyData.insert_one(familyPost)

            # Also update the userData collection to reflect the familyID
            userData.update_one(
                {'_id': ObjectId(session['sessionID'])},
                {'$set': {"familyID": idCounter}}
            )

        # Send verification email after successfully saving account details
        send_verification_email(cform.email.data)

        flash('Account created successfully! An email will be sent to you.', 'success')
        return redirect(url_for('animal_id'))

    return render_template("register.html", form=cform)


 
@app.route('/register_family/<familyID>', methods=['GET', 'POST'])
def register_family(familyID):
    form = FamilyRegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        dob = form.dob.data
        password = form.password.data

        timeNow = datetime.now()
        dobTime = datetime(year=dob.year, month=dob.month, day=dob.day, hour=0, minute=0, second=0)

        # Retrieve the familyID from the session (use default 0 if not found)

        # Prepare the user data post
        post = {
            "username": username,
            "email": email,  # No email for family members in this form
            "DOB": dobTime,
            "loginPassword": password,
            "animalID": None,
            "accountType": 'family',
            "familyID": familyID,
            "masterPassword": None,
            "2FA": False,
            "failedAttempt": 0,
            "accountLocked": "Unlocked",
            "lockDuration": 'empty',
            "lockTimestamp": timeNow
        }

        print("FamilyID: ", familyID)

        userData.insert_one(post)

        findPost = userData.find_one(post)
        session['sessionID'] = str(findPost['_id'])
        userData.update_one({'_id': ObjectId(session['sessionID'])},
                    {'$set': {'username': encrypt(username, session['sessionID']), 'loginPassword': encrypt(password, session['sessionID'])}})
        familyPost = familyData.find_one({"_id": ObjectId(familyID)})
        print("Family Document:", familyPost)

        i = 1
        while True:

            childName = f'childName{i}'
            childNumber = f'childID{i}'
            print("ChildNum: ", childNumber)
            
            if childNumber not in familyPost:

                familyData.update_one({"_id": ObjectId(familyID)}, {"$set": {childName: findPost['username'], childNumber: findPost['_id']}})
                break

            i += 1

        flash('Family member added successfully!', 'success')
        session['sessionID'] = str(findPost['_id'])

        # Redirect to set up animal ID
        return redirect(url_for('animal_id'))

    return render_template('registrationAddFamily.html', form=form, familyID=familyID)



@app.route('/master_password', methods=['GET', 'POST'])
def master_password():
    sessionID = session.get('sessionID')

    if not sessionID:
        return redirect(url_for('login'))

    findPost = userData.find_one({"_id": ObjectId(sessionID)})

    if not findPost:
        # Handle case where user data is not found
        return "User not found", 404

    email = findPost['email']

    # Check if the user is logged in and if the account is locked
    if email:
        # print("Before lockPost is assigned a variable")

        lockedPost = findPost["accountLocked"]
        print(lockedPost)
        if lockedPost == "Locked":
            flash(
                'Your account is currently locked. You cannot set or reset the master password while the account is locked.',
                'error')
            return redirect(url_for('settings'))

    if request.method == 'POST':
        master_password = request.form['master_password']

        if master_password == request.form['confirmMaster_password']:
            # Encrypt and update the master password
            encrypted_password = master_password
            userData.update_one({"_id": ObjectId(sessionID)}, {"$set": {"masterPassword": encrypt(encrypted_password, sessionID)}})

            # Check if the user has a family account
            account_type = findPost.get('accountType', 'personal')

            # Flash a success message
            flash('Master password set up successfully!', 'success')

            # Redirect based on account type
            if account_type == 'family':
                return redirect(url_for('familyPasswordList'))
            else:
                return redirect(url_for('passwordList'))

    return render_template('masterPassword.html')



@app.route('/addPassword', methods=['GET', 'POST'])
def addPassword():
    accountType = session.get('accountType', 'family')

    if request.method == 'POST':
        if 'keyword' in request.form:
            # Password generator form was submitted
            keyword = request.form.get('keyword')
            length = int(request.form.get('length', 8))  # Provide a default value in case it's not set
            use_numbers = 'numbers' in request.form
            use_symbols = 'symbols' in request.form
            replace_vowels = 'replace_vowels' in request.form
            replace_most_frequent_vowel = 'replace_most_frequent_vowel' in request.form
            remove_vowels = 'remove_vowels' in request.form
            randomize = 'randomize' in request.form

            # Validate options and generate password
            if not use_numbers and not use_symbols:
                error = "Please select at least one option: Use Numbers or Use Symbols."
            else:
                password = generate_password(keyword, length, use_numbers, use_symbols, replace_vowels, replace_most_frequent_vowel, remove_vowels, randomize)
                strength = check_password_strength(password)
                if not password:
                    error = "Failed to generate password. Ensure the keyword is shorter than the desired password length."
                else:
                    return jsonify({'password': password, 'strength': strength})

            return jsonify({'error': 'Failed to generate password.'})

        else:
            # Add password form was submitted
            website = request.form.get('website')
            username = request.form.get('username')
            password = request.form.get('password')

            additional_fields = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'account_number': request.form.get('account_number'),
                'pin': request.form.get('pin'),
                'date': request.form.get('date'),
                'other': request.form.get('other')
            }

            saveNewPassword(website, username, password, additional_fields)
            return redirect(url_for('passwordList'))


    return render_template('addPassword.html', accountType=accountType)



def saveNewPassword(website, username, password, additional_fields):
    sessionID = session.get('sessionID')

    if not sessionID:
        raise ValueError("Session ID not found. Please log in.")

    # Convert sessionID back to ObjectId
    searchPasswords = userPasswords.find_one({"_id": ObjectId(sessionID)})

    i = 1
    post = {}

    if searchPasswords is None:
        userPasswords.insert_one({"_id": ObjectId(sessionID)})
        searchPasswords = {"_id": ObjectId(sessionID)}

    while True:
        newName = f"name{i}"
        newCreatedDate = f"createdDate{i}"
        newWebsite = f"website{i}"
        newUsername = f"username{i}"
        newEmail = f"email{i}"
        newAccountNumber = f"accountNumber{i}"
        newPin = f"pin{i}"
        newDate = f"date{i}"
        newPassword = f"password{i}"
        newOther = f"other{i}"
        newPasswordLocked = f"passwordLocked{i}"

        # Check if the entry doesn't exist yet
        
        if newWebsite not in searchPasswords:
            post = {
                newName: additional_fields.get('name'),
                newCreatedDate: datetime.now(),
                newWebsite: website,
                newUsername: username,
                newEmail: additional_fields.get('email'),
                newAccountNumber: additional_fields.get('account_number'),
                newPin: additional_fields.get('pin'),
                newDate: additional_fields.get('date'),
                newPassword: password,
                newOther: additional_fields.get('other'),
                newPasswordLocked: False
            }
            break
        i += 1

    encryptableFields = [newName, newWebsite, newUsername, newAccountNumber, newPin, newDate, newPassword, newOther]
    # for item in post.keys():
    #     if item in encryptableFields and post[item] is not None:
    #         post[item] = encrypt(post[item])

    newData = {"$set": post}
    userPasswords.update_one({"_id": ObjectId(sessionID)}, newData)



@app.route('/passwordView/<name>', methods=['GET', 'POST'])
def passwordView(name):
    accountType = session.get('accountType', 'family')

    sessionID = session.get('sessionID')

    if not sessionID:
        # If sessionID is not found, redirect to login
        return redirect(url_for('login'))

    searchPasswords = userPasswords.find_one({"_id": ObjectId(sessionID)})

    if not searchPasswords:
        print("No passwords found for the user.")
        return redirect(url_for('passwordList'))

    password_data = {}

    for i in range(1, len(searchPasswords)):
        if searchPasswords.get(f"name{i}") == name:
            password_data = {
                "name": searchPasswords.get(f"name{i}"),
                "createdDate": searchPasswords.get(f"createdDate{i}"),
                "website": searchPasswords.get(f"website{i}"),
                "username": searchPasswords.get(f"username{i}"),
                "email": searchPasswords.get(f"email{i}"),
                "accountNumber": searchPasswords.get(f"accountNumber{i}"),
                "pin": searchPasswords.get(f"pin{i}"),
                "date": searchPasswords.get(f"date{i}"),
                "password": searchPasswords.get(f"password{i}"),
                "other": searchPasswords.get(f"other{i}")
            }
            break

    if request.method == 'POST':
        new_data = {
            "name": request.form.get('name'),
            "website": request.form.get('website'),
            "username": request.form.get('username'),
            "email": request.form.get('email'),
            "accountNumber": request.form.get('accountNumber'),
            "pin": request.form.get('pin'),
            "date": request.form.get('date'),
            "password": request.form.get('password'),
            "other": request.form.get('other')
        }

        updatePassword(name, new_data)

        return redirect(url_for('passwordList'))

    return render_template('passwordView.html', password_data=password_data, accountType=accountType)



def updatePassword(name, new_data):
    sessionID = session.get('sessionID')

    if not sessionID:
        # Handle the case where sessionID is not found
        print("Session ID not found. Please log in.")
        return

    searchPasswords = userPasswords.find_one({'_id': ObjectId(sessionID)})

    if not searchPasswords:
        print("No passwords found for the user.")
        return

    for i in range(1, len(searchPasswords)):
        if searchPasswords.get(f"name{i}") == name:
            update_fields = {}

            if new_data['name']:
                update_fields[f"name{i}"] = new_data['name']
            if new_data['website']:
                update_fields[f"website{i}"] = new_data['website']
            if new_data['username']:
                update_fields[f"username{i}"] = new_data['username']
            if new_data['email']:
                update_fields[f"email{i}"] = new_data['email']
            if new_data['accountNumber']:
                update_fields[f"accountNumber{i}"] = new_data['accountNumber']
            if new_data['pin']:
                update_fields[f"pin{i}"] = new_data['pin']
            if new_data['date']:
                update_fields[f"date{i}"] = new_data['date']
            if new_data['password']:
                update_fields[f"password{i}"] = new_data['password']
            if new_data['other']:
                update_fields[f"other{i}"] = new_data['other']

            # If there are any fields to update, apply the update to the database
            if update_fields:
                userPasswords.update_one({"_id": ObjectId(sessionID)}, {"$set": update_fields})
            break



@app.route('/resetPassword', methods=['GET', 'POST'])
def resetPassword():

    print("reset password being ran")
    
    sessionID = session.get('sessionID')

    if not sessionID:
        flash('User not logged in.', 'error')
        return redirect(url_for('login'))

    findPost = userData.find_one({"_id": ObjectId(sessionID)})

    if not findPost:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    # Check if the account is locked
    lockedPost = findPost['accountLocked']

    # if lockedPost == "Locked":
    #     flash(
    #         'Your account is currently locked. You cannot reset the login password while the account is locked.',
    #         'error'
    #     )
    #     return redirect(url_for('settings'))

    if request.method == 'POST':
        newPassword = request.form['newPassword']
        confirmNewPassword = request.form['confirmNewPassword']

        if newPassword == confirmNewPassword:
            # Encrypt and update the new password in the database
            encrypted_password = encrypt(newPassword, sessionID)
            userData.update_one({"_id": ObjectId(sessionID)}, {"$set": {"loginPassword": encrypted_password}})

            flash('Password reset successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match. Please try again.', 'error')

    return render_template('resetPassword.html', currentRoute='resetPassword')



@app.route('/resetPasswordLocked/<emailAddress>', methods=['GET', 'POST'])
def resetPasswordLocked(emailAddress):

    findPost = userData.find_one({"email": emailAddress})

    if not findPost:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    print("Found findPost")

    if request.method == 'POST':
        newPassword = request.form['newPassword']
        confirmNewPassword = request.form['confirmNewPassword']

        print("New Password: ", newPassword, "\nConfirmed Password: ", confirmNewPassword)

        if newPassword == confirmNewPassword:

            update = {
                "$set": {
                    'loginPassword': encrypt(newPassword, session['sessionID']),
                    'lockDuration': 0,
                    'accountLocked': 'Unlocked',
                    'lockTimestamp': datetime.now(),
                    'failedAttempt': 0
                }
            }

            # print("Update set: ", update)

            userData.update_one({'email': emailAddress}, update)

            session.pop('lock_state', None)
            session.pop('unlock_time', None)

            flash('Password reset successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match. Please try again.', 'error')

    return render_template('resetPassword.html', currentRoute='resetPasswordLocked', emailAddress=emailAddress)



@app.route('/passwordList', methods=['GET'])
def passwordList():
    sessionID = session.get('sessionID')

    if not sessionID:
        flash('Please log in to access your passwords.', 'warning')
        return redirect(url_for('login'))

    findPost = userData.find_one({'_id': ObjectId(sessionID)})

    if 'username' in session:
        # Check if the account is locked or unlocked
        if findPost.get('accountLocked') == "Locked":
            print("Account is Locked")
            return redirect(url_for('lockedPasswordList'))
        elif findPost.get('accountLocked') == "Unlocked":
            userPasswordList = getPasswords(sessionID)

            if not userPasswordList:
                return render_template('passwordList.html', passwords=[])

            return render_template('passwordList.html', passwords=userPasswordList)
    else:
        flash('Please log in to access your passwords.', 'warning')
        return redirect(url_for('login'))



@app.route('/familyPasswordList', methods=['GET', 'POST'])
def familyPasswordList():
    sessionID = session.get('sessionID')
    if not sessionID:
        flash('User not logged in. Please log in first.', 'warning')
        return redirect(url_for('login'))

    # Retrieve user data from MongoDB using the session ID
    findPost = userData.find_one({'_id': ObjectId(sessionID)})
    if not findPost:
        flash('User not found. Please try again.', 'error')
        return redirect(url_for('login'))

    # Default to sessionID if no family account is selected
    if request.method == 'POST':
        selectedAccount = request.form.get('accountSelect')
        if selectedAccount and selectedAccount != 'current_user':
            accountID = ObjectId(selectedAccount)  # Set to selected family member's ID
        else:
            accountID = ObjectId(sessionID)  # Use sessionID for the current user
    else:
        accountID = ObjectId(sessionID)

    # Check if the account is unlocked
    if findPost.get('accountLocked') == "Locked":
        return redirect(url_for('lockedPasswordList'))

    # Get family members for the dropdown menu
    familyMembers = getFamilyMembers(sessionID)

    # Retrieve passwords for the selected account
    userPasswordList = getPasswords(accountID)

    return render_template(
        'passwordListFamily.html',
        passwords=userPasswordList or [],
        family_accounts=familyMembers,
        selected_account_id=accountID
    )



def is_child_account(sessionID):
    # Search for any field starting with 'childID' that matches the sessionID
    child_record = familyData.find_one({
        "$expr": {
            "$in": [ObjectId(sessionID), {"$map": {
                "input": {"$objectToArray": "$$ROOT"},
                "as": "field",
                "in": {"$cond": [{"$regexMatch": {"input": "$$field.k", "regex": "^childID"}}, "$$field.v", None]}
            }}]
        }
    })
    # Return True if any matching child ID field is found
    return child_record is not None



@app.route('/lockedPasswordList', methods=['GET'])
def lockedPasswordList():

    findPost = userData.find_one({'_id': ObjectId(session['sessionID'])})
    print(findPost['accountLocked'])
    return render_template('lockedPasswordList.html')



@app.route('/deleteEntry/<password>', methods=['POST'])
def deleteEntry(password):
    sessionID = session.get('sessionID')

    # print("Delete function triggered with password:", password)
    # print("SessionID:", sessionID)

    if not sessionID:
        print("Session ID not found.")
        return jsonify({"success": False, "error": "Session ID not found"}), 400

    try:
        # Ensure sessionID is a valid ObjectId
        findPost = userData.find_one({'_id': ObjectId(sessionID)})
        searchPasswords = userPasswords.find_one({"_id": ObjectId(sessionID)})
        # print("Document found:", searchPasswords)

        # if not searchPasswords:
        #     print("No passwords found for the user.")
        #     return jsonify({"success": False, "error": "No passwords found"}), 404

        # Step 1: Find the field name with the specified password
        fieldNumber = None
        for field, value in searchPasswords.items():
            if value == password and field.startswith("name"):
                fieldNumber = field[len("name"):]
                # print("fieldNumber = ", fieldNumber)
                break

        
        # print("Final fieldNumber = ", fieldNumber)

        if fieldNumber is None:
            print("No matching password found.")
            return jsonify({"success": False, "error": "No matching password found"}), 404

        # Step 2: Define the fields to delete using the field number
        fieldsToDelete = {
            f"name{fieldNumber}": "",
            f"createdDate{fieldNumber}": "",
            f"website{fieldNumber}": "",
            f"username{fieldNumber}": "",
            f"email{fieldNumber}": "",
            f"accountNumber{fieldNumber}": "",
            f"pin{fieldNumber}": "",
            f"date{fieldNumber}": "",
            f"password{fieldNumber}": "",
            f"other{fieldNumber}": "",
            f"passwordLocked{fieldNumber}": ""
        }
        # print("Fields to delete:", fieldsToDelete)

        # Step 3: Use $unset to delete the fields
        updateResult = userPasswords.update_one(
            {"_id": ObjectId(sessionID)},
            {"$unset": fieldsToDelete}
        )

        if updateResult.modified_count > 0:
            print(f"Entry with password '{password}' deleted successfully.")
            # return jsonify({"success": True, "message": "Entry deleted successfully"}), 200
            account_type = findPost.get('accountType', 'personal')
            if account_type == 'family':
                return redirect(url_for('familyPasswordList'))
            else:
                return redirect(url_for('passwordList'))
        else:
            print(f"Failed to delete entry with password '{password}'.")
            return jsonify({"success": False, "error": "Failed to delete entry"}), 500

    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/settings', methods=['GET'])
def settings():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

    findPost = userData.find_one({'_id': ObjectId(sessionID)})
    print(findPost['accountLocked'])
    print(findPost['lockTimestamp'])

    return render_template('settings.html')



@app.route('/settingsFamily', methods=['GET'])
def settings_family():
    accountType = session.get('accountType', 'family')
    return render_template('settingsFamily.html', accountType=accountType)



@app.route('/familyRegister', methods=['GET', 'POST'])
def familyRegister():
    return render_template('registrationAddFamily.html')



@app.route('/add_family_account', methods=['POST'])
def add_family_account():
    data = request.get_json()
    family_email = data.get('email')

    # Ensure the email is provided
    if not family_email:
        return jsonify({"success": False, "message": "No email provided"}), 400

    # Assume the current user's email is stored in session
    current_user_email = session.get('email')
    current_user = userData.find_one({"email": current_user_email})
    sessionID = session.get('sessionID')
    familyPost = userData.find_one({"_id": ObjectId(sessionID)})
    parentID = familyPost["_id"]
    print("SessionID: ", sessionID)
    print("ParentID: ", parentID)

    if current_user:
        current_username = current_user["username"]

        # Send the email to the family member
        send_family_account_request(family_email, parentID, current_username)

        return jsonify({"success": True, "message": "Request sent successfully"})
    else:
        return jsonify({"success": False, "message": "Current user not found"}), 404



@app.route('/twoFA_verifylogin', methods=['GET'])
def two_fa_verify():
    if not session.get('email'):
        return redirect(url_for('login'))

    return render_template('2faVerifyLogin.html')



@app.route('/enable_2fa', methods=['POST'])
def enable_2fa():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'message': 'User not logged in'}), 401

    update_2fa_status(ObjectId(sessionID), True)

    return jsonify({'message': '2FA has been enabled'}), 200



@app.route('/disable_2fa', methods=['POST'])
def disable_2fa():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'message': 'User not logged in'}), 401

    update_2fa_status(ObjectId(sessionID), False)

    return jsonify({'message': '2FA has been disabled'}), 200



def update_2fa_status(sessionID, status):
    userData.update_one({"_id": ObjectId(sessionID)}, {"$set": {"2FA": status}})
    return status



@app.route('/get_2fa_status')
def get_2fa_status():
    # Retrieve sessionID from session
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'error': 'User not logged in'}), 401

    findPost = userData.find_one({'_id': ObjectId(sessionID)})

    if findPost:
        two_fa_status = findPost['2FA']
        print("2FA Status:", two_fa_status)
        return jsonify({'2fa_enabled': two_fa_status})
    else:
        return jsonify({'error': 'User not found'}), 404



@app.route('/setup_2fa', methods=['POST'])
def setup_2fa():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'message': 'User not logged in'}), 401

    user_email = request.json.get('email')
    pin = random.randint(1000, 9999)
    send_2fa_verification_email(user_email, pin, purpose='enable_2fa')
    store_pin(user_email, pin)
    return jsonify({'message': 'A 2FA PIN has been sent to your email'}), 200



@app.route('/verify_2fa_enable', methods=['POST'])
def verify_2fa():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'message': 'User not logged in'}), 401

    data = request.get_json()
    print("Received data:", data)  # Log received data

    if not data or 'email' not in data or 'pin' not in data:
        return jsonify({'message': 'Email and PIN are required'}), 400

    user_email = data['email']
    entered_pin = data['pin']
    print("Email:", user_email, "Entered PIN:", entered_pin)  # Log specifics

    if is_valid_pin(user_email, entered_pin):
        return jsonify({'message': '2FA verification successful!'}), 200
    else:
        return jsonify({'message': 'Invalid or expired PIN'}), 400



@app.route('/verify_2fa_login', methods=['POST'])
def verify_2fa_login():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'message': 'User not logged in'}), 401

    data = request.get_json()
    print("Received data for login:", data)

    if not data or 'email' not in data or 'pin' not in data:
        return jsonify({'message': 'Email and PIN are required'}), 400

    user_email = data['email']
    entered_pin = data['pin']
    print("Email:", user_email, "Entered PIN for login:", entered_pin)

    if is_valid_pin(user_email, entered_pin):
        session['2fa_verified'] = True
        return jsonify({'message': '2FA login verification successful!'}), 200
    else:
        return jsonify({'message': 'Invalid or expired PIN'}), 400



@app.route('/lock_account', methods=['POST'])
def lock_account():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

    data = request.get_json()
    lock_duration = data.get('lockDuration')

    lock_timestamp = datetime.now() + timedelta(minutes=int(lock_duration))

    update = {
        "$set": {
            'lockDuration': lock_duration,
            'accountLocked': 'Locked',
            'lockTimestamp': lock_timestamp
        }
    }

    userData.update_one({'_id': ObjectId(sessionID)}, update)

    if lock_account_in_db(lock_duration, sessionID):
        session['lock_state'] = 'locked'
        session['unlock_time'] = lock_timestamp

        return jsonify({'status': 'success', 'message': 'Account locked'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to lock account'})
    


@app.route('/check_lock', methods=['GET'])
def check_lock():
    sessionID = session.get('sessionID')

    # print("check_lock has been run")

    if not sessionID:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

    findPost = userData.find_one({'_id': ObjectId(sessionID)})
    lock_state = findPost['accountLocked']
    unlock_timestamp = findPost['lockTimestamp']
    current_time = datetime.now()

    if lock_state == 'Locked' and current_time < unlock_timestamp:
        return jsonify({'locked': True, 'unlock_time': unlock_timestamp})
    else:
        update_lock_state_in_db('Unlocked', sessionID)
        return jsonify({'locked': False})



def update_lock_state_in_db(lock_state, sessionID):
    update = {
        "$set": {
            "accountLocked": lock_state,
            "lockTimestamp": datetime.now() if lock_state == 'Unlocked' else None
        }
    }
    userData.update_one({'_id': ObjectId(sessionID)}, update)



@app.route('/unlock_account', methods=['POST'])
def unlock_account():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

    data = request.get_json()
    master_password = data.get('master_password')

    if verify_and_unlock_account(master_password, sessionID):
        session.pop('lock_state', None)
        session.pop('unlock_time', None)
        return jsonify({'status': 'success', 'message': 'Account unlocked'})
    else:
        return jsonify({'status': 'error', 'message': 'Incorrect master password'}), 401



def verify_and_unlock_account(master_password, sessionID):
    findPost = userData.find_one({'_id': ObjectId(sessionID)})
    if findPost and decrypt(findPost['masterPassword'], sessionID) == master_password:
        userData.update_one({'_id': ObjectId(sessionID)}, {"$set": {"accountLocked": "Unlocked"}})
        return True
    return False



def lock_account_in_db(lock_duration, sessionID):
    lock_duration_in_minutes = int(lock_duration)

    update = {
        "$set": {
            "accountLocked": "Locked",
            "lockTimestamp": datetime.now() + timedelta(minutes=lock_duration_in_minutes)
        }
    }
    result = userData.update_one({'_id': ObjectId(sessionID)}, update)
    return result.modified_count > 0



@app.route('/auto_unlock_account', methods=['POST'])
def auto_unlock_account():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

    userData.update_one({'_id': ObjectId(sessionID)}, {"$set": {"accountLocked": "Unlocked"}})
    return jsonify({'status': 'success', 'message': 'Account automatically unlocked'})



def store_pin(email, pin):
    temporary_2fa_storage[email] = {
        'pin': pin, 'timestamp': datetime.now()
    }



def is_valid_pin(email, entered_pin):
    pin_data = temporary_2fa_storage.get(email)
    print("Stored PIN data for", email, ":", pin_data)  # Log stored PIN data

    if pin_data and str(pin_data['pin']) == str(entered_pin):
        time_diff = datetime.now() - pin_data['timestamp']
        if time_diff.total_seconds() <= 600:  # 10 minutes validity
            return True
    return False



@app.route('/delete_account', methods=['POST'])
def delete_account():
    sessionID = session.get('sessionID')

    if not sessionID:
        return jsonify({"success": False, "message": "User not logged in."}), 401

    sessionID = ObjectId(sessionID)

    # Check if the user is authenticated
    if 'email' not in session:
        return jsonify({"success": False, "message": "User not logged in."}), 401

    email = session['email']

    # Find the user and their passwords in the database
    findData = userData.find_one({'_id': sessionID})
    findPassword = userPasswords.find_one({'_id': sessionID})

    session.pop('email', None)
    session.pop('username', None)

    if findData and findPassword:
        if sessionID == findData['_id'] and sessionID == findPassword['_id']:
            if findData['accountType'] == 'family':
                familyData.delete_one({'_id': sessionID})

            userData.delete_one({'_id': sessionID})
            userPasswords.delete_one({'_id': sessionID})

            # Clear the entire session
            session.clear()

            return jsonify({"success": True, "message": "Account successfully deleted."})
        else:
            return jsonify({"success": False, "message": "Account mismatch."})
    else:
        return jsonify({"success": False, "message": "Account not found."})



if __name__ == '__main__':
    app.run(debug=True)