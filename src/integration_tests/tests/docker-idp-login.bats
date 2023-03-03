# Integration tests for aws login

load 'common-docker-idp'

@test "Login with Docker IdP" {
    run aws login --verify-ssl-certificate=false --password password <<< 0
    assert_failure
    assert_output -e "An error occurred \(InvalidIdentityToken\) when calling the AssumeRoleWithSAML operation: Specified provider doesn't exist \(Service: AWSOpenIdDiscoveryService; Status Code: 400; Error Code: AuthSamlManifestNotFoundException; Request ID: [0-9a-f-]+; Proxy: null\)"
}
