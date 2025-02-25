# Integration tests for aws login & logout using two configured profiles

load 'duo'

init() {
    ! read -r -d '' CREDS_AWS_FILE <<- EOF
		[default]$CR
		credential_process = aws-login --profile default$CR
		[test]$CR
		credential_process = aws-login --profile test
	EOF
    # The expiration used to end in Z now in +00:00. They each
    # indicate the same UTC time. When login is run as a plugin you
    # get Z, when you run it from the credentials script as a
    # standalone you get +00:00. I don't know why.
    ! read -r -d '' CREDS <<- EOF
		[default]$CR
		aws_access_key_id = ABCDEFGHIJKLMNOPQRST$CR
		aws_secret_access_key = SUPER DUPER SECRET KEY$CR
		aws_session_token = BOGUS TOKEN$CR
		aws_security_token = BOGUS TOKEN$CR
		expiration = 2222-09-06T22:28:39+00:00$CR
		aws_principal_arn = arn:aws:iam::123456789010:saml-provider/shibboleth.illinois.edu$CR
		aws_role_arn = arn:aws:iam::123456789010:role/Team$CR
		username = netid$CR
		$CR
		[test]$CR
		aws_access_key_id = ABCDEFGHIJKLMNOPQRST$CR
		aws_secret_access_key = SUPER DUPER SECRET KEY$CR
		aws_session_token = BOGUS TOKEN$CR
		aws_security_token = BOGUS TOKEN$CR
		expiration = 2222-09-06T22:28:39+00:00$CR
		aws_principal_arn = arn:aws:iam::123456789010:saml-provider/shibboleth.illinois.edu$CR
		aws_role_arn = arn:aws:iam::123456789010:role/Team$CR
		username = test
	EOF

    ! read -r -d '' CREDS_AFTER_LOGOUT <<- EOF
		[test]$CR
		aws_access_key_id = ABCDEFGHIJKLMNOPQRST$CR
		aws_secret_access_key = SUPER DUPER SECRET KEY$CR
		aws_session_token = BOGUS TOKEN$CR
		aws_security_token = BOGUS TOKEN$CR
		expiration = 2222-09-06T22:28:39+00:00$CR
		aws_principal_arn = arn:aws:iam::123456789010:saml-provider/shibboleth.illinois.edu$CR
		aws_role_arn = arn:aws:iam::123456789010:role/Team$CR
		username = test
	EOF

}

login_test() {
    assert_equal "$(<$AWS_SHARED_CREDENTIALS_FILE)" "$CREDS_AWS_FILE"
    run aws login --load-http-traffic cassettes/login.yaml --password foo <<< 0
    assert_success
    run aws --profile test login --load-http-traffic cassettes/login.yaml --password foo <<< 0
    assert_success

    assert_equal "$(<$AWS_SHARED_CREDENTIALS_FILE)" "$CREDS_AWS_FILE"
    assert_exists "$AWSCLI_LOGIN_ROOT/.aws-login/credentials"
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" "$CREDS"
}

@test "Login and logout with two profiles" {
    init  # Load shared vars
    login_test # Run login and shared tests

    run aws logout
    assert_success
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" "$CREDS_AFTER_LOGOUT"

    run aws logout
    assert_failure
    assert_output "Already logged out!"
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" "$CREDS_AFTER_LOGOUT"

    run aws --profile test logout
    assert_success
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" ""

    run aws --profile test logout
    assert_failure
    assert_output "Already logged out!"
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" ""
}

@test "Logout --all" {
    init  # Load shared vars
    login_test # Run login and shared tests

    run aws logout --all
    assert_success
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" ""

    run aws logout
    assert_failure
    assert_output "Already logged out!"

    run aws --profile test logout
    assert_failure
    assert_output "Already logged out!"

    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" ""
}
