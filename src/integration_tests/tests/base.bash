# Creates a clean environment where awscli-login is enabled but
# unconfigured.

load 'clean'
eval "_clean_$(declare -f setup)"  # Rename setup to _clean_setup

setup() {
    _clean_setup
    aws configure set plugins.login awscli_login.plugin

    assert_exists "$AWS_CONFIG_FILE"
    assert_not_exists "$AWSCLI_LOGIN_ROOT/.aws-login/config"
}
