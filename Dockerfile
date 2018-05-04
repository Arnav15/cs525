FROM python:3.6.5

COPY requirements.txt .
COPY ./antimatter ./antimatter

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 9991/tcp

CMD [ "python3", "antimatter/participant.py", "--log-level", "DEBUG" ]
