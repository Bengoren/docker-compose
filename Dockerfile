FROM alpine:3.11 AS builder
WORKDIR /app
COPY foodtrucks/project/flask-app /app

#Copy dependencies files
COPY requirements.txt /app/requirements.txt
COPY foodtrucks/project/flask-app/package.json /app/package.json    

#build dependencies
RUN apk add --no-cache python2 nodejs npm py2-pip && \
    pip2 install --no-cache-dir -r requirements.txt && \
    npm install && \
    npm run build && \
    rm -rf node_modules ~/.npm ~/.cache

FROM alpine:3.11
WORKDIR /app
# install only the runtime dependencies
RUN apk add --no-cache python2
# copy only the necessary files from the builder stage - pip installments
COPY --from=builder /usr/lib/python2.7/site-packages /usr/lib/python2.7/site-packages
# copy the app files
COPY --from=builder /app /app

EXPOSE 5000
ENTRYPOINT ["python2", "app.py"]        





