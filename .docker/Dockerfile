FROM python:3.9-slim

RUN useradd -m -s /bin/bash openhv \
    && apt-get update && apt-get install -y --no-install-recommends make curl \
    && apt-get clean

RUN mkdir /home/openhv/ladder

WORKDIR /home/openhv/ladder

ADD ./tools ./tools
ADD ./web ./web
ADD ./misc ./misc
ADD ./Makefile ./
ADD ./MANIFEST.in ./
ADD ./setup.py ./
ADD ./LICENSE ./

RUN chown openhv: -R /home/openhv

# https://github.com/chartjs/Chart.js/releases/latest
ENV CHART_JS_VERSION="2.9.3"
# https://github.com/jquery/jquery/releases/latest
ENV JQUERY_VERSION="3.6.0"
# https://github.com/DataTables/DataTables/releases/latest
ENV DATATABLES_VERSION="1.10.24"

RUN cd web/static/ \
    && curl -s -L https://cdnjs.cloudflare.com/ajax/libs/Chart.js/${CHART_JS_VERSION}/Chart.min.css -o Chart.min.css \
    && curl -s -L https://cdnjs.cloudflare.com/ajax/libs/Chart.js/${CHART_JS_VERSION}/Chart.bundle.min.js -o Chart.bundle.min.js \
    && curl -s -L https://cdn.datatables.net/v/dt/dt-${DATATABLES_VERSION}/datatables.min.js -o datatables.min.js \
    && curl -s -L https://code.jquery.com/jquery-${JQUERY_VERSION}.min.js -o jquery.min.js

RUN python3 -m venv venv/

RUN . venv/bin/activate && pip install gunicorn && pip install -e .

RUN mkdir instance \
    && for DB in "hv-all" "hv-2m";  \
        do venv/bin/openhv-ladder -d "instance/db-${DB}.sqlite3";  \
        done;

CMD ["venv/bin/gunicorn", "-b", "0.0.0.0:8000", "web:app"]

USER openhv
