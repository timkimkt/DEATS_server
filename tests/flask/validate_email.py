"""
Adapted email-validator source code by Joshua Tauberer (https://pypi.org/project/email-validator/), specifically
the functions validate_email and validate_email_domain_part, to validate Dartmouth only emails

Source code: https://github.com/JoshData/python-email-validator
"""

import re
import idna  # implements IDNA 2008; Python's codec is only IDNA 2003

from email_validator import unicode_class, EmailSyntaxError, ValidatedEmail, validate_email_local_part
from email_validator import EMAIL_MAX_LENGTH, __get_length_reason, DOMAIN_MAX_LENGTH


def validate_email(email, allow_smtputf8=True):
    """
    Validates Dartmouth email addresses, raising an EmailNotValidError if the address is not valid or returning a dict
    of information when the address is valid. The email argument can be a str or a bytes instance, but if bytes it
     must be ASCII-only.
    """

    # Allow email to be a str or bytes instance. If bytes,
    # it must be ASCII because that's how the bytes work
    # on the wire with SMTP.
    if not isinstance(email, (str, unicode_class)):
        try:
            email = email.decode("ascii")
        except ValueError:
            raise EmailSyntaxError("The provided Dartmouth email address isn't valid ASCII.")

    # At-sign.
    parts = email.split('@')
    if len(parts) != 2:
        raise EmailSyntaxError("The provided Dartmouth email address isn't valid. It must have exactly one @-sign.")

    # Collect return values in this instance.
    ret = ValidatedEmail()
    ret.original_email = email

    # Validate the email address's local part syntax and get a normalized form.
    local_part_info = validate_email_local_part(parts[0], allow_smtputf8=allow_smtputf8)
    ret.local_part = local_part_info["local_part"]
    ret.ascii_local_part = local_part_info["ascii_local_part"]
    ret.smtputf8 = local_part_info["smtputf8"]

    # Validate the email address's domain part syntax and get a normalized form.
    domain_part_info = validate_email_domain_part(parts[1])
    ret.domain = domain_part_info["domain"]
    ret.ascii_domain = domain_part_info["ascii_domain"]

    # Construct the complete normalized form.
    ret.email = ret.local_part + "@" + ret.domain

    # If the email address has an ASCII form, add it.
    if not ret.smtputf8:
        ret.ascii_email = ret.ascii_local_part + "@" + ret.ascii_domain

    # If the email address has an ASCII representation, then we assume it may be
    # transmitted in ASCII (we can't assume SMTPUTF8 will be used on all hops to
    # the destination) and the length limit applies to ASCII characters (which is
    # the same as octets). The number of characters in the internationalized form
    # may be many fewer (because IDNA ASCII is verbose) and could be less than 254
    # Unicode characters, and of course the number of octets over the limit may
    # not be the number of characters over the limit, so if the email address is
    # internationalized, we can't give any simple information about why the address
    # is too long.
    #
    # In addition, check that the UTF-8 encoding (i.e. not IDNA ASCII and not
    # Unicode characters) is at most 254 octets. If the addres is transmitted using
    # SMTPUTF8, then the length limit probably applies to the UTF-8 encoded octets.
    # If the email address has an ASCII form that differs from its internationalized
    # form, I don't think the internationalized form can be longer, and so the ASCII
    # form length check would be sufficient. If there is no ASCII form, then we have
    # to check the UTF-8 encoding. The UTF-8 encoding could be up to about four times
    # longer than the number of characters.
    #
    # See the length checks on the local part and the domain.
    if ret.ascii_email and len(ret.ascii_email) > EMAIL_MAX_LENGTH:
        if ret.ascii_email == ret.email:
            reason = __get_length_reason(ret.ascii_email)
        elif len(ret.email) > EMAIL_MAX_LENGTH:
            # If there are more than 254 characters, then the ASCII
            # form is definitely going to be too long.
            reason = __get_length_reason(ret.email, utf8=True)
        else:
            reason = "(when converted to IDNA ASCII)"
        raise EmailSyntaxError("The provided Dartmouth email address is too long {}".format(reason))
    if len(ret.email.encode("utf8")) > EMAIL_MAX_LENGTH:
        if len(ret.email) > EMAIL_MAX_LENGTH:
            # If there are more than 254 characters, then the UTF-8
            # encoding is definitely going to be too long.
            reason = __get_length_reason(ret.email, utf8=True)
        else:
            reason = "(when encoded in bytes)"
        raise EmailSyntaxError("The provided Dartmouth email address is too long {}".format(reason))

    return ret


