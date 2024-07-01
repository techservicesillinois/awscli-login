# Creates a clean environment where awscli-login is enabled but
# unconfigured.

load 'clean'
eval "_clean_$(declare -f setup)"  # Rename setup to _clean_setup

setup() {
    _clean_setup
    aws configure set plugins.login awscli_login
    if [ -v AWSCLI_TEST_V2 ]; then
        assert_exists "$AWSCLI_TEST_PLUGIN_PATH"
        aws configure set \
            plugins.cli_legacy_plugin_path "$AWSCLI_TEST_PLUGIN_PATH"
        echo "Configured for AWSCLI V2."
    else
        echo "Configured for AWSCLI V1."
    fi
    assert_exists "$AWS_CONFIG_FILE"
    assert_not_exists "$AWSCLI_LOGIN_ROOT/.aws-login/config"
}
