FROM python:3.9


WORKDIR /api


COPY ./requirements.txt /api/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /api/requirements.txt


COPY ./api /api/app


CMD ["fastapi", "run", "app/main.py", "--port", "80"]
