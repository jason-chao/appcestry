FROM nginx:latest

RUN mkdir /usr/share/nginx/html/images
COPY *.html /usr/share/nginx/html/
COPY *.css /usr/share/nginx/html/
COPY *.js /usr/share/nginx/html/
COPY images/* /usr/share/nginx/html/images/
COPY nginx/* /etc/nginx/conf.d/
