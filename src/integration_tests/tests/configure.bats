# Integration tests for aws login configure

load 'clean'

# We expect a failure here because the plugin is not enabled in
# the $AWS_CONFIG_FILE. This is here to make sure setup actually
# creates a clean environment and awscli uses it as expected.
@test "Login with unconfigured awscli" {
    assert_not_exists "$AWS_CONFIG_FILE"
    assert_not_exists "$AWS_SHARED_CREDENTIALS_FILE"
    assert_not_exists "$AWSCLI_LOGIN_ROOT/.awscli-login/config"

    run aws login
    assert_failure
    assert_line --partial "aws: error: argument command: Invalid choice"
}

@test "Enable plugin in ~/.aws/config" {
    assert_not_exists "$AWS_CONFIG_FILE"
    run aws configure set plugins.login awscli_login
    assert_success

    ! read -r -d '' CONFIG_FILE <<- EOF  # NOTA BENE: <<- strips tabs
		[plugins]$CR
		login = awscli_login
	EOF
    assert_equal "$(<$AWS_CONFIG_FILE)" "$CONFIG_FILE"
}
