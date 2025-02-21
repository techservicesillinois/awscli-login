FACTORS = ['auto', 'push', 'passcode', 'sms', 'phone']
YES = ['y', 'yes']

WARNING_PROFILE_CONTAINS_CREDS = "WARNING: Profile '%s' contains credentials."
ERROR_INVALID_PROFILE_ROLE = "Profile role is invalid: %s\a"
OVERWRITE_PROFILE = "Overwrite profile '%s' to enable login? "

DUO_HEADER_FACTOR = 'X-Shibboleth-Duo-Factor'
DUO_HEADER_PASSCODE = 'X-Shibboleth-Duo-Passcode'

ERROR_INVALID_CRED_PROC_PATH = \
    "credential_process:%s: Is not on $PATH or not executable."
ERROR_INVALID_CRED_PROC_WRONG_PROFILE_ARG = \
    "credential_process:%s: --profile not set to current profile '%s'."
ERROR_INVALID_CRED_PROC_MISSING_PROFILE_ARG = \
    "credential_process:%s: --profile argument not set."
