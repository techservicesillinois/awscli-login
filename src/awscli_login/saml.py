import logging
import re

import lxml.etree as ET

from base64 import b64encode
from datetime import datetime
from http.cookiejar import LWPCookieJar
from typing import List, Tuple
from typing import cast
from uuid import uuid4

from lxml.etree import XMLSyntaxError
from lxml.etree import tostring, Element, SubElement
from requests import Session
from requests.cookies import RequestsCookieJar

from .exceptions import (
    AuthnFailed,
    InvalidSOAP,
    MissingCookieJar,
    RoleParseFail,
)
from .typing import Role, Headers
from .util import secure_touch

SAML_SUCCESS = "urn:oasis:names:tc:SAML:2.0:status:Success"

ns = {
       'S': 'http://schemas.xmlsoap.org/soap/envelope/',
       'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion',
       'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
}

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """ This is a wrapper function to ease testing with Mocks. """
    return datetime.utcnow()


def raise_if_saml_failed(soap: bytes) -> None:
    """
    Parses a SAML SOAP response to determine if authentication
    succeeded or failed.

    Args:
        soap: A byte string containing a SOAP response from an
        IdP.

    Raises:
        AuthnFailed: If a SAML success code was not returned.
        XMLSyntaxError: If the SOAP response contains syntax errors.
    """
    xml = ET.fromstring(soap)

    elem = xml.find('S:Body/saml2p:Response/saml2p:Status' +
                    '/saml2p:StatusCode' +
                    '[@Value="' + SAML_SUCCESS + '"]', ns)

    if elem is None:
        raise AuthnFailed


def saml_login(url: str, jar: LWPCookieJar,
               username: str = None, password: str = None,
               headers: Headers = None) -> bytes:
    """
    Generates and posts a SAML AuthNRequest to an IdP.

    Args:
        url: ECP endpoint URL for the IdP.
        username: Username to provide to the IdP.
        password: Password to provide to the IdP.
        headers: optional headers to provide to the IdP.

    Returns:
        The SOAP response from the IdP.
    """
    s = Session()
    s.cookies = cast(RequestsCookieJar, jar)
    s.headers.update({'Content-Type': 'text/xml', 'charset': 'utf-8'})

    envelope = authn_request()
    auth = (username, password) if username and password else None
    logger.debug("POST %r\nheaders: %r\npayload %r" %
                 (url, headers, envelope))
    r = s.post(url, data=envelope, headers=headers, auth=auth)
    logger.debug("POST returned: %r" % r.content)

    r.raise_for_status()
    try:
        raise_if_saml_failed(r.content)
    except XMLSyntaxError:
        raise InvalidSOAP(url)
    return r.content


def authenticate(url: str, cookies: str,
                 username: str, password: str,
                 headers: Headers) -> Tuple[str, List[Role]]:
    """
    Authenitcate with user credentials to IdP.

    Args:
        url: ECP endpoint URL for the IdP.
        cookies: A path to a cookie jar.
        username: Username to provide to the IdP.
        password: Password to provide to the IdP.
        headers: Optional headers to provide to the IdP.

    Returns:
        A base 64 encoded SAML assertion string, and a list of
        tuples containing a SAML provider ARN and a Role ARN.
    """
    jar = LWPCookieJar(cookies)
    soap = saml_login(url, jar, username, password, headers)

    mesg = "Successfully authenticated with username/password"
    logger.info(mesg + " to endpoint: " + url)

    secure_touch(cookies)
    jar.save(ignore_discard=True)
    logger.info("Saved cookies to jar: " + jar.filename)

    return parse_soap_response(soap)


def refresh(url: str, cookies: str) -> Tuple[str, List[Role]]:
    """
    Reauthenticate with cookies to IdP.

    Args:
        url: ECP endpoint URL for the IdP.
        cookies: A path to a cookie jar.

    Returns:
        A base 64 encoded SAML assertion string, and a list of
        tuples containing a SAML provider ARN and a role ARN.
    """
    jar = LWPCookieJar(cookies)
    try:
        jar.load(ignore_discard=True)
        logger.info("Loaded cookie jar: " + cookies)
    except FileNotFoundError:
        raise MissingCookieJar(url)

    soap = saml_login(url, jar)

    mesg = "Successfully authenticated with cookies"
    logger.info(mesg + " to endpoint: " + url)

    return parse_soap_response(soap)


def parse_soap_response(soap: bytes) -> Tuple[str, List[Role]]:
    """
    Parses SAML SOAP response for SAML assertion and SAML attributes:
    provider & role ARN(s).

    Args:
        soap: A SAML Response

    Returns:
        A base 64 encoded SAML assertion string, and a list of
        tuples containing a SAML provider ARN and a role ARN.
    """
    body = ET.fromstring(soap)
    resp = body.find('S:Body/saml2p:Response', ns)

    roles = resp.findall("saml2:Assertion/" +
                         "saml2:AttributeStatement/saml2:Attribute[@Name=" +
                         "'https://aws.amazon.com/SAML/Attributes/Role']/" +
                         "saml2:AttributeValue", ns)

    return b64encode(tostring(resp)).decode("us-ascii"), parse_role_arns(roles)


def parse_role_arns(roles: List[SubElement]) -> List[Role]:
    """
    Parses SAML Attributes for SAML provider and Role ARNS.

    Args:
        roles: List of XML SAML Attributes.

    Returns:
        A list of tuples containing a SAML provider ARN and a
        Role ARN.

    Raises:
        SAML: If unable to find a SAML provider or Role ARN.
    """
    role_arns = []
    role_regex = re.compile('.*(arn:aws:iam::([0-9]+):role/([^,:]+)).*')
    saml_regex = re.compile(
        '.*(arn:aws:iam::([0-9]+):saml-provider/([^,:]+)).*'
    )

    for role in roles:
        arn = role_regex.match(role.text)
        saml = saml_regex.match(role.text)

        if arn and saml:
            role_arns.append((saml.group(1), arn.group(1)))
        else:
            raise RoleParseFail(role.text)

    return role_arns


def authn_request() -> bytes:
    """
    Generates an ECP SAML AuthNRequest for the Amazon SP.

    Returns:
        A SOAP byte string.
    """
    now = utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    uuid = '_' + str.upper(str(uuid4())).replace('-', '')

    SOAP = "{%s}" % ns['S']
    SAML2 = "{%s}" % ns['saml2']
    SAML2P = "{%s}" % ns['saml2p']

    envelope = Element(SOAP + "Envelope", nsmap=ns)
    body = SubElement(envelope, SOAP + "Body")

    attr = {
       'AssertionConsumerServiceURL': "https://signin.aws.amazon.com/saml",
       'ID': uuid,
       'IssueInstant': now,
       'ProtocolBinding': "urn:oasis:names:tc:SAML:2.0:bindings:PAOS",
       'Version': '2.0',
    }
    authn_request = SubElement(body, SAML2P + "AuthnRequest", **attr)

    issuer = SubElement(authn_request, SAML2 + "Issuer")
    issuer.text = "urn:amazon:webservices"

    return tostring(envelope)
