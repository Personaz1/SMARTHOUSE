FROM python:3.11-slim

WORKDIR /app
RUN pip install --no-cache-dir aiomqtt==1.2.1 fastapi==0.111.0 uvicorn[standard]==0.30.1 pillow==10.4.0

COPY sim.py /app/sim.py
COPY sim_http.py /app/sim_http.py

CMD sh -c "python /app/sim.py & uvicorn sim_http:app --host 0.0.0.0 --port 8100"


