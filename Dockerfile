FROM alpine:3.11 AS builder
WORKDIR /app

#Copy dependencies files 
COPY foodtrucks/project/flask-app /app

#build dependencies
RUN apk add --no-cache nodejs npm  && \
    npm install && \
    npm run build && \
    rm -rf node_modules ~/.npm ~/.cache

FROM alpine:3.11
WORKDIR /app
COPY foodtrucks/project/flask-app/app.py /app/app.py
COPY requirements.txt /app/requirements.txt
COPY foodtrucks/project/utils /app/utils
# install only the runtime dependencies
RUN apk add --no-cache python2 py2-pip && \
    pip2 install -r requirements.txt
# expose the port and run the app
EXPOSE 5000
ENTRYPOINT ["python2", "app.py"] 