PYTHON ?= python3.9
CURL   ?= curl
VENV   ?= venv

LADDER_STATIC = web/static/Chart.bundle.min.js  \
                web/static/Chart.min.css        \
                web/static/datatables.min.js    \
                web/static/jquery.min.js        \

LADDER_DATABASES = instance/db-hv-all.sqlite3 \
                   instance/db-hv-2m.sqlite3  \

# https://github.com/chartjs/Chart.js/releases/latest
CHART_JS_VERSION = 2.9.3

# https://github.com/jquery/jquery/releases/latest
JQUERY_VERSION = 3.6.0

# https://github.com/DataTables/DataTables/releases/latest
DATATABLES_VERSION = 1.10.24

ladderdev: initladderdev
	FLASK_APP=web FLASK_DEBUG=True FLASK_RUN_PORT=5000 $(VENV)/bin/flask run

initladderdev: $(VENV) $(LADDER_STATIC) $(LADDER_DATABASES)

web/static/Chart.min.css:
	$(CURL) -s -L https://cdnjs.cloudflare.com/ajax/libs/Chart.js/$(CHART_JS_VERSION)/Chart.min.css -o $@

web/static/Chart.bundle.min.js:
	$(CURL) -s -L https://cdnjs.cloudflare.com/ajax/libs/Chart.js/$(CHART_JS_VERSION)/Chart.bundle.min.js -o $@

web/static/datatables.min.js:
	$(CURL) -s -L https://cdn.datatables.net/v/dt/dt-$(DATATABLES_VERSION)/datatables.min.js -o $@

web/static/jquery.min.js:
	$(CURL) -s -L https://code.jquery.com/jquery-$(JQUERY_VERSION).min.js -o $@

$(LADDER_DATABASES): instance
	([ -f $@ ] ||  $(VENV)/bin/openhv-ladder -d $@)

instance:
	mkdir -p $@

wheel: $(VENV)
	$(VENV)/bin/python -m pip install wheel && python setup.py bdist_wheel

test: $(VENV)
	$(VENV)/bin/pytest -v

clean:
	$(RM) -r build
	$(RM) -r dist
	$(RM) -r oraladder.egg-info
	$(RM) -r venv

$(VENV):
	$(PYTHON) -m venv $@
	$(VENV)/bin/python -m pip install -e .

.PHONY: ladderdev initladderdev wheel clean test
