FROM python:3.6.5

COPY requirements.txt .
COPY ./antimatter ./antimatter
COPY ./client_keys ./client_keys

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python3", "antimatter/client.py", "--log-level", "DEBUG" ]
