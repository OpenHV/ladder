FROM python:3.9-slim

RUN useradd -m -s /bin/bash openhv \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl make \
    && apt-get clean

RUN mkdir /home/openhv/ladder

WORKDIR /home/openhv/ladder

ADD ./tools ./tools
ADD ./web ./web
ADD ./misc ./misc
ADD ./MANIFEST.in ./
ADD ./setup.py ./
ADD ./LICENSE ./
ADD ./Makefile ./

RUN chown openhv: -R /home/openhv

RUN make download-static

RUN python3 -m venv venv/

RUN . venv/bin/activate && pip install gunicorn && pip install -e .

CMD ["venv/bin/gunicorn", "-b", "0.0.0.0:8000", "web:app"]

USER openhv