def validate_email_domain_part(domain):
    # Empty?
    if len(domain) == 0:
        raise EmailSyntaxError("There must be \'dartmouth.edu\' in your domain name (after the @-sign)")

    # Perform UTS-46 normalization, which includes casefolding, NFC normalization,
    # and converting all label separators (the period/full stop, fullwidth full stop,
    # ideographic full stop, and halfwidth ideographic full stop) to basic periods.
    # It will also raise an exception if there is an invalid character in the input,
    # such as "⒈" which is invalid because it would expand to include a period.
    try:
        domain = idna.uts46_remap(domain, std3_rules=False, transitional=False)
    except idna.IDNAError as e:
        raise EmailSyntaxError("The provided Dartmouth email domain name \'%s\' contains invalid characters (%s)"
                               % (domain, str(e)))

    # Now we can perform basic checks on the use of periods (since equivalent
    # symbols have been mapped to periods). These checks are needed because the
    # IDNA library doesn't handle well domains that have empty labels (i.e. initial
    # dot, trailing dot, or two dots in a row).
    if domain.endswith("."):
        raise EmailSyntaxError("The provided Dartmouth email address cannot end with a period")
    if domain.startswith("."):
        raise EmailSyntaxError("The provided Dartmouth email address cannot have a period immediately after the @-sign"
                               )
    if ".." in domain:
        raise EmailSyntaxError("The provided Dartmouth email address cannot have two periods in a row")

    # Regardless of whether international characters are actually used,
    # first convert to IDNA ASCII. For ASCII-only domains, the transformation
    # does nothing. If internationalized characters are present, the MTA
    # must either support SMTPUTF8 or the mail client must convert the
    # domain name to IDNA before submission.
    #
    # Unfortunately this step incorrectly 'fixes' domain names with leading
    # periods by removing them, so we have to check for this above. It also gives
    # a funky error message ("No input") when there are two periods in a
    # row, also checked separately above.
    try:
        ascii_domain = idna.encode(domain, uts46=False).decode("ascii")
    except idna.IDNAError as e:
        if "Domain too long" in str(e):
            # We can't really be more specific because UTS-46 normalization means
            # the length check is applied to a string that is different from the
            # one the user supplied. Also I'm not sure if the length check applies
            # to the internationalized form, the IDNA ASCII form, or even both!
            raise EmailSyntaxError("The provided Dartmouth email address is too long after the @-sign")
        raise EmailSyntaxError("The provided Dartmouth email domain name \'%s\' contains invalid characters (%s)"
                               % (domain, str(e)))

    # We may have been given an IDNA ASCII domain to begin with. Check
    # that the domain actually conforms to IDNA. It could look like IDNA
    # but not be actual IDNA. For ASCII-only domains, the conversion out
    # of IDNA just gives the same thing back.
    #
    # This gives us the canonical internationalized form of the domain,
    # which we should use in all error messages.
    try:
        domain_i18n = idna.decode(ascii_domain.encode('ascii'))
    except idna.IDNAError as e:
        raise EmailSyntaxError("The provided Dartmouth email domain name %s isn't valid IDNA (%s)"
                               % (ascii_domain, str(e)))

    # RFC 5321 4.5.3.1.2
    # We're checking the number of bytes (octets) here, which can be much
    # higher than the number of characters in internationalized domains,
    # on the assumption that the domain may be transmitted without SMTPUTF8
    # as IDNA ASCII. This is also checked by idna.encode, so this exception
    # is never reached.
    if len(ascii_domain) > DOMAIN_MAX_LENGTH:
        raise EmailSyntaxError("The provided Dartmouth email address is too long after the @-sign")

    if not re.search("dartmouth", ascii_domain):
        raise EmailSyntaxError(
            "The provided Dartmouth email domain isn't valid. It should have \'dartmouth\' after the @ sign"
        )

    if not re.search(".edu", ascii_domain):
        raise EmailSyntaxError(
            "The provided Dartmouth email domain isn't valid. It should have a \'.edu\' after \'dartmouth\'"
        )

    # Return the IDNA ASCII-encoded form of the domain, which is how it
    # would be transmitted on the wire (except when used with SMTPUTF8
    # possibly), as well as the canonical Unicode form of the domain,
    # which is better for display purposes. This should also take care
    # of RFC 6532 section 3.1's suggestion to apply Unicode NFC
    # normalization to addresses.
    return {
        "ascii_domain": ascii_domain,
        "domain": domain_i18n,
    }
