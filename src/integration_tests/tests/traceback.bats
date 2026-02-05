# Integration tests for aws login

load 'common'

@test "Logout verbose flag" {
    ! read -r -d '' CREDS_AWS_FILE <<- EOF
		[default]$CR
		credential_process = aws-login --profile default
	EOF

    # Regression test for #260
    run aws logout --verbose
    assert_failure
    assert_line "Loaded login profile: default$CR"
    assert_line "Already logged out!"

    # Regression test for #260
    run aws logout --verbose --verbose
    assert_failure
    assert_line "Traceback (most recent call last):$CR"

    # Regression test for #260
    run aws logout --verbose --verbose --verbose
    assert_failure
    assert_line "Traceback (most recent call last):$CR"
}

@test "aws-login verbose flag" {
    ! read -r -d '' CREDS_AWS_FILE <<- EOF
		[default]$CR
		credential_process = aws-login --profile default
	EOF

    # Regression test for #260
    run aws-login --verbose
    assert_failure
    assert_line "Loaded login profile: default$CR"
    assert_line "Already logged out!"

    # Regression test for #260
    run aws-login  --verbose --verbose
    assert_failure
    assert_line "Traceback (most recent call last):$CR"

    # Regression test for #260
    run aws-login --verbose --verbose --verbose
    assert_failure
    assert_line "Traceback (most recent call last):$CR"
}
