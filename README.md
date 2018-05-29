# CSH Self Service Account Management

[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

### Features
* Account Recovery 
  * Based on information stored about the user, allow them to reset a potentially forgotten password.
  * Administrators can also manually generate these reset tokens, allowing for manual identity verification.
* Two Factor Management
  * Allow users to generate and verify a two factor secret which will then be created in both Keycloak and FreeIPA.
  * Also provides the ability to disable two-factor, removing the secret from both locations.
* Password Changing
  * Provide a central web interface for changing known passwords.

### Recovery Techniques
* SMS Number
  * Uses common carrier email to SMS bridges to send temporary verification pin. Once verified the user is redirected to the reset page.
* External Email
  * Emails a direct link to the reset page.
 
