.PHONY: all tests debug submodules
SUBMODULES:=bats $(addprefix test_helper/,bats-assert bats-file bats-support)

all: tests

tests: submodules
	bats/bin/bats -r tests

debug: export BATSLIB_TEMP_PRESERVE_ON_FAILURE=1
debug: submodules
	bats/bin/bats -r tests

submodules: $(addsuffix /.git, $(SUBMODULES))
%/.git:
	git submodule update --init --recursive -- $*

clean:
	rm -rf $(SUBMODULES)
