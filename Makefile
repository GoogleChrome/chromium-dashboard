.PHONY: setup clean-setup deps dev-deps dev-ot-key do-tests start-emulator-persist start-emulator \
	stop-emulator build tsc-clean watch start-app debug-app start stop test webtest webtest-watch \
	webtestpuppeteer webtestpuppeteer-watch webtest-coverage do-coverage coverage view-coverage \
	mypy lint lint-fix presubmit pylint openapi openapi-webstatus openapi-frontend openapi-backend \
	openapi-validate pwtests pwtests-update pwtests-report pwtests-ui pwtests-shell pwtests-debug pwtests-shutdown

setup:
	npm ci
	python3.13 -m venv cs-env
	$(MAKE) deps

clean-setup:
	rm -rf node_modules cs-env
	$(MAKE) setup

deps:
	. cs-env/bin/activate && pip install -r requirements.txt --upgrade && pip install -r requirements.dev.txt --upgrade

dev-deps:
	@echo 'dev-deps is no longer needed'

dev-ot-key:
	gcloud secrets versions access latest --secret=DEV_OT_API_KEY --out-file=ot_api_key.txt --project=cr-status-staging

do-tests:
	. cs-env/bin/activate && curl -X POST 'http://localhost:15606/reset' && python3.13 -m unittest discover -p '*_test.py' -b

start-emulator-persist:
	gcloud beta emulators datastore start --project=cr-status-staging --host-port=:15606 --use-firestore-in-datastore-mode

start-emulator:
	gcloud beta emulators datastore start --project=cr-status-staging --host-port=:15606 --no-store-on-disk --use-firestore-in-datastore-mode

stop-emulator:
	curl -X POST 'http://localhost:15606/shutdown' || true
	pkill -f "CloudDatastore.jar" || true

build: tsc-clean
	npx tsc
	npx gulp

tsc-clean:
	npx tsc --build --clean

watch: build
	npx concurrently "tsc --watch" "gulp watch"

start-app: build
	curl --retry 4 http://$${DATASTORE_EMULATOR_HOST:-localhost:15606}/ --retry-connrefused
	./scripts/start_server.sh

debug-app: build
	curl --retry 4 http://$${DATASTORE_EMULATOR_HOST:-localhost:15606}/ --retry-connrefused
	./scripts/debug_server.sh

start: stop
	. cs-env/bin/activate && \
	($(MAKE) start-emulator-persist > /dev/null 2>&1 &) && \
	$(MAKE) start-app; status=$$?; $(MAKE) stop-emulator; exit $$status

stop: pwtests-shutdown
	kill `pgrep gunicorn` || true

test:
	($(MAKE) start-emulator > /dev/null 2>&1 &)
	sleep 6
	curl --retry 4 http://localhost:15606/ --retry-connrefused
	$(MAKE) do-tests; status=$$?; $(MAKE) stop-emulator; exit $$status

webtest: build
	npx web-test-runner --playwright --browsers chromium firefox

webtest-watch: build
	npx web-test-runner "build/**/*_test.{js,ts}" --node-resolve --playwright --watch --browsers chromium

webtestpuppeteer: build
	npx web-test-runner --puppeteer --browsers chrome

webtestpuppeteer-watch: build
	npx web-test-runner --puppeteer --watch --browsers chrome

webtest-coverage: build
	npx web-test-runner --playwright --coverage --browsers chromium firefox

do-coverage:
	. cs-env/bin/activate && coverage3 erase && coverage3 run -m unittest discover -p '*_test.py' -b && coverage3 html

coverage:
	($(MAKE) start-emulator > /dev/null 2>&1 &)
	sleep 3
	curl --retry 4 http://localhost:15606/ --retry-connrefused
	$(MAKE) do-coverage; status=$$?; $(MAKE) stop-emulator; exit $$status

view-coverage:
	pushd htmlcov/ && python3.13 -m http.server 8080 && popd

mypy:
	. cs-env/bin/activate && mypy --ignore-missing-imports --exclude cs-env/ --exclude appengine_config.py --exclude gen/py/webstatus_openapi/build/ --exclude gen/py/webstatus_openapi/setup.py --exclude gen/py/webstatus_openapi/test/ --exclude gen/py/chromestatus_openapi/build/ --exclude gen/py/chromestatus_openapi/chromestatus_openapi/test --exclude appengine_config.py --no-namespace-packages --disable-error-code "annotation-unchecked" .

lint:
	npx prettier client-src/js-src client-src/elements client-src/elements packages/playwright/tests --check
	npx eslint "client-src/js-src/**/*.{js,ts}" "packages/playwright/tests/*.{js,ts}"
	npx tsc -p tsconfig.json
	npx lit-analyzer "client-src/elements/chromedash-*.{js,ts}" "packages/playwright/tests/*.{js,ts}"

lint-fix:
	npx prettier client-src/js-src client-src/elements packages/playwright/tests --write
	npx eslint "client-src/js-src/**/*.{js,ts}" "packages/playwright/tests/*.{js,ts}" --fix

presubmit: test webtest lint mypy

pylint:
	npx pylint --output-format=parseable *py api/*py framework/*py internals/*py pages/*py

openapi: openapi-backend openapi-frontend

openapi-webstatus:
	. cs-env/bin/activate && \
	rm -rf gen/py/webstatus_openapi && \
	npx openapi-generator-cli generate --reserved-words-mappings field=field -i https://raw.githubusercontent.com/GoogleChrome/webstatus.dev/e2ee5bab74d5f96fb7fdaea5744d1b9f2b934593/openapi/backend/openapi.yaml -g python -o gen/py/webstatus_openapi --additional-properties=packageName=webstatus_openapi && \
	pip install -r requirements.txt

openapi-frontend:
	rm -rf gen/js/chromestatus-openapi && \
	npx openapi-generator-cli generate --reserved-words-mappings field=field -i openapi/api.yaml -g typescript-fetch -o gen/js/chromestatus-openapi --config openapi/js-config.yaml && \
	npm install

openapi-backend:
	. cs-env/bin/activate && \
	rm -rf gen/py/chromestatus_openapi && \
	npx openapi-generator-cli generate --reserved-words-mappings field=field -i openapi/api.yaml -g python-flask -o gen/py/chromestatus_openapi --additional-properties=packageName=chromestatus_openapi && \
	pip install -r requirements.txt

openapi-validate:
	npx openapi-generator-cli validate -i openapi/api.yaml

pwtests: pwtests-shutdown
	./scripts/playwright.sh bash -c "./wait-for-app.sh && npx playwright test"

pwtests-update: pwtests-shutdown
	./scripts/playwright.sh bash -c "./wait-for-app.sh && npx playwright test --update-snapshots $${npm_config_filename} "

pwtests-report: pwtests-shutdown
	./scripts/playwright.sh bash -c "./wait-for-app.sh && npx playwright show-report"

pwtests-ui: pwtests-shutdown
	./scripts/playwright.sh bash -c "./wait-for-app.sh && npx playwright test --ui --ui-port=8123"

pwtests-shell:
	./scripts/playwright.sh bash

pwtests-debug:
	./scripts/playwright.sh debug

pwtests-shutdown:
	./scripts/playwright.sh down
