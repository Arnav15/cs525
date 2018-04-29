FROM python:3.6.5

WORKDIR /opt/blockchain

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "antimatter/proposer.py" ]
