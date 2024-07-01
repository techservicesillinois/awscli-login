# Creates a clean environment where awscli-login is enabled and
# configured to work with a local test IdP.

load 'base'
eval "_base_$(declare -f setup)"  # Rename setup to _base_setup

setup() {
    _base_setup

    # We cannot run integration tests dependent on Linux docker
    # containers on Windows runners because GitHub Actions does not
    # support Linux containers on Windows (See actions/runner-images#1143,
    # actions/runner#904, and actions/runner-images#5760).
    if [ $RUNNER_OS == "Windows" ]; then
        skip "Windows runners do not support Docker IdP integration tests."
    fi

    if [ $RUNNER_OS == "macOS" ]; then
        skip "macOS runners do not support Docker IdP integration tests."
    fi

    
    aws login configure <<- EOF  # NOTA BENE: <<- strips tabs
		https://localhost:8443/idp/profile/SAML2/SOAP/ECP
		user01
		
		push
		
	EOF
    assert_exists "$AWSCLI_LOGIN_ROOT/.aws-login/config"

    # Wait for Docker IdP to start
    timeout=15
    until curl -fks https://localhost:8443/idp >/dev/null 2>&1; ret=$?; [ $ret -eq 0 -o $timeout -eq 0 ]; do
        sleep 1
        let $((timeout--))
    done

    if [ $ret -ne 0 ]; then
        echo
        echo ==================================================
        echo
        echo "Docker IdP is non-responsive: https://localhost:8443/idp"
        echo "Run 'make idp' to start Docker IdP"
        exit 1
    fi

}
