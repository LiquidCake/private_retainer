FROM nginx

ARG build_ver

#copy config
COPY build/package/nginx/conf/nginx.conf /etc/nginx/nginx.conf

#copy ssl cert files
#COPY build/package/nginx/conf/ssl/ssl-bundle.crt /etc/ssl/ssl-bundle.crt
#COPY build/package/nginx/conf/ssl/test.net.key /etc/ssl/test.net.key

#RUN chmod 444 /etc/ssl/ssl-bundle.crt
#RUN chmod 444 /etc/ssl/test.net.key

EXPOSE 80 443