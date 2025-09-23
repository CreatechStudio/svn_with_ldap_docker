FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    apache2 \
    subversion \
    libapache2-mod-svn \
    libapache2-mod-ldap-userdir \
    && rm -rf /var/lib/apt/lists/*

RUN a2enmod dav dav_svn authnz_ldap ldap

RUN mkdir -p /var/lib/svn && chown -R www-data:www-data /var/lib/svn

EXPOSE 80
CMD ["apachectl", "-D", "FOREGROUND"]
