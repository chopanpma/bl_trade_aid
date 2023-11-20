UNIT_TESTS = bl_trade_aid.patterns.tests.unit
UNIT_TEST = bl_trade_aid.patterns.tests.unit.test_searching_market.ScannerSubscriptionTestCase.test_call_req_Scanner_for_no_changed_contracts
unit-test:
	docker-compose -f local.yml run django python manage.py test $(UNIT_TESTS) --exclude-tag=INTEGRATION
unit-test-x:
	docker-compose -f local.yml run django python manage.py test $(UNIT_TEST) --exclude-tag=INTEGRATION
clean:
	rm -rf output/*.*
test: unit-test
test-x: unit-test-x
cov:
	docker-compose -f local.yml run django coverage run manage.py test $(UNIT_TESTS) --exclude-tag=INTEGRATION
	docker-compose -f local.yml run django coverage report
