FROM python:3.8

RUN pip install pipenv

ENV PROJECT_DIR /app

ENV PYTHONPATH ${PROJECT_DIR}

WORKDIR ${PROJECT_DIR}

COPY Pipfile Pipfile.lock ${PROJECT_DIR}/

RUN pipenv install --system --deploy

COPY app ${PROJECT_DIR}/app

CMD ["python", "./main.py"]