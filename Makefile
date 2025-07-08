PYTHON ?= python3.9
CURL   ?= curl
VENV   ?= venv



LADDER_STATIC = ladderweb/static/Chart.bundle.min.js  \
                ladderweb/static/Chart.min.css        \
                ladderweb/static/datatables.min.js    \
                ladderweb/static/jquery.min.js        \

LADDER_DATABASES = instance/db-ra-all.sqlite3 \
                   instance/db-ra-2m.sqlite3  \
                   instance/db-td-all.sqlite3 \
                   instance/db-td-2m.sqlite3  \

# https://github.com/chartjs/Chart.js/releases/latest
CHART_JS_VERSION = 2.9.3

# https://github.com/jquery/jquery/releases/latest
JQUERY_VERSION = 3.6.0

# https://github.com/DataTables/DataTables/releases/latest
DATATABLES_VERSION = 1.10.24

ladderdev: initladderdev
	FLASK_APP=ladderweb FLASK_DEBUG=True FLASK_RUN_PORT=5000 $(VENV)/bin/flask run

initladderdev: $(VENV) $(LADDER_STATIC) $(LADDER_DATABASES)

ladderweb/static/Chart.min.css:
	$(CURL) -L https://cdnjs.cloudflare.com/ajax/libs/Chart.js/$(CHART_JS_VERSION)/Chart.min.css -o $@

ladderweb/static/Chart.bundle.min.js:
	$(CURL) -L https://cdnjs.cloudflare.com/ajax/libs/Chart.js/$(CHART_JS_VERSION)/Chart.bundle.min.js -o $@

ladderweb/static/datatables.min.js:
	$(CURL) -L https://cdn.datatables.net/v/dt/dt-$(DATATABLES_VERSION)/datatables.min.js -o $@

ladderweb/static/jquery.min.js:
	$(CURL) -L https://code.jquery.com/jquery-$(JQUERY_VERSION).min.js -o $@

$(LADDER_DATABASES): instance
	([ -f $@ ] ||  $(VENV)/bin/ora-ladder -d $@)

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
