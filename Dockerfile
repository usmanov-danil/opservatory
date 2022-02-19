FROM python:3.9

COPY Pipfile /app/
COPY Pipfile.lock /app/
WORKDIR /app
RUN pip3 install pipenv

RUN if [ "$ENV" = "dev" ]; then \
    pipenv install --dev --deploy --clear --system; \
else \
    pipenv install --deploy --clear --system; \
fi

COPY opservatory /app/opservatory
EXPOSE 5000
ENTRYPOINT ["uvicorn", "opservatory.api:app", "--host", "0.0.0.0", "--port", "5000"]