# CS302-MasterVault
MasterVault is a Flask-based password management application designed for secure storage and management of passwords. It features functionalities like user authentication, password generation, encryption, two-factor authentication (2FA), and family account management.


## Features
- **Secure Login & Registration**: Users can create accounts and log in securely.
  
- **Password Management**: Add, view, edit, delete, or hide saved passwords in real time.

- **Password Generation**: Generate strong, unique passwords with customizable options.
  
- **Password Strength Checker**: Evaluates the strength of passwords in real time.
  
- **Two-Factor Authentication (2FA)**: Adds an extra layer of security to user accounts.
  
- **Account Locking**: Temporarily lock accounts for a specified duration.
  
- **Encryption**: Sensitive data is encrypted using 256-AES for secure storage.
  
- **Email Notifications**: Sends emails for account verification, 2FA PINs, failed login alerts, and family management updates.
  
- **Personal and Family Accounts**: Separate account types for individual users and family account management.
  
- **Family Account Management**: Add, manage, or delete family members under a single family account.
  
- **Animal ID Verification**: Adds an additional security layer using unique animal identifiers.
  
- **Failed Login Attempts**: Users are notified via email after certain amount of login attempts are made.
  
- **MasterVault Extension**: Includes a browser extension for password generation and auto-filling generated passwords onto websites.



## Setup & Installation

### MasterVault Web Application
1. **Clone the Repository:** Start by cloning this repository to your local machine.
   
2. **Install Dependencies:** Use `pip install -r requirements.txt` to install the necessary Python packages.
   
3. **Run the Application:** Execute `app.py` to start the Flask server.

### MasterVault Extension Installation (Chrome)
1. **Build the Extension:**
   - Navigate to the MasterVaultExtension directory.
   - Install dependencies:
     ```
     npm install
     npm run build
     ```
    - A `dist` folder will be generated.
  
2. **Add Extension to Chrome:**
    - Open Chrome and navigate to `chrome://extensions/`.
    - Enable "Developer Mode" in the top-right corner.
    - Click "Load unpacked" and select the `dist` folder.
  
3. **Login:**
    - Login to your MasterVault account in the extension.
    - Your extension is ready to use.

## Usage
1. **Register:** Create a new account by providing a username, email, and password.

2. **Animal ID Verification:** Set up and use Animal ID for an additional security measure.
  
3. **Login:** Access your account using your credentials.
  
4. **Password Management:** Add new passwords, view saved ones, or modify existing entries.
  
5. **Generate Password:** Use the built-in tool to create strong passwords.
  
6. **Account Settings:** Enable/disable 2FA, lock your account, or reset your password.

7. **Family Accounts:** Add family memmbers and manage them under a single family account. View, delete, or manage family members from your account settings.

8. **MasterVault Extension:** Use the browser extension for password generation and auto-filling generated passwords onto websites.


## Security Features
* **Encryption:** All sensitive data is encrypted using 256-AES encryption.

* **Master Password:** Provides an additional layer of security by requiring a master password to access all saved passwords.
  
* **2FA:** Optional two-factor authentication adds an extra layer of security.
  
* **Account Locking:** Temporarily lock your account to prevent unauthorized access.

* **Animal ID Verification:** Adds an additional layer of security with unique identifiers.

  

## Email Integration
* **Verification Emails:** Sent upon account creation.
  
* **2FA Emails:** Sent when 2FA is enabled, containing a PIN for verification.

* **Add Family Member Emails:** Sent to invite family members to join the family account, containing instructions for account setup.

* **Failed Login Alerts:** After three failed attempts, the owner receives an email alerting them of suspicious activity. If the failed attempts reach five or more, the account is automatically locked. The email sent at this stage includes a secure link that allows the user to reset their password.


   



