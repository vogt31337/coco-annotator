# FROM jsbroks/coco-annotator:python-env
FROM python:latest

WORKDIR /workspace/

# Install python package dependices
COPY ./backend/ /workspace/
COPY ./.git /workspace/.git
# RUN python set_path.py
RUN pip install -r requirements.txt

ENV FLASK_ENV=development
ENV DEBUG=true

EXPOSE 5000
CMD gunicorn -c /workspace/webserver/gunicorn_config.py webserver:app --no-sendfile
