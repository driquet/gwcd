FROM python:3
MAINTAINER <mrummuka@hotmail.com>
COPY LICENCE ./
COPY gwcd.py ./
COPY reader.py ./
CMD [ "python", "./gwcd.py", "--output", "/data", "--lua", "/data/wigo.gwc" ]
