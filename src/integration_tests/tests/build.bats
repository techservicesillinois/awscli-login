# Integration tests for build artifacts

load 'clean'
eval "_base_$(declare -f setup)"  # Rename setup to _base_setup

setup() {
    _base_setup

    python -m venv "$TEST_TEMP_DIR/venv"
    export PATH="$TEST_TEMP_DIR/venv/bin:$PATH"
}

@test "Install from source distribution" {
    run pip install --no-deps ../../dist/awscli_login*.tar.gz
    assert_success
}
