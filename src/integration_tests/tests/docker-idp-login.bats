# Integration tests for aws login

load 'common-docker-idp'

@test "Test --ecp-endpoint-url" {
    aws login configure <<- EOF  # NOTA BENE: <<- strips tabs
		https://localhost:8443/bad/endpoint
		user01
		
		push
		
	EOF

    run aws login --verify-ssl-certificate=false --password password
    assert_failure
    assert_output "404 Client Error:  for url: https://localhost:8443/bad/endpoint"
    run aws login --verify-ssl-certificate=false --password password \
        --ecp-endpoint-url 'https://localhost:8443/idp/profile/SAML2/SOAP/ECP'
    assert_failure
    assert_output -e "An error occurred \(InvalidIdentityToken\) when calling the AssumeRoleWithSAML operation: Specified provider doesn't exist \(Service: AWSOpenIdDiscoveryService; Status Code: 400; Error Code: AuthSamlManifestNotFoundException; Request ID: [0-9a-f-]+; Proxy: null\)"
}

@test "Login with Docker IdP" {
    run aws login --verify-ssl-certificate=false --password password
    assert_failure
    assert_output -e "An error occurred \(InvalidIdentityToken\) when calling the AssumeRoleWithSAML operation: Specified provider doesn't exist \(Service: AWSOpenIdDiscoveryService; Status Code: 400; Error Code: AuthSamlManifestNotFoundException; Request ID: [0-9a-f-]+; Proxy: null\)"
}
