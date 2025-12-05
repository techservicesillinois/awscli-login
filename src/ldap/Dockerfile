FROM alpine:latest
RUN apk add --no-cache openldap openldap-back-mdb
COPY ./slapd.conf /etc/openldap/slapd.conf
COPY ./users.ldif /
RUN slapadd -l /users.ldif
EXPOSE 1389
ENTRYPOINT ["slapd", "-d256", "-h", "ldap://0.0.0.0:1389"]
