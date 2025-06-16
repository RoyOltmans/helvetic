FROM python:3.6-slim

ENV PYTHONUNBUFFERED=1 TZ=Europe/Amsterdam

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git build-essential python3-dev dos2unix \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "--chdir", "helv_test", "helv_test.wsgi:application", "--bind", "0.0.0.0:5000"]
