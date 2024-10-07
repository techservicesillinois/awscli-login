# Integration tests for aws login configure

load 'base'

@test "Login with unconfigured default profile" {
    run aws login
    assert_failure

    run aws login
    ! read -r -d '' ERROR_MESG <<- EOF  # NOTA BENE: <<- strips tabs
		Credential process is not set for current profile "default".$CR
		Reconfigure using:$CR
		$CR
		aws login configure
	EOF
    assert_output "$ERROR_MESG"
}

@test "Configure nonexistent default profile" {
    configure_default_profile
    test_default_profile
}

configure_default_profile() {
    run aws login configure <<- EOF  # NOTA BENE: <<- strips tabs
		https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP$CR
		netid$CR
		$CR
		push$CR
		
	EOF
    assert_output "ECP Endpoint URL [None]: Username [None]: Enable Keyring [False]: Duo Factor [None]: Role ARN [None]: "
}

test_default_profile() {
    assert_exists "$AWSCLI_LOGIN_ROOT/.aws-login/config"
    ! read -r -d '' CONFIG_FILE <<- EOF  # NOTA BENE: <<- strips tabs
		[default]$CR
		ecp_endpoint_url = https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP$CR
		username = netid$CR
		factor = push
	EOF
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/config)" "$CONFIG_FILE"
}

# Regression test for issue #212
@test "Configure empty default profile" {
    cat <<- EOF > $AWS_SHARED_CREDENTIALS_FILE
		[default]
		aws_access_key_id = 
		aws_secret_access_key =         
		aws_session_token =
		aws_security_token =
	EOF

    configure_default_profile
    test_default_profile
}

create_nonempty_default_profile() {
    cat <<- EOF > $AWS_SHARED_CREDENTIALS_FILE
		[default]
		aws_access_key_id = foo
		aws_secret_access_key = bar
	EOF
}

@test "Configure nonempty default profile" {
    create_nonempty_default_profile

    run aws login configure <<- EOF  # NOTA BENE: <<- strips tabs
		YES
		https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP$CR
		netid$CR
		$CR
		push$CR
		
	EOF
    assert_output "WARNING: Profile 'default' contains credentials.$CR
Overwrite profile 'default' to enable login? ECP Endpoint URL [None]: Username [None]: Enable Keyring [False]: Duo Factor [None]: Role ARN [None]: "
    test_default_profile
}

@test "Do not configure nonempty default profile" {
    create_nonempty_default_profile
    run aws login configure <<- EOF  # NOTA BENE: <<- strips tabs
		No
	EOF
    assert_output "WARNING: Profile 'default' contains credentials.$CR
Overwrite profile 'default' to enable login? "
    assert_not_exists "$AWSCLI_LOGIN_ROOT/.aws-login/config"
}
