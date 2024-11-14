let globalTimerInterval = null;

    // ----------------------------
    // Utility Functions
    // ----------------------------

 function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    function displayMessageAndHide(feedbackElement, message, delay = 3500) {
        feedbackElement.innerText = message;
        setTimeout(() => {
            feedbackElement.innerText = '';
        }, delay);
    }

    function updateStrengthIndicator(strength) {
        const strengthBarInner = document.getElementById('strength-bar-inner');
        if (strengthBarInner) {
            strengthBarInner.style.width = (strength.score / 5) * 100 + '%';
            strengthBarInner.style.backgroundColor = strength.color;
        }

        const strengthText = document.getElementById('strength-text');
        if (strengthText) {
            strengthText.textContent = strength.status;
        }
    }

    // ----------------------------
    // Field Management
    // ----------------------------

    // Expose addField and removeField to the global scope
    window.addField = function (field) {
        const fieldHtml = `
            <div class="field-container" id="field-${field}">
                <h4 class="mt-3">${capitalizeFirstLetter(field)}</h4>
                <div class="row mb-4">
                    <div class="col-8">
                        <input type="text" name="${field}" class="form-control">
                    </div>
                    <div class="col-1">
                        <button type="button" class="btn btn-danger btn-sm" onclick="removeField('${field}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        const fieldsContainer = document.getElementById('fields-container');
        fieldsContainer.insertAdjacentHTML('beforeend', fieldHtml);

        const dropdownMenu = document.getElementById('dropdown-menu');
        const dropdownItems = dropdownMenu.querySelectorAll('a');
        dropdownItems.forEach(item => {
            if (item.textContent.toLowerCase().replace(' ', '_') === field) {
                item.parentElement.remove();
            }
        });
    };

    window.removeField = function (field) {
        const fieldContainer = document.getElementById(`field-${field}`);
        if (fieldContainer) {
            fieldContainer.remove();
        }

        const dropdownMenu = document.getElementById('dropdown-menu');
        const dropdownItem = document.createElement('li');
        dropdownItem.innerHTML = `<a class="dropdown-item" href="javascript:void(0);" onclick="addField('${field}')">${capitalizeFirstLetter(field)}</a>`;
        dropdownMenu.appendChild(dropdownItem);
    };

    // ----------------------------
    // Account Locking
    // ----------------------------

    // All account locking related functions
    window.lockAccount = function (duration) {
        const lockTime = new Date();
        const unlockTime = new Date(lockTime.getTime() + duration * 60000);

        fetch('/lock_account', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({lockDuration: duration})
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Account Locked Successfully');

                    localStorage.setItem('lockState', 'locked');
                    localStorage.setItem('unlockTime', unlockTime.toISOString());

                    startCountdown(duration * 60000);
                    document.getElementById('toggleLockBtn').textContent = 'UNLOCK ACCOUNT';
                    document.getElementById('lockSwitch').disabled = true;
                    document.getElementById('lockRange').disabled = true;
                } else {
                    alert(data.message);
                }
            })
            .catch(error => console.error('Error:', error));
    };

    window.unlockAccount = function () {
        const masterPasswordInput = document.getElementById('masterPasswordInput');
        const masterPassword = masterPasswordInput.value;
        console.log("Attempting to unlock with master password:", masterPassword);
        fetch('/unlock_account', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({master_password: masterPassword})
        })
            .then(response => response.json())
            .then(data => {
                console.log("Response from server:", data);
                if (data.status === 'success') {
                    alert('Account Unlocked Successfully');

                    // Stop the countdown timer
                    stopCountdown();

                    // Reset lock state in local storage
                    localStorage.removeItem('lockState');
                    localStorage.removeItem('unlockTime');

                    // Reset the UI
                    resetLockUI();
                } else {
                    alert('Failed to unlock account: ' + data.message);
                }
            })
            .catch(error => console.error('Error:', error));
    };

    function startCountdown(durationInMilliseconds) {
        const endTime = Date.now() + durationInMilliseconds;
        globalTimerInterval = setInterval(() => {
            const remainingTime = endTime - Date.now();
            if (remainingTime <= 0) {
                clearInterval(globalTimerInterval);
                resetLockUI();
                autoUnlock();
            } else {
                const minutes = Math.floor(remainingTime / 60000);
                const seconds = Math.floor((remainingTime % 60000) / 1000);
                document.getElementById('lockRangeLabel').innerText = `${minutes}:${seconds.toString().padStart(2, '0')} minutes left`;
            }
        }, 1000);
    }

    function stopCountdown() {
        if (globalTimerInterval) {
            clearInterval(globalTimerInterval);
            globalTimerInterval = null;
        }
        document.getElementById('lockRangeLabel').innerText = '0 minutes';
    }

    function resetLockUI() {
        const lockSwitch = document.getElementById('lockSwitch');
        const lockRange = document.getElementById('lockRange');
        const toggleLockBtn = document.getElementById('toggleLockBtn');
        const unlockForm = document.getElementById('unlockForm');

        lockSwitch.checked = false;
        lockSwitch.disabled = false;
        lockRange.value = 0;
        lockRange.disabled = true;
        document.getElementById('lockRangeLabel').innerText = '0 minutes';
        toggleLockBtn.textContent = 'LOCK ACCOUNT';
        toggleLockBtn.disabled = true;
        unlockForm.style.display = 'none';

        if (globalTimerInterval) {
            clearInterval(globalTimerInterval);
            globalTimerInterval = null;
        }
    }

    function autoUnlock() {
        fetch('/auto_unlock_account', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Account Automatically Unlocked');

                    localStorage.removeItem('lockState');
                    localStorage.removeItem('unlockTime');

                    resetLockUI();
                } else {
                    console.error('Failed to auto unlock account: ' + data.message);
                }
            })
            .catch(error => console.error('Error:', error));
    }

// ----------------------------
// 2FA Authentication
// ----------------------------

// Function to enable 2FA and request a PIN from the user
    window.enable2FAandRequestPIN = function (userEmail, feedbackElement, twoStepVerificationInput) {
        fetch('/enable_2fa', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: userEmail})
        })
            .then(response => response.json())
            .then(data => {
                feedbackElement.innerText = data.message;

                // Reset and show the PIN input if 2FA was enabled successfully
                if (data.message === '2FA has been enabled') {
                    resetPINInput(twoStepVerificationInput);  // Reset the input field
                    requestPIN(userEmail, feedbackElement, twoStepVerificationInput);
                }
            })
            .catch(error => {
                feedbackElement.innerText = 'Error: ' + error.message;
            });
    };

// Function to disable 2FA and hide the PIN input
    window.disable2FA = function (userEmail, feedbackElement, twoStepVerificationInput) {
        fetch('/disable_2fa', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: userEmail})
        })
            .then(response => response.json())
            .then(data => {
                displayMessageAndHide(feedbackElement, data.message);
                // Hide the PIN input field when 2FA is disabled
                twoStepVerificationInput.style.display = 'none';
            })
            .catch(error => {
                displayMessageAndHide(feedbackElement, 'Error: ' + error.message);
            });
    };

// Function to request the PIN for 2FA setup
    window.requestPIN = function (userEmail, feedbackElement, twoStepVerificationInput) {
        fetch('/setup_2fa', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: userEmail})
        })
            .then(response => response.json())
            .then(data => {
                feedbackElement.innerText = data.message;
                // Ensure the PIN input field is visible after request
                twoStepVerificationInput.style.display = 'block';
            })
            .catch(error => {
                feedbackElement.innerText = 'Error: ' + error.message;
                twoStepVerificationInput.style.display = 'none';
            });
    };

// Function to verify the PIN entered by the user
    window.verifyPIN = function (userEmail, feedbackElement, twoStepVerificationInput) {
        const pin = document.getElementById('twoStepPin').value;
        const verifyPinBtn = document.getElementById('verifyPinBtn'); // Get the verify button
        if (!pin || pin.length !== 4) {
            displayMessageAndHide(feedbackElement, 'Please enter a valid 4-digit PIN.');
            return;
        }

        fetch('/verify_2fa_enable', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: userEmail, pin: pin})
        })
            .then(response => response.json())
            .then(data => {
                displayMessageAndHide(feedbackElement, data.message);
                if (data.message === '2FA verification successful!') {
                    // Hide the PIN input, verify button, and their container upon successful verification
                    document.getElementById('twoStepPin').style.display = 'none';
                    verifyPinBtn.style.display = 'none';
                    twoStepVerificationInput.style.display = 'none';
                }
            })
            .catch(error => {
                displayMessageAndHide(feedbackElement, 'Error verifying PIN: ' + error.message);
            });
    };

// Function to fetch and update the 2FA toggle based on current status
    window.update2FAToggle = function () {
        fetch('/get_2fa_status')
            .then(response => response.json())
            .then(data => {
                if (data['2fa_enabled'] !== undefined) {
                    document.getElementById('twoStepVerification').checked = data['2fa_enabled'];
                }
            })
            .catch(error => console.error('Error fetching 2FA status:', error));
    };

// Function to reset PIN input and display the verification section
    function resetPINInput(twoStepVerificationInput) {
        const pinInput = document.getElementById('twoStepPin');
        const verifyPinBtn = document.getElementById('verifyPinBtn');

        // Clear any existing value in the PIN input
        pinInput.value = '';

        // Ensure the input field and button are visible
        pinInput.style.display = 'block';
        verifyPinBtn.style.display = 'block';

        // Make sure the whole section is visible
        twoStepVerificationInput.style.display = 'block';
    }

// Helper function to display messages and hide elements after some time
    function displayMessageAndHide(element, message, timeout = 3000) {
        element.innerText = message;
        setTimeout(() => {
            element.innerText = '';  // Clear the message after 3 seconds
        }, timeout);
    }


    // ----------------------------
    // Password Management / Toggle Visibilities
    // ----------------------------

    window.togglePinVisibility = function () {
        const pinInputs = document.querySelectorAll('.pin-input');
        const togglePinIcon = document.getElementById('togglePinIcon');

        // Check the type of the first input to decide whether to show or hide the pins
        if (pinInputs[0].type === 'password') {
            // Change all inputs to type "text" to show the PIN
            pinInputs.forEach(input => input.type = 'text');
            togglePinIcon.className = 'bi bi-eye-slash';  // Change the icon to 'eye-slash' when showing
        } else {
            // Change all inputs to type "password" to hide the PIN
            pinInputs.forEach(input => input.type = 'password');
            togglePinIcon.className = 'bi bi-eye';  // Change the icon back to 'eye' when hiding
        }
    };

    window.togglePasswordVisibility = function () {
        const passwordInput = document.getElementById('password');
        const togglePasswordIcon = document.getElementById('togglePasswordIcon');
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            togglePasswordIcon.className = 'bi bi-eye-slash';
        } else {
            passwordInput.type = 'password';
            togglePasswordIcon.className = 'bi bi-eye';
        }
    };

    window.toggleConfirmPasswordVisibility = function () {
        const confirmPasswordInput = document.getElementById('confirm_password');
        const toggleConfirmPasswordIcon = document.getElementById('toggleConfirmPasswordIcon');
        if (confirmPasswordInput.type === 'password') {
            confirmPasswordInput.type = 'text';
            toggleConfirmPasswordIcon.className = 'bi bi-eye-slash';
        } else {
            confirmPasswordInput.type = 'password';
            toggleConfirmPasswordIcon.className = 'bi bi-eye';
        }
    };

    window.checkPasswordMatch = function () {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        const passwordMatchMessage = document.getElementById('passwordMatchMessage');

        if (password === confirmPassword) {
            passwordMatchMessage.style.color = 'green';
            passwordMatchMessage.innerText = 'Passwords match';
        } else {
            passwordMatchMessage.style.color = 'red';
            passwordMatchMessage.innerText = 'Passwords do not match';
        }
    };

    window.toggleMasterPasswordVisibility = function () {
        const passwordInput = document.getElementById('master_password');
        const togglePasswordIcon = document.getElementById('toggleMasterPasswordIcon');
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            togglePasswordIcon.className = 'bi bi-eye-slash';
        } else {
            passwordInput.type = 'password';
            togglePasswordIcon.className = 'bi bi-eye';
        }
    };

    window.toggleConfirmMasterPasswordVisibility = function () {
        const confirmMasterPasswordInput = document.getElementById('confirm_master_password');
        const toggleConfirmMasterPasswordIcon = document.getElementById('toggleConfirmMasterPasswordIcon');
        if (confirmMasterPasswordInput.type === 'password') {
            confirmMasterPasswordInput.type = 'text';
            toggleConfirmMasterPasswordIcon.className = 'bi bi-eye-slash';
        } else {
            confirmMasterPasswordInput.type = 'password';
            toggleConfirmMasterPasswordIcon.className = 'bi bi-eye';
        }
    };

    window.checkMasterPasswordMatch = function () {
        const masterPassword = document.getElementById('master_password').value;
        const confirmMasterPassword = document.getElementById('confirm_master_password').value;
        const passwordMatchMessage = document.getElementById('passwordMatchMessage');

        if (masterPassword === confirmMasterPassword) {
            passwordMatchMessage.style.color = 'green';
            passwordMatchMessage.innerText = 'Passwords match';
        } else {
            passwordMatchMessage.style.color = 'red';
            passwordMatchMessage.innerText = 'Passwords do not match';
        }
    };


// ----------------------------
// Password Generation
// ----------------------------

    window.generatePassword = function () {
        const phraseInput = document.getElementById('phrase-input');
        const lengthInput = document.getElementById('length-input');
        const generatedPasswordField = document.getElementById('generated-password');
        const excludeNumbersCheckbox = document.getElementById('exclude_numbers');
        const excludeSymbolsCheckbox = document.getElementById('exclude_symbols');
        const replaceVowelsCheckbox = document.getElementById('replace_vowels');
        const randomizeCheckbox = document.getElementById('randomize');

        var phrase = phraseInput.value;
        var length = parseInt(lengthInput.value, 10);
        var excludeNumbers = excludeNumbersCheckbox.checked;
        var excludeSymbols = excludeSymbolsCheckbox.checked;
        var replaceVowels = replaceVowelsCheckbox.checked;
        var randomize = randomizeCheckbox.checked;

        // If the length is smaller than the phrase or phrase is empty, show an error
        if (!phrase || length < phrase.replace(/\s+/g, '').length) {
            generatedPasswordField.value = "Error: Check phrase length.";
            updateStrengthIndicator({status: "Weak", score: 0, color: "red"});
            return;
        }

        var newPassword = generatePasswordLogic(phrase, length, excludeNumbers, excludeSymbols, replaceVowels, randomize);
        generatedPasswordField.value = newPassword;

        checkPasswordStrength(newPassword);
    };

// ----------------------------
// Password Refresh
// ----------------------------

    window.refreshPassword = function () {
        const phraseInput = document.getElementById('phrase-input');
        const lengthInput = document.getElementById('length-input');
        const generatedPasswordField = document.getElementById('generated-password');
        const excludeNumbersCheckbox = document.getElementById('exclude_numbers');
        const excludeSymbolsCheckbox = document.getElementById('exclude_symbols');
        const replaceVowelsCheckbox = document.getElementById('replace_vowels');
        const randomizeCheckbox = document.getElementById('randomize');

        const phrase = phraseInput.value;
        const length = parseInt(lengthInput.value, 10);
        const excludeNumbers = excludeNumbersCheckbox.checked;
        const excludeSymbols = excludeSymbolsCheckbox.checked;
        const replaceVowels = replaceVowelsCheckbox.checked;
        const randomize = randomizeCheckbox.checked;

        if (!phrase || length < phrase.replace(/\s+/g, '').length) {
            generatedPasswordField.value = "Error: Check phrase length.";
            return;
        }

        const newPassword = generatePasswordLogic(phrase, length, excludeNumbers, excludeSymbols, replaceVowels, randomize);
        generatedPasswordField.value = newPassword;
    };

    document.addEventListener('DOMContentLoaded', function () {
        const refreshButton = document.querySelector('.refreshButton');
        if (refreshButton) {
            refreshButton.addEventListener('click', refreshPassword);
        }
    });


// Function to dynamically update the length input based on the phrase input
    window.updateLengthInput = function () {
        const phraseInput = document.getElementById('phrase-input');
        const lengthInput = document.getElementById('length-input');

        var phrase = phraseInput.value;
        var minLength = phrase.replace(/\s+/g, '').length; // Remove spaces from the phrase
        lengthInput.min = minLength;

        if (lengthInput.value < minLength) {
            lengthInput.value = minLength;
        }
    };

// Add event listener to dynamically adjust length when phrase input changes
    document.addEventListener('DOMContentLoaded', function () {
        const phraseInput = document.getElementById('phrase-input');
        if (phraseInput) {
            phraseInput.addEventListener('input', updateLengthInput);
        }
    });

    function generatePasswordLogic(phrase, length, excludeNumbers = false, excludeSymbols = false, replaceVowels = false, randomize = false) {
        // Always start with letters as the base characters
        var characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

        // Remove spaces from the phrase
        phrase = phrase.replace(/\s+/g, '');

        // Add numbers and symbols unless excluded
        if (!excludeNumbers) characters += "0123456789";
        if (!excludeSymbols) characters += "!@#$%^&*()_-+=<>?/[]{}|";

        // If the phrase is longer than the desired length, truncate it
        if (!phrase || length < phrase.length) return "";

        // Extended vowel map with phoneme-based replacements
        if (replaceVowels) {
            const vowelMap = {
                'a': ['@', 'A', 'æ', '4', 'â', 'ä'],
                'e': ['3', 'E', '€', 'ê', 'é', 'ë'],
                'i': ['1', 'I', '!', 'î', 'ï', 'í'],
                'o': ['0', 'O', 'ø', 'ô', 'ö', 'ó'],
                'u': ['U', 'u', 'ù', 'û', 'ü', 'ú']
            };

            // Replace vowels in the phrase based on the extended vowel map
            phrase = phrase.split('').map(function (char) {
                return vowelMap[char.toLowerCase()] ?
                    vowelMap[char.toLowerCase()][Math.floor(Math.random() * vowelMap[char.toLowerCase()].length)]
                    : char;
            }).join('');
        }

        // Revert numbers and symbols if they are excluded
        if (excludeNumbers) {
            phrase = phrase.replace(/1/g, 'i').replace(/3/g, 'e').replace(/0/g, 'o');
        }
        if (excludeSymbols) {
            phrase = phrase.replace(/@/g, 'a').replace(/\$/g, 's').replace(/#/g, 'h');
        }

        // Randomize the phrase characters if the option is selected
        if (randomize) {
            phrase = phrase.split('').sort(() => 0.5 - Math.random()).join('');
        }

        // Map the phrase to its phoneme equivalents
        var phonemeMap = {
            'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F',
            'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J', 'k': 'K', 'l': 'L',
            'm': 'M', 'n': 'N', 'o': 'O', 'p': 'P', 'q': 'Q', 'r': 'R',
            's': 'S', 't': 'T', 'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X',
            'y': 'Y', 'z': 'Z',
            // Phoneme-based replacements
            'ph': 'F', 'gh': 'G', 'ch': 'C', 'sh': 'S', 'th': 'T'
        };

        // Map the phrase to its phoneme equivalents
        var phrasePhoneme = phrase.split('').map(function (char) {
            return phonemeMap[char.toLowerCase()] || char;
        }).join('');

        // Prevent extra characters from being added
        var password = phrasePhoneme.slice(0, length);

        return password;
    }


    document.addEventListener('DOMContentLoaded', function () {
        const passwordInput = document.getElementById('generated-password'); // The password field
        const phraseInput = document.getElementById('phrase-input'); // The phrase input field
        const lengthInput = document.getElementById('length-input'); // The length input field

        // Listen for changes in the generated password
        if (passwordInput) {
            passwordInput.addEventListener('input', function () {
                const password = passwordInput.value;
                checkPasswordStrength(password);
            });
        }

        // Listen for changes in the phrase input and regenerate the password
        if (phraseInput) {
            phraseInput.addEventListener('input', function () {
                updateLengthInput(); // Dynamically adjust the length based on the phrase
                refreshPassword(); // Regenerate the password when the phrase changes
            });
        }
    });

// Dynamically update the length input based on the phrase input
    window.updateLengthInput = function () {
        const phraseInput = document.getElementById('phrase-input');
        const lengthInput = document.getElementById('length-input');

        const phrase = phraseInput.value;
        const minLength = phrase.replace(/\s+/g, '').length; // Remove spaces and calculate the length of the phrase
        lengthInput.value = minLength; // Automatically set the length input value based on the phrase length
    };

// Dynamically regenerate and check password strength
    window.refreshPassword = function () {
        const phraseInput = document.getElementById('phrase-input');
        const lengthInput = document.getElementById('length-input');
        const generatedPasswordField = document.getElementById('generated-password');

        const excludeNumbersCheckbox = document.getElementById('exclude_numbers');
        const excludeSymbolsCheckbox = document.getElementById('exclude_symbols');
        const replaceVowelsCheckbox = document.getElementById('replace_vowels');
        const randomizeCheckbox = document.getElementById('randomize');

        const phrase = phraseInput.value;
        const length = parseInt(lengthInput.value, 10);
        const excludeNumbers = excludeNumbersCheckbox.checked;
        const excludeSymbols = excludeSymbolsCheckbox.checked;
        const replaceVowels = replaceVowelsCheckbox.checked;
        const randomize = randomizeCheckbox.checked;

        // Validate the phrase and length
        if (!phrase || length < phrase.replace(/\s+/g, '').length) {
            generatedPasswordField.value = "Error: Check phrase length.";
            updateStrengthIndicator({status: "Weak", score: 0, color: "red"});
            return;
        }

        // Generate the password using the current phrase and options
        const newPassword = generatePasswordLogic(phrase, length, excludeNumbers, excludeSymbols, replaceVowels, randomize);
        generatedPasswordField.value = newPassword;

        // Check password strength after generating it
        checkPasswordStrength(newPassword);
    };

    window.checkPasswordStrength = function (password) {
        var strength = {status: 'Weak', score: 0, color: 'red'};

        // Check if password is empty
        if (!password) {
            updateStrengthIndicator(strength);
            return;
        }

        // Length check: more points for longer passwords
        if (password.length >= 16) {
            strength.score += 2;
        } else if (password.length >= 12) {
            strength.score += 1.5;
        } else if (password.length >= 8) {
            strength.score += 1;
        } else {
            strength.score += 0.5;
        }

        // Check for digits
        if (/\d/.test(password)) {
            strength.score += 1;
        }

        // Check for uppercase and lowercase combination
        if (/[A-Z]/.test(password) && /[a-z]/.test(password)) {
            strength.score += 1;
        }

        // Check for symbols
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            strength.score += 1;
        }

        // Check for letters mixed with numbers or symbols
        if (/[a-zA-Z]/.test(password) && (/\d/.test(password) || /[!@#$%^&*(),.?":{}|<>]/.test(password))) {
            strength.score += 1;
        }

        // Penalty for common patterns (e.g., "123", "password", "abc", "qwerty")
        var commonPatterns = ['123', 'password', 'abc', 'qwerty'];
        commonPatterns.forEach(function (pattern) {
            if (password.toLowerCase().includes(pattern)) {
                strength.score -= 1;
            }
        });

        // Penalty for consecutive identical characters
        if (/(\w)\1{2,}/.test(password)) { // e.g., "aaa" or "111"
            strength.score -= 1;
        }

        // Penalty for too many repeated characters
        var charCount = {};
        for (var i = 0; i < password.length; i++) {
            var char = password[i];
            charCount[char] = charCount[char] ? charCount[char] + 1 : 1;
        }
        var maxRepetition = Math.max(...Object.values(charCount));
        if (maxRepetition > password.length / 2) {
            strength.score -= 1;
        }

        // Ensure score does not fall below zero
        strength.score = Math.max(0, strength.score);

        // Update the status and color based on score
        if (strength.score >= 5) {
            strength.status = 'Very Strong';
            strength.color = 'green';
        } else if (strength.score >= 4) {
            strength.status = 'Strong';
            strength.color = 'lightgreen';
        } else if (strength.score >= 3) {
            strength.status = 'Moderate';
            strength.color = 'orange';
        } else {
            strength.status = 'Weak';
            strength.color = 'red';
        }

        // Update the UI (assuming you have elements to show strength status and color)
        updateStrengthIndicator(strength);

        return strength;
    };

    function updateStrengthIndicator(strength) {
        const strengthBarInner = document.getElementById('strength-bar-inner');
        const strengthText = document.getElementById('strength-text');

        if (strengthBarInner) {
            strengthBarInner.style.width = (strength.score / 5) * 100 + '%';
            strengthBarInner.style.backgroundColor = strength.color;
        }

        if (strengthText) {
            strengthText.textContent = strength.status;
        }
    }


// ----------------------------
// Clipboard Functions
// ----------------------------

    // Function to copy the generated password to clipboard
    window.copyToClipboard = function () {
        const passwordField = document.getElementById('generated-password');
        const clipboardButton = document.getElementById('clipboard-button');
        const clipboardIcon = document.getElementById('clipboard-icon');

        // Ensure there's a password to copy
        if (passwordField && passwordField.value) {
            // Select the text in the password field
            passwordField.select();
            passwordField.setSelectionRange(0, 99999);

            // Copy the text inside the password field to clipboard
            try {
                document.execCommand('copy');
                clipboardIcon.classList.remove('bi-clipboard'); // Remove the default icon
                clipboardIcon.classList.add('bi-clipboard-check'); // Add the "check" icon to indicate success

                // Reset the icon and button text after 2 seconds
                setTimeout(function () {
                    clipboardIcon.classList.remove('bi-clipboard-check');
                    clipboardIcon.classList.add('bi-clipboard');
                }, 2000);
            } catch (err) {
                clipboardButton.textContent = "Failed to copy"; // Indicate if copying failed
            }
        } else {
            clipboardButton.textContent = "No password to copy"; // Indicate no password available to copy
        }
    };

    window.copyWebsite = function () {
        var field = document.getElementById('website-input');
        field.select();
        document.execCommand('copy');
        changeIconTemporarily('website-icon');
    };

    window.copyEmail = function () {
        var field = document.getElementById('email-input');
        field.select();
        document.execCommand('copy');
        changeIconTemporarily('email-icon');
    };

    window.copyPassword = function () {
        var field = document.getElementById('password-input');
        field.select();
        document.execCommand('copy');
        changeIconTemporarily('password-icon');
    };

    function changeIconTemporarily(iconId) {
        var icon = document.getElementById(iconId);
        if (icon) {
            icon.className = 'bi bi-clipboard-check';

            setTimeout(function () {
                icon.className = 'bi bi-clipboard';
            }, 2000); // Reset icon after 2 seconds
        }
    }

    // ----------------------------
    // Account Deletion
    // ----------------------------

    window.deleteAccount = function () {
        if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
            fetch('/delete_account', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        window.location.href = '/login';
                    } else {
                        alert(data.message);
                    }
                })
                .catch(error => console.error('Error:', error));
        }
    };

    // ----------------------------
    // Family Account Management
    // ----------------------------

    window.showFamilyAccountInput = function () {
        var familyAccountInput = document.getElementById('familyAccountInput');
        if (familyAccountInput) {
            familyAccountInput.style.display = familyAccountInput.style.display === 'none' || familyAccountInput.style.display === '' ? 'block' : 'none';
        }
    };

    window.addFamilyAccount = function () {
        var familyEmail = document.getElementById('familyEmail').value;

        fetch('/add_family_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({email: familyEmail})
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Request sent successfully!");
                    document.getElementById('familyAccountInput').style.display = 'none';
                } else {
                    alert("Error: " + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    };

    function deleteChildAccount() {
    const selectedChildID = document.getElementById('deleteChildAccountSelect').value;
    if (!selectedChildID) {
        alert('Please select a child account to delete.');
        return;
    }

    if (confirm('Are you sure you want to delete this child account? This action cannot be undone.')) {
        fetch('/delete_child_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ childID: selectedChildID })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Child account deleted successfully.');
                window.location.reload();  // Reloads the page to refresh the list
            } else {
                alert('Failed to delete child account: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the child account.');
        });
    }
}



    // ----------------------------
    // Alert Dismissal
    // ----------------------------

    window.dismissAlerts = function () {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            setTimeout(function () {
                alert.style.opacity = '0';
                setTimeout(function () {
                    alert.remove();
                }, 500);
            }, 3000); // 3s before starting the fade out
        });
    };

    // ----------------------------
    // Form Submission and Validation
    // ----------------------------

    window.validateForm = function (event) {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        if (!email || !password) {
            alert("Email and password are required!");
            event.preventDefault();
        }
    };

    // ----------------------------
    // Password List Management
    // ----------------------------

    // window.deleteEntry = function (website, email, password) {
    //     // Log the values to check if they are properly passed
    //     console.log('Website:', website);
    //     console.log('Email:', email);
    //     console.log('Password:', password);

    //     if (!website || !email || !password) {
    //         alert('Error: Missing required data.');  // Check if any field is missing
    //         return;
    //     }

    //     if (confirm('Are you sure you want to delete this entry?')) {
    //         const data = {website: website, email: email, password: password};
    //         console.log('Sending data:', data);  // Log the data you're sending

    //         fetch('/delete-password', {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json'
    //             },
    //             body: JSON.stringify(data)
    //         }).then(response => response.json())
    //             .then(data => {
    //                 if (data.status === 'success') {
    //                     alert('Entry deleted successfully');
    //                     window.location.reload();
    //                 } else {
    //                     alert('Failed to delete entry: ' + data.message);
    //                 }
    //             }).catch(error => {
    //             console.error('Error:', error);
    //             alert('An error occurred while deleting the entry');
    //         });
    //     }
    // };



function deleteEntry(password) {
    console.log("Password identifier received:", password);

    if (!password) {
        alert("Password identifier is missing!");
        return;
    }

    fetch(`/deleteEntry/${password}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log("Server responded with status:", response.status);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert("Failed to delete entry.");
        }
    })
    .catch(error => console.error('Fetch error:', error));  // Logs any network issues
} 


    // ----------------------------
    // Animal ID Functionality
    // ----------------------------

    window.toggleSubmitButton = function () {
        const submitButton = document.getElementById('submit-button');
        const radioButtons = document.querySelectorAll('input[name="animal"]');
        let isChecked = false;
        radioButtons.forEach((radio) => {
            if (radio.checked) {
                isChecked = true;
            }
        });
        if (submitButton) {
            submitButton.disabled = !isChecked;
        }
    };

    window.toggleSecurityCheckButton = function () {
        const checkBox = document.getElementById('securityCheck');
        const submitButton = document.getElementById('confirmButton');
        if (submitButton && checkBox) {
            submitButton.disabled = !checkBox.checked;
        }
    };

    window.preventImageClickPropagation = function () {
        var img = document.querySelector('.animal-img');
        if (img) {
            img.addEventListener('click', function (event) {
                event.stopPropagation();
            });
        }
    };

    // ----------------------------
    // Event Listeners Initialization
    // ----------------------------

    document.addEventListener('DOMContentLoaded', function () {
        // Initialize Field Management (if needed)
        // Initialize Account Locking UI
        initializeLockingUI();

        // Initialize 2FA Toggle State
        update2FAToggle();

        // Initialize Password Strength (if applicable)
        var initialPassword = document.getElementById('generated-password')?.value;
        if (initialPassword) {
            checkPasswordStrength(initialPassword);
        }

        // Initialize Alert Dismissal
        dismissAlerts();

        // Initialize Animal Image Click Prevention
        preventImageClickPropagation();

        // Form Submission Validation
        const form = document.querySelector("form");
        if (form) {
            form.addEventListener("submit", validateForm);
        }

        // Password Generation Event Listeners
        const generatedPasswordField = document.getElementById('generated-password');
        if (generatedPasswordField) {
            generatedPasswordField.addEventListener('input', function () {
                var password = generatedPasswordField.value;
                var strength = checkPasswordStrength(password);
                updateStrengthIndicator(strength);
            });
        }

        // Initialize Locking UI based on saved state
        initializeLockingState();
    });

    // ----------------------------
    // Account Locking UI Initialization
    // ----------------------------

    function initializeLockingUI() {
        const lockSwitch = document.getElementById('lockSwitch');
        const lockRange = document.getElementById('lockRange');
        const lockRangeLabel = document.getElementById('lockRangeLabel');
        const unlockForm = document.getElementById('unlockForm');
        const toggleLockBtn = document.getElementById('toggleLockBtn');
        const masterPasswordInput = document.getElementById('masterPasswordInput');
        const toggleLockVisibilityBtn = document.getElementById('toggleLockVisibilityBtn');
        const toggleLockVisibilityIcon = document.getElementById('toggleLockVisibilityIcon');
        const unlockAccountBtn = document.getElementById('unlockAccountBtn');

        if (unlockAccountBtn) {
            unlockAccountBtn.addEventListener('click', unlockAccount);
        }

        function updateRangeLabel() {
            const rangeValue = lockRange.value;
            lockRangeLabel.innerText = rangeValue * 10 + ' minutes';
        }

        lockRange.addEventListener('input', updateRangeLabel);

        const savedLockState = localStorage.getItem('lockState');
        const savedUnlockTime = localStorage.getItem('unlockTime');

        if (savedLockState === 'locked' && savedUnlockTime && new Date(savedUnlockTime) > new Date()) {
            if (lockSwitch) lockSwitch.checked = true;
            if (lockRange) lockRange.disabled = true;
            if (toggleLockBtn) {
                toggleLockBtn.disabled = false;
                toggleLockBtn.textContent = 'UNLOCK ACCOUNT';
            }
            if (unlockForm) unlockForm.style.display = 'none';
            if (savedUnlockTime) {
                startCountdown(new Date(savedUnlockTime) - new Date());
            }
        } else {
            resetLockUI();
        }

        if (lockSwitch) {
            lockSwitch.addEventListener('change', function () {
                if (lockRange) lockRange.disabled = !this.checked;
                if (toggleLockBtn) toggleLockBtn.disabled = !this.checked;
                if (!this.checked) {
                    if (toggleLockBtn) toggleLockBtn.textContent = 'LOCK ACCOUNT';
                    if (unlockForm) unlockForm.style.display = 'none';
                    localStorage.removeItem('lockState');
                    localStorage.removeItem('unlockTime');
                    if (globalTimerInterval) {
                        clearInterval(globalTimerInterval);
                        globalTimerInterval = null;
                    }
                }
            });
        }

        if (toggleLockBtn) {
            toggleLockBtn.addEventListener('click', function () {
                if (this.textContent.trim() === 'LOCK ACCOUNT') {
                    const lockDuration = lockRange.value * 10;
                    lockAccount(lockDuration);
                } else {
                    if (unlockForm) {
                        unlockForm.style.display = unlockForm.style.display === 'none' ? 'block' : 'none';
                        this.textContent = unlockForm.style.display === 'block' ? 'CANCEL UNLOCK' : 'LOCK ACCOUNT';
                    }
                }
            });
        }

        if (masterPasswordInput) {
            masterPasswordInput.addEventListener('keydown', function (event) {
                if (event.key === 'Enter') {
                    unlockAccount();
                }
            });
        }

        if (toggleLockVisibilityBtn) {
            toggleLockVisibilityBtn.addEventListener('click', function () {
                const type = masterPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                masterPasswordInput.setAttribute('type', type);
                toggleLockVisibilityIcon.classList.toggle('bi-eye-slash');
                toggleLockVisibilityIcon.classList.toggle('bi-eye');
            });
        }
    }

    function initializeLockingState() {
        // Any additional initialization for locking can go here
    }

    // ----------------------------
    // 2FA Event Listeners Initialization
    // ----------------------------

    document.addEventListener('DOMContentLoaded', function () {
        const twoStepVerificationCheckbox = document.getElementById('twoStepVerification');
        const twoStepVerificationInput = document.getElementById('twoStepVerificationInput');
        const verifyPinBtn = document.getElementById('verifyPinBtn');
        const feedbackElement = document.getElementById('twoStepFeedback');
        const userEmailElement = document.getElementById('userEmail');
        const userEmail = userEmailElement ? userEmailElement.textContent : '';

        if (twoStepVerificationCheckbox) {
            twoStepVerificationCheckbox.addEventListener('change', function () {
                if (this.checked) {
                    enable2FAandRequestPIN(userEmail, feedbackElement, twoStepVerificationInput);
                } else {
                    disable2FA(userEmail, feedbackElement, twoStepVerificationInput);
                }
            });
        }

        if (verifyPinBtn) {
            verifyPinBtn.addEventListener('click', function () {
                verifyPIN(userEmail, feedbackElement, twoStepVerificationInput);
            });
        }
    });

    // ----------------------------
    // 2FA Login (If 2FA Enabled)
    // ----------------------------

    document.querySelectorAll('.pin-input').forEach((input, index, arr) => {
        input.addEventListener('input', () => {
            if (input.value.length === 1 && index < arr.length - 1) {
                arr[index + 1].focus();
            }
        });
    });

    document.getElementById('verify-2fa-form').addEventListener('submit', function (e) {
        e.preventDefault();  // Prevent default form submission

        const email = document.querySelector('input[name="email"]').value;
        const pin = [
            document.getElementById('pin1').value,
            document.getElementById('pin2').value,
            document.getElementById('pin3').value,
            document.getElementById('pin4').value
        ].join('');

        const feedbackElement = document.getElementById('feedback');

        if (pin.length !== 4) {
            feedbackElement.innerText = 'Please enter the complete 4-digit PIN.';
            return;
        }

        // Send a POST request for 2FA login verification
        fetch('/verify_2fa_login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email, pin: pin})
        })
            .then(response => response.json())
            .then(data => {
                feedbackElement.innerText = data.message;
                if (data.message === '2FA login verification successful!') {
                    window.location.href = '/animalID_verification';  // Redirect after successful 2FA login
                }
            })
            .catch(error => {
                feedbackElement.innerText = 'Error: ' + error.message;
            });
    })



