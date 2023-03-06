# Integration tests for aws login

load 'common-docker-idp'

@test "Test --ecp-endpoint-url" {
    aws login configure <<- EOF  # NOTA BENE: <<- strips tabs
		https://localhost:8443/bad/endpoint
		user01
		
		push
		
	EOF

    run aws $LOGIN
    assert_failure
    assert_output "404 Client Error:  for url: https://localhost:8443/bad/endpoint"
    run aws $LOGIN --ecp-endpoint-url 'https://localhost:8443/idp/profile/SAML2/SOAP/ECP'
    assert_success
    assert_output ""
}

@test "Login with Docker IdP" {
    run aws $LOGIN
    assert_success
    assert_output ""
}
