FROM alpine:3.11
WORKDIR /app
COPY foodtrucks/project/flask-app /app
COPY requirements.txt /app/requirements.txt
COPY foodtrucks/project/flask-app/package.json /app/package.json    
RUN apk add --no-cache python2 nodejs npm py2-pip && \
    pip2 install --no-cache-dir -r requirements.txt && \
    npm install && \
    npm run build
EXPOSE 5000
ENTRYPOINT ["python2", "app.py"]






