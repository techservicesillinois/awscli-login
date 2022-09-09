# Integration tests for aws login

load 'common'

@test "Login and logout" {
    ! read -r -d '' CREDS <<- EOF
		[default]$CR
		aws_access_key_id = ABCDEFGHIJKLMNOPQRST$CR
		aws_secret_access_key = SUPER DUPER SECRET KEY$CR
		aws_session_token = BOGUS TOKEN$CR
		aws_security_token = BOGUS TOKEN
	EOF

    assert_not_exists "$AWS_SHARED_CREDENTIALS_FILE"
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
    assert_exists "$AWS_SHARED_CREDENTIALS_FILE"
    assert_equal "$(<$AWS_SHARED_CREDENTIALS_FILE)" "$CREDS"

    # refresh process dies on startup because our setup is fake
    # but on github there is a race condition so logout twice to
    # be sure
    aws logout || echo "Ignore errors."
    run aws logout
    assert_failure
    assert_output "Already logged out!"
}
