FROM alpine:3.11
WORKDIR /app
COPY foodtrucks/project/flask-app /app
EXPOSE 5000
RUN apk add --no-cache python2 nodejs npm py2-pip && \
    pip2 install --no-cache-dir -r requirements.txt && \
    npm install && \
    npm run build
ENTRYPOINT ["python2", "app.py"]




