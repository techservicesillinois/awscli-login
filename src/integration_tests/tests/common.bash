# Creates a clean environment where awscli-login is enabled and
# configured.

load 'base'
eval "_base_$(declare -f setup)"  # Rename setup to _base_setup

setup() {
    _base_setup
    aws login configure <<- EOF  # NOTA BENE: <<- strips tabs
		https://shibboleth.illinois.edu/idp/profile/SAML2/SOAP/ECP
		netid
		
		push
		
	EOF
    assert_exists "$AWSCLI_LOGIN_ROOT/.aws-login/config"
}
