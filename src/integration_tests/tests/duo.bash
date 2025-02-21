# Creates a clean environment where awscli-login is enabled and
# configured.

load 'common'
eval "_common_$(declare -f setup)"  # Rename setup to _common_setup

setup() {
    _common_setup
    aws --profile test login configure <<- EOF  # NOTA BENE: <<- strips tabs
		https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
		test
		
		push
		
	EOF
    assert_exists "$AWSCLI_LOGIN_ROOT/.aws-login/config"
}
