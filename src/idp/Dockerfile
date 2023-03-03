FROM tier/shib-idp:latest
RUN sed -i 's/SAML2\.ECP/SAML2\.ECP\.MDDriven/' /opt/shibboleth-idp/conf/relying-party.xml
COPY ./idp-configs/		/opt/shibboleth-idp/
