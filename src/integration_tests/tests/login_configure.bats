# Integration tests for aws login configure

load 'base'

@test "Login with unconfigured default profile" {
    run aws login
    assert_failure

    run aws login
    ! read -r -d '' ERROR_MESG <<- EOF  # NOTA BENE: <<- strips tabs
		The login profile default could not be found!$CR
		Configure the profile with the following command:$CR
		$CR
		aws login configure --profile default
	EOF
    assert_output "$ERROR_MESG"
}

@test "Configure default profile" {
    run aws login configure <<- EOF  # NOTA BENE: <<- strips tabs
		https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP$CR
		netid$CR
		$CR
		push$CR
		
	EOF
    assert_output "ECP Endpoint URL [None]: Username [None]: Enable Keyring [False]: Duo Factor [None]: Role ARN [None]: "

    assert_exists "$AWSCLI_LOGIN_ROOT/.aws-login/config"
    ! read -r -d '' CONFIG_FILE <<- EOF  # NOTA BENE: <<- strips tabs
		[default]$CR
		ecp_endpoint_url = https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP$CR
		username = netid$CR
		factor = push
	EOF
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/config)" "$CONFIG_FILE"
}
