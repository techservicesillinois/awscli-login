# Integration tests for aws login

load 'common'

@test "Login and logout" {
    ! read -r -d '' CREDS_AWS_FILE <<- EOF
		[default]$CR
		credential_process = aws-login --profile default
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
		username = netid
	EOF

    assert_equal "$(<$AWS_SHARED_CREDENTIALS_FILE)" "$CREDS_AWS_FILE"
    run aws login --load-http-traffic cassettes/login.yaml --password foo <<< 0
    assert_success
    assert_output <<- EOF
		Please choose the role you would like to assume:$CR
		        Account: 123456789010$CR
		            [ 0 ]: Team$CR
		        Account: 987654321098$CR
		            [ 1 ]: Admins$CR
		Selection:
	EOF
    assert_equal "$(<$AWS_SHARED_CREDENTIALS_FILE)" "$CREDS_AWS_FILE"
    assert_exists "$AWSCLI_LOGIN_ROOT/.aws-login/credentials"
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" "$CREDS"

    run aws logout
    assert_success
    assert_equal "$(<$AWSCLI_LOGIN_ROOT/.aws-login/credentials)" ""

    run aws logout
    assert_failure
    assert_output "Already logged out!"
}

# Regression test for #222 and #230
@test "Ensure environment of plugin is the same as the standalone script" {
    run aws login --debug-info
    # USEFUL HACK: diff output is much shorter than assert_equal!
    echo "$output$CR" > $BATS_TEST_TMPDIR/output.txt
    run bash -c 'aws-login --debug-info | diff - $BATS_TEST_TMPDIR/output.txt'
    assert_success
}
