UNIT_TESTS = bl_trade_aid.patterns.tests.unit
UNIT_TEST = bl_trade_aid.patterns.tests.unit.test_commands.GenerateCurrentProfileChartsCommandTestCase.test_generate_current_profile_chart_one_symbol
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
