UNIT_TESTS = bl_trade_aid.patterns.tests.unit
unit-test:
	docker-compose -f local.yml run django python manage.py test $(UNIT_TESTS) --exclude-tag=INTEGRATION
clean:
	rm -rf output/*.*
test: unit-test
cov:
	docker-compose -f local.yml run django coverage run manage.py test $(UNIT_TESTS) --exclude-tag=INTEGRATION
	docker-compose -f local.yml run django coverage report
