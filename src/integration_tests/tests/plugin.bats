load 'clean'

@test "Ensure plugin does not require external modules" {
    PYTHON=$TEST_TEMP_DIR/venv/bin/python

    if [ $RUNNER_OS == "Windows" ]; then
        skip "This test does not support Windows."
    fi

    # Install awscli-login without deps
    python -m venv $TEST_TEMP_DIR/venv
    $PYTHON -m pip install --no-deps ../..

    # Import plugin in clean venv
    $PYTHON -c 'import awscli_login'
    
    # Load version in clean venv
    $PYTHON -c 'from awscli_login._version import __version__'
}
