from zschema.leaves import *
from zschema.compounds import *

import zschema.registry

from ztag.annotation import Annotation

class CensysString(WhitespaceAnalyzedString):
    "default type for any strings in Censys"
    INCLUDE_RAW = True

__local_metadata = {}
for key in Annotation.LOCAL_METADATA_KEYS:
    __local_metadata[key] = CensysString()
local_metadata = SubRecord(__local_metadata)

# x509/pkix/pkix.go: Name
# zgrab_subj_issuer -> distinguished_name
zgrab_subj_issuer = SubRecord({
    "serial_number":ListOf(String()),
    "common_name":ListOf(CensysString()),
    "surname":ListOf(CensysString()),
    "country":ListOf(CensysString()),
    "locality":ListOf(CensysString()),
    "province":ListOf(CensysString()),
    "street_address":ListOf(CensysString()),
    "organization":ListOf(CensysString()),
    "organizational_unit":ListOf(CensysString()),
    "postal_code":ListOf(String()),
    "domain_component":ListOf(CensysString()),
    "email_address":ListOf(CensysString()),
    "given_name":ListOf(CensysString()),
    # EV Fields
    # Commented out 2017-08-18 due to ES analyzer mismatch:
    # Data with these fields got into the IPv4 index before the ES mapping
    # was updated, and ES automatically chose a different analyzer.
    # "jurisdiction_country":ListOf(CensysString()),
    # "jurisdiction_locality":ListOf(CensysString()),
    # "jurisdiction_province":ListOf(CensysString()),
})

# x509/pkix/pkix.go: Extension
unknown_extension = SubRecord({
    "id":OID(),
    "critical":Boolean(),
    "value":IndexedBinary(),
})

# x509/pkix/pkix.go: type EDIPartyName struct
edi_party_name = SubRecord({
    "name_assigner": CensysString(),
    "party_name": CensysString(),
})

# x509/extensions.go: GeneralNames/jsonGeneralNames
alternate_name = SubRecord({
    "dns_names":ListOf(FQDN()),
    "email_addresses":ListOf(EmailAddress()),
    "ip_addresses":ListOf(IPAddress()),
    "directory_names":ListOf(zgrab_subj_issuer),
    "edi_party_names":ListOf(edi_party_name),
    "other_names":ListOf(SubRecord({
        "id":OID(),
        "value":IndexedBinary(),
    })),
    "registered_ids":ListOf(OID()),
    "uniform_resource_identifiers":ListOf(URI()),
})

# json/dhe.go: cryptoParameter / auxCryptoParameter
crypto_parameter = SubRecord({
    "value": IndexedBinary(),
    "length": Unsigned16BitInteger(),
})

# json/dhe.go: DHParams / auxDHParams:
ztag_dh_params = SubRecord({
    "prime": crypto_parameter,
    "generator": crypto_parameter,
    "server_public": crypto_parameter,
    "server_private": crypto_parameter,
    "client_public": crypto_parameter,
    "client_private": crypto_parameter,
    "session_key": crypto_parameter,
})

# json/rsa.go: RSAPublicKey/auxRSAPublicKey (alias for crypto/rsa/PublicKey)
ztag_rsa_params = SubRecord({
    "exponent": Unsigned32BitInteger(),
    "modulus": IndexedBinary(),
    "length": Unsigned16BitInteger(doc="Bit-length of modulus.")
})

# json/ecdhe.go: TLSCurveID.MarshalJSON()
tls_curve_id = SubRecord({
    "name": String(),
    "id": Unsigned16BitInteger(),
})

# json/ecdhe.go: ECPoint.MarshalJSON()
ec_point = SubRecord({
    "x": crypto_parameter,
    "y": crypto_parameter,
})

# json/ecdhe.go: ECDHPrivateParams
ecdh_private_params = SubRecord({
    "value": IndexedBinary(required=False),
    "length": Unsigned16BitInteger(required=False),
})

# json/ecdhe.go: ECDHParams
ztag_ecdh_params = SubRecord({
    "curve_id": tls_curve_id,
    "server_public": ec_point,
    "server_private": ecdh_private_params,
    "client_public": ec_point,
    "client_private": ecdh_private_params,
})

# x509/json.go (mapped from crypto.dsa)
# (dsa_public_key)
ztag_dsa_params = SubRecord({
    "p": IndexedBinary(),
    "q": IndexedBinary(),
    "g": IndexedBinary(),
    "y": IndexedBinary(),
})

# x509/json.go (mapped from crypto.ecdsa)
# (ecdsa_public_key)
ztag_ssh_ecdsa_public_key = SubRecord({
    "pub": IndexedBinary(),
    "b": IndexedBinary(),
    "gx": IndexedBinary(),
    "gy": IndexedBinary(),
    "n": IndexedBinary(),
    "p": IndexedBinary(),
    "x": IndexedBinary(),
    "y": IndexedBinary(),
    "curve": Enum(["P-224", "P-256", "P-384", "P-521"]),
    "length": Unsigned16BitInteger(),
    # schema conflict in censys prod cert index
    #"asn1_oid":OID(), # TODO: this is currently commented out
    # because for a bunch of certificates, this was encoded as [1, 2,
    # 840, 113549, 1, 1, 12] not 1.2.840.113549.1.1.12
})



# Unused? Not defined in zcrypto.
ztag_ed25519_public_key = SubRecord({
    "public_bytes":IndexedBinary(),
})

# x509/ct/types.go: SignedCertificateTimestamp.
ztag_sct = SubRecord({
    "version":Unsigned8BitInteger(),
    "log_id":IndexedBinary(),
    # Note: log_name is not present in the struct.
    "log_name":String(),
    "timestamp":Timestamp(),
    "signature":Binary(),
    "extensions":Binary(),
})

# x509/json.go: auxGeneralSubtreeIP (modifies GeneralSubtreeIP from x509.go)
# (general_subtree_ip)
expanded_cidr = SubRecord({
    "cidr":String(),
    "begin":IPAddress(),
    "end":IPAddress(),
    "mask":IPAddress(),
}, exclude=["bigquery",]) # XXX

# x509/extensions.go: type NoticeReference struct
notice_reference = SubRecord({
    "organization": CensysString(),
    "notice_numbers": ListOf(Signed32BitInteger()),
})

# x509/extensions.go: type UserNoticeData struct
user_notice_data = SubRecord({
    "explicit_text": EnglishString(),
    "notice_reference": ListOf(notice_reference),
})

# x509/extensions.go: type CertificatePoliciesJSON struct
certificate_policy = SubRecord({
    "id": OID(),
    "cps": String(),
    "user_notice": ListOf(user_notice_data),
})

# x509/extensions.go: type CertificatePoliciesJSON struct
certificate_policy = SubRecord({
    "id": OID(),
    "name": String(),
    "cps": ListOf(URL()),
    # FIXME: Isn't this a ListOf(...)? see x509/extensions.go line 82
    "user_notice": user_notice_data
}, exclude=["bigquery",]) # XXX

# Generated by zcrypto/x509/extended_key_usage.sh, with a manual tweak on unknown
extended_key_usage = SubRecord({
    "value": ListOf(Signed32BitInteger()), # TODO: remove after reparse
    "any": Boolean(),
    "apple_code_signing": Boolean(),
    "apple_code_signing_development": Boolean(),
    "apple_code_signing_third_party": Boolean(),
    "apple_crypto_development_env": Boolean(),
    "apple_crypto_env": Boolean(),
    "apple_crypto_maintenance_env": Boolean(),
    "apple_crypto_production_env": Boolean(),
    "apple_crypto_qos": Boolean(),
    "apple_crypto_test_env": Boolean(),
    "apple_crypto_tier0_qos": Boolean(),
    "apple_crypto_tier1_qos": Boolean(),
    "apple_crypto_tier2_qos": Boolean(),
    "apple_crypto_tier3_qos": Boolean(),
    "apple_ichat_encryption": Boolean(),
    "apple_ichat_signing": Boolean(),
    "apple_resource_signing": Boolean(),
    "apple_software_update_signing": Boolean(),
    "apple_system_identity": Boolean(),
    "client_auth": Boolean(),
    "code_signing": Boolean(),
    "dvcs": Boolean(),
    "eap_over_lan": Boolean(),
    "eap_over_ppp": Boolean(),
    "email_protection": Boolean(),
    "ipsec_end_system": Boolean(),
    "ipsec_tunnel": Boolean(),
    "ipsec_user": Boolean(),
    "microsoft_ca_exchange": Boolean(),
    "microsoft_cert_trust_list_signing": Boolean(),
    "microsoft_csp_signature": Boolean(),
    "microsoft_document_signing": Boolean(),
    "microsoft_drm": Boolean(),
    "microsoft_drm_individualization": Boolean(),
    "microsoft_efs_recovery": Boolean(),
    "microsoft_embedded_nt_crypto": Boolean(),
    "microsoft_encrypted_file_system": Boolean(),
    "microsoft_enrollment_agent": Boolean(),
    "microsoft_kernel_mode_code_signing": Boolean(),
    "microsoft_key_recovery_21": Boolean(),
    "microsoft_key_recovery_3": Boolean(),
    "microsoft_license_server": Boolean(),
    "microsoft_licenses": Boolean(),
    "microsoft_lifetime_signing": Boolean(),
    "microsoft_mobile_device_software": Boolean(),
    "microsoft_nt5_crypto": Boolean(),
    "microsoft_oem_whql_crypto": Boolean(),
    "microsoft_qualified_subordinate": Boolean(),
    "microsoft_root_list_signer": Boolean(),
    "microsoft_server_gated_crypto": Boolean(),
    "microsoft_sgc_serialized": Boolean(),
    "microsoft_smart_display": Boolean(),
    "microsoft_smartcard_logon": Boolean(),
    "microsoft_system_health": Boolean(),
    "microsoft_system_health_loophole": Boolean(),
    "microsoft_timestamp_signing": Boolean(),
    "microsoft_whql_crypto": Boolean(),
    "netscape_server_gated_crypto": Boolean(),
    "ocsp_signing": Boolean(),
    "sbgp_cert_aa_service_auth": Boolean(),
    "server_auth": Boolean(),
    "time_stamping": Boolean(),
    # NOTE: unknown is actually included in the JSON.
    # "unknown": ListOf(OID()),
})

zgrab_parsed_certificate = SubRecord({
    "subject": zgrab_subj_issuer,
    "subject_dn": CensysString(),
    "issuer": zgrab_subj_issuer,
    "issuer_dn": CensysString(),
    "version": Unsigned8BitInteger(),
    "serial_number": String(doc="Serial number as an signed decimal integer. "\
                                "Stored as string to support >uint lengths. "\
                                "Negative values are allowed."),
    "validity": SubRecord({
        "start": Timestamp(doc="Timestamp of when certificate is first valid. Timezone is UTC."),
        "end": Timestamp(doc="Timestamp of when certificate expires. Timezone is UTC."),
        "length": Signed64BitInteger(),
    }),
    "signature_algorithm": SubRecord({
        "name": String(),
        "oid": OID(),
    }),
    "subject_key_info": SubRecord({
        "fingerprint_sha256": HexString(),
        # x509/json.go: auxPublicKeyAlgorithm
        "key_algorithm": SubRecord({
            "name": String(doc="Name of public key type, e.g., RSA or ECDSA. "\
                               "More information is available the named SubRecord "\
                               "(e.g., rsa_public_key)."),
            "oid": OID(doc="OID of the public key on the certificate. "\
                           "This is helpful when an unknown type is present. "\
                           "This field is reserved and not current populated.")
        }),
        "rsa_public_key": ztag_rsa_params,
        "dsa_public_key": ztag_dsa_params,
        "ecdsa_public_key": ztag_ssh_ecdsa_public_key
    }),
    "extensions": SubRecord({
        "key_usage": SubRecord({
            "value": Unsigned16BitInteger("Integer value of the bitmask in the extension"),
            "digital_signature": Boolean(),
            "certificate_sign": Boolean(),
            "crl_sign": Boolean(),
            "content_commitment": Boolean(),
            "key_encipherment": Boolean(),
            "data_encipherment": Boolean(),
            "key_agreement": Boolean(),
            "decipher_only": Boolean(),
            "encipher_only": Boolean(),
        }),
        "basic_constraints": SubRecord({
            "is_ca": Boolean(),
            "max_path_len": Signed32BitInteger(),
        }),
        "subject_alt_name": alternate_name,
        "issuer_alt_name": alternate_name,
        "crl_distribution_points" :ListOf(URL()),
        "authority_key_id" :HexString(),
        "subject_key_id": HexString(),
        "extended_key_usage": extended_key_usage,
        "certificate_policies": ListOf(certificate_policy),
        "authority_info_access": SubRecord({
            "ocsp_urls": ListOf(URL()),
            "issuer_urls": ListOf(URL())
        }),
        "name_constraints": SubRecord({
            "critical": Boolean(),
            "permitted_names": ListOf(FQDN()),
            # We do not schema email addresses as an EmailAddress per
            # rfc5280#section-4.2.1.10 documentation:
            # A name constraint for Internet mail addresses MAY specify a
            # particular mailbox, all addresses at a particular host, or all
            # mailboxes in a domain.  To indicate a particular mailbox, the
            # constraint is the complete mail address.  For example,
            # "root@example.com" indicates the root mailbox on the host
            # "example.com".  To indicate all Internet mail addresses on a
            # particular host, the constraint is specified as the host name.  For
            # example, the constraint "example.com" is satisfied by any mail
            # address at the host "example.com".  To specify any address within a
            # domain, the constraint is specified with a leading period (as with
            # URIs).  For example, ".example.com" indicates all the Internet mail
            # addresses in the domain "example.com", but not Internet mail
            # addresses on the host "example.com".
            "permitted_email_addresses": ListOf(CensysString()),
            "permitted_ip_addresses": ListOf(expanded_cidr),
            "permitted_directory_names": ListOf(zgrab_subj_issuer),
            "permitted_registered_ids": ListOf(OID()),
            "permitted_edi_party_names": ListOf(edi_party_name),
            "excluded_names": ListOf(FQDN()),
            "excluded_email_addresses": ListOf(CensysString()),
            "excluded_ip_addresses": ListOf(expanded_cidr),
            "excluded_directory_names": ListOf(zgrab_subj_issuer),
            "excluded_registered_ids": ListOf(OID()),
            "excluded_edi_party_names": ListOf(edi_party_name),

        }),
        "signed_certificate_timestamps": ListOf(ztag_sct),
        "ct_poison": Boolean()
    }),
    "unknown_extensions": ListOf(unknown_extension),
    "signature": SubRecord({
        "signature_algorithm": SubRecord({
            "name": String(),
            "oid": OID(),
        }),
        "value": IndexedBinary(),
        "valid": Boolean(),
        "self_signed": Boolean(),
    }),
    "fingerprint_md5": HexString(),
    "fingerprint_sha1": HexString(),
    "fingerprint_sha256": HexString(),
    "spki_subject_fingerprint": HexString(),
    "tbs_fingerprint": HexString(),
    "tbs_noct_fingerprint": HexString(),
    "names": ListOf(FQDN()),
    "__expanded_names":ListOf(String()),
    "validation_level":Enum(),
    "redacted": Boolean(),
})

zgrab_certificate_trust = SubRecord({
    "type": Enum(doc="root, intermediate, or leaf certificate"),
    "trusted_path": Boolean(doc="Does certificate chain up to browser root store"),
    "valid": Boolean(doc="is this certificate currently valid in this browser"),
    "was_valid": Boolean(doc="was this certificate ever valid in this browser")
})

zgrab_certificate = SubRecord({
    "raw": Binary(),
    "parsed": zgrab_parsed_certificate,
    "validation": SubRecord({
        "nss": zgrab_certificate_trust,
        "apple": zgrab_certificate_trust,
        "microsoft": zgrab_certificate_trust,
        "android": zgrab_certificate_trust,
        "java": zgrab_certificate_trust,
    }),
    "lint": lint
})

zgrab_server_certificate_valid = SubRecord({
    "complete_chain": Boolean(doc="does server provide a chain up to a root"),
    "valid": Boolean(doc="is this certificate currently valid in this browser"),
    "error": CensysString()
})

ztag_tls = SubRecord({
    "version":String(),
    "cipher_suite":SubRecord({
        "id":String(),
        "name":CensysString(),
    }),
    "ocsp_stapling":Boolean(),
    "secure_renegotiation":Boolean(),
    "certificate":zgrab_certificate,
    "chain":ListOf(zgrab_certificate),
    "scts":ListOf(ztag_sct),
    "session_ticket":SubRecord({
        "length":Unsigned32BitInteger(),
        "lifetime_hint":Unsigned32BitInteger(),
    }),
    "validation":SubRecord({
        "matches_domain":Boolean(),
        "browser_trusted":Boolean(),
        #"stores":SubRecord({
        #    "nss":zgrab_server_certificate_valid,
        #    "microsoft":zgrab_server_certificate_valid,
        #    "apple":zgrab_server_certificate_valid,
        #    "java":zgrab_server_certificate_valid,
        #    "android":zgrab_server_certificate_valid,
        #})
    }),
    "server_key_exchange":SubRecord({
        "ecdh_params":ztag_ecdh_params,
        "dh_params":ztag_dh_params,
        "rsa_params":ztag_rsa_params,
    }),
    "signature":SubRecord({
        "valid":Boolean(),
        "signature_error":CensysString(),
        "signature_algorithm":String(),
        "hash_algorithm":String(),
    }),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_sslv2 = SubRecord({
    "support": Boolean(),
    "extra_clear": Boolean(),
    "export": Boolean(),
    "certificate": zgrab_certificate,
    "ciphers": ListOf(SubRecord({
        "name": String(),
        "id": Unsigned32BitInteger(),
    })),
    "metadata": local_metadata,
    "timestamp":Timestamp(),
})

ztag_heartbleed = SubRecord({
    "heartbeat_enabled":Boolean(),
    "heartbleed_vulnerable":Boolean(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_extended_random = SubRecord({
    "extended_random_support": Boolean(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_smtp_starttls = SubRecord({
    "banner": CensysString(),
    "ehlo": CensysString(),
    "starttls": CensysString(),
    "tls": ztag_tls,
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_mail_starttls = SubRecord({
    "banner": CensysString(),
    "starttls": CensysString(),
    "tls": ztag_tls,
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_mail_tls = SubRecord({
    "tls":ztag_tls,
    "banner": CensysString(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

zgrab_unknown_http_header = SubRecord({
    "key":String(),
    "value":CensysString()
})

zgrab_http_headers = SubRecord({
    "access_control_allow_origin":CensysString(),
    "accept_patch":CensysString(),
    "accept_ranges":CensysString(),
    "age":CensysString(),
    "allow":CensysString(),
    "alt_svc":CensysString(),
    "alternate_protocol":CensysString(),
    "cache_control":CensysString(),
    "connection":CensysString(),
    "content_disposition":CensysString(),
    "content_encoding":CensysString(),
    "content_language":CensysString(),
    "content_length":CensysString(),
    "content_location":CensysString(),
    "content_md5":CensysString(),
    "content_range":CensysString(),
    "content_type":CensysString(),
    "date":CensysString(),
    "etag":CensysString(),
    "expires":CensysString(),
    "last_modified":CensysString(),
    "link":CensysString(),
    "location":CensysString(),
    "p3p":CensysString(),
    "pragma":CensysString(),
    "proxy_authenticate":CensysString(),
    "public_key_pins":CensysString(),
    "refresh":CensysString(),
    # Currently misindexed in IPv4 schema
    #"referer":CensysString(),
    "retry_after":CensysString(),
    "server":CensysString(),
    "set_cookie":CensysString(),
    "status":CensysString(),
    "strict_transport_security":CensysString(),
    "trailer":CensysString(),
    "transfer_encoding":CensysString(),
    "upgrade":CensysString(),
    "vary":CensysString(),
    "via":CensysString(),
    "warning":CensysString(),
    "www_authenticate":CensysString(),
    "x_frame_options":CensysString(),
    "x_xss_protection":CensysString(),
    "content_security_policy":CensysString(),
    "x_content_security_policy":CensysString(),
    "x_webkit_csp":CensysString(),
    "x_content_type_options":CensysString(),
    "x_powered_by":CensysString(),
    "x_ua_compatible":CensysString(),
    "x_content_duration":CensysString(),
    "proxy_agent":CensysString(),
    "unknown":ListOf(zgrab_unknown_http_header)
})

ztag_http = SubRecord({
    "status_code":Unsigned16BitInteger(),
    "status_line":CensysString(),
    "body":HTML(),
    "headers":zgrab_http_headers,
    "body_sha256":HexString(),
    "title":CensysString(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_dh_export = SubRecord({
    "dh_params":ztag_dh_params,
    "support":Boolean(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_dh = SubRecord({
    "dh_params":ztag_dh_params,
    "support":Boolean(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_rsa_export = SubRecord({
    "rsa_params":ztag_rsa_params,
    "support":Boolean(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_ecdh = SubRecord({
    "ecdh_params":ztag_ecdh_params,
    "support":Boolean(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})


golang_crypto_param = SubRecord({
    "value":IndexedBinary(),
    "length":Unsigned32BitInteger()
})

#ztag_open_proxy = SubRecord({
#    "connect":SubRecord({
#      "status_code":Integer(),
#      "status_line":CensysString(),
#      "body":CensysString(),
#      "headers":zgrab_http_headers
#    }),
#    "get":SubRecord({
#      "status_code":Integer(),
#      "status_line":CensysString(),
#      "body":CensysString(),
#      "headers":zgrab_http_headers,
#      "random_present":Boolean(),
#      "body_sha256":HexString()
#    }),
#    "metadata":local_metadata
#})

ztag_ssh_v2 = SubRecord({
    "metadata":local_metadata,
    "timestamp":Timestamp(),
    "banner":SubRecord({
        "raw":CensysString(),
        "version":String(),
        "software":CensysString(),
        "comment":CensysString(),
    }),
    "support":SubRecord({
        "kex_algorithms":ListOf(String()),
        "host_key_algorithms":ListOf(String()),
        "first_kex_follows":Boolean(),
        "client_to_server":SubRecord({
            "ciphers":ListOf(String()),
            "macs":ListOf(String()),
            "compressions":ListOf(String()),
            "languages":ListOf(String()),
        }),
        "server_to_client":SubRecord({
            "ciphers":ListOf(String()),
            "macs":ListOf(String()),
            "compressions":ListOf(String()),
            "languages":ListOf(String()),
        }),
    }),
    "selected":SubRecord({
        "kex_algorithm":String(),
        "host_key_algorithm":String(),
        "client_to_server": SubRecord({
            "cipher":String(),
            "mac":String(),
            "compression":String(),
        }),
        "server_to_client": SubRecord({
            "cipher":String(),
            "mac":String(),
            "compression":String(),
        }),
    }),
    "key_exchange": SubRecord({
        "ecdh_params": SubRecord({
            "server_public": SubRecord({
                "x": golang_crypto_param,
                "y": golang_crypto_param,
            }),
        }),
        "dh_params": SubRecord({
            "prime": golang_crypto_param,
            "generator": golang_crypto_param,
        }),
    }),
    "server_host_key":SubRecord({
        "key_algorithm":String(),
        "fingerprint_sha256":HexString(),
        "rsa_public_key":ztag_rsa_params,
        "dsa_public_key":ztag_dsa_params,
        "ecdsa_public_key":ztag_ssh_ecdsa_public_key,
        "ed25519_public_key":ztag_ed25519_public_key,
        "certkey_public_key":SubRecord({
            "nonce":IndexedBinary(),
            "key":SubRecord({
                "fingerprint_sha256":HexString(),
                "algorithm":String(),
                "rsa_public_key":ztag_rsa_params,
                "dsa_public_key":ztag_dsa_params,
                "ecdsa_public_key":ztag_ssh_ecdsa_public_key,
                "ed25519_public_key":ztag_ed25519_public_key,
            }),
            "serial":String(),
            "type":SubRecord({
                "id":Unsigned32BitInteger(),
                "name":String(),
            }),
            "key_id":String(),
            "valid_principals":ListOf(String()),
            "validity":SubRecord({
                "valid_after":Timestamp(doc="Timestamp of when certificate is first valid. Timezone is UTC."),
                "valid_before":Timestamp(doc="Timestamp of when certificate expires. Timezone is UTC."),
                "length":Signed64BitInteger(),
            }),
            "signature_key":SubRecord({
                "fingerprint_sha256":HexString(),
                "key_algorithm":String(),
                "rsa_public_key":ztag_rsa_params,
                "dsa_public_key":ztag_dsa_params,
                "ecdsa_public_key":ztag_ssh_ecdsa_public_key,
                "ed25519_public_key":ztag_ed25519_public_key,
            }),
            "signature":SubRecord({
                "signature_algorithm":SubRecord({
                    "name":String(),
                }),
                "value":IndexedBinary(),
            }),
            "parse_error":String(),
            "extensions":SubRecord({
                "permit_X11_forwarding":Boolean(),
                "permit_agent_forwarding":Boolean(),
                "permit_port_forwarding":Boolean(),
                "permit_pty":Boolean(),
                "permit_user_rc":Boolean(),
                "unknown":ListOf(String()),
            }),
            "critical_options":SubRecord({
                "force_command":Boolean(),
                "source_address":Boolean(),
                "unknown":ListOf(String()),
            }),
        }),
    }),
})

ztag_ftp = SubRecord({
    "banner":CensysString(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

telnet_caps_list = ListOf(SubRecord({
    "name":String(),
    "value":Unsigned32BitInteger()
}))

ztag_telnet = SubRecord({
    "support":Boolean(),
    "banner":CensysString(),
    "will":telnet_caps_list,
    "wont":telnet_caps_list,
    "do":telnet_caps_list,
    "dont":telnet_caps_list,
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_modbus = SubRecord({
    "support":Boolean(),
    "function_code":Unsigned16BitInteger(),
    "mei_response":SubRecord({
      "conformity_level":Signed32BitInteger(),
      "objects":SubRecord({
        "vendor":CensysString(),
        "product_code":CensysString(),
        "revision":CensysString(),
        "vendor_url":URL(),
        "product_name":CensysString(),
        "model_name":CensysString(),
        "user_application_name":CensysString(),
      })
    }),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_bacnet = SubRecord({
    "support":Boolean(),
    "instance_number": Signed32BitInteger(),
    "vendor": SubRecord({
        "id": Signed32BitInteger(),
        "reported_name":CensysString(),
        "official_name":CensysString(),
    }),
    "firmware_revision": String(),
    "application_software_revision":String(),
    "object_name":CensysString(),
    "model_name":CensysString(),
    "description":CensysString(),
    "location":CensysString(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_dns_question = SubRecord({
    "name":String(),
    "type":String()
})


ztag_dns_answer = SubRecord({
    "name":String(),
    "response":CensysString(),
    "type":String()
})

ztag_dns_lookup = SubRecord({
    "support":Boolean(),
    "errors":Boolean(),
    "open_resolver":Boolean(),
    "resolves_correctly":Boolean(),
    "answers":ListOf(ztag_dns_answer),
    "authorities":ListOf(ztag_dns_answer),
    "additionals":ListOf(ztag_dns_answer),
    "questions":ListOf(ztag_dns_question),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_tls_support = SubRecord({
    "support": Boolean(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_fox = SubRecord({
    "support":Boolean(),
    "version":CensysString(),
    "id":Signed32BitInteger(),
    "hostname":CensysString(),
    "host_address":CensysString(),
    "app_name":CensysString(),
    "app_version":CensysString(),
    "vm_name":CensysString(),
    "vm_version":CensysString(),
    "os_name":CensysString(),
    "os_version":CensysString(),
    "station_name":CensysString(),
    "language":CensysString(),
    "time_zone":CensysString(),
    "host_id":CensysString(),
    "vm_uuid":CensysString(),
    "brand_id":CensysString(),
    "sys_info":CensysString(),
    "auth_agent_type":String(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_dnp3 = SubRecord({
    "support":Boolean(),
    "raw_response":Binary(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_s7 = SubRecord({
    "support":Boolean(),
    "system":CensysString(),
    "module":CensysString(),
    "plant_id":CensysString(),
    "copyright":CensysString(),
    "serial_number":CensysString(),
    "reserved_for_os":CensysString(),
    "module_type":CensysString(),
    "memory_serial_number":CensysString(),
    "cpu_profile":CensysString(),
    "oem_id":CensysString(),
    "location":CensysString(),
    "module_id":CensysString(),
    "hardware":CensysString(),
    "firmware":CensysString(),
    "metadata":local_metadata,
    "timestamp":Timestamp(),
})

ztag_smb = SubRecord({
    "smbv1_support":Boolean(),
})

ztag_schemas = [
    ("ztag_https", ztag_tls),
    ("ztag_heartbleed", ztag_heartbleed),
    ("ztag_smtp_starttls", ztag_smtp_starttls),
    ("ztag_imap_starttls", ztag_mail_starttls),
    ("ztag_pop3_starttls", ztag_mail_starttls),
    ("ztag_imap_tls", ztag_mail_tls),
    ("ztag_pop3_tls", ztag_mail_tls),
    ("ztag_http", ztag_http),
    ("ztag_ftp", ztag_ftp),
    ("ztag_dh", ztag_dh),
    ("ztag_dh_export", ztag_dh_export),
    ("ztag_rsa_export", ztag_rsa_export),
    ("ztag_ecdh", ztag_ecdh),
    ("ztag_sslv2", ztag_sslv2),
    ("ztag_sslv3", ztag_tls_support),
    ("ztag_tls1", ztag_tls_support),
    ("ztag_tls2", ztag_tls_support),
    ("ztag_tls3", ztag_tls_support),
    ("ztag_modbus", ztag_modbus),
    ("ztag_extended_random", ztag_extended_random),
    ("ztag_ssh_v2", ztag_ssh_v2),
    ("ztag_dns_lookup", ztag_dns_lookup),
    ("ztag_bacnet", ztag_bacnet),
    ("ztag_fox", ztag_fox),
    ("ztag_dnp3", ztag_dnp3),
    ("ztag_s7", ztag_s7),
    ("ztag_smb", ztag_smb),
]
for (name, schema) in ztag_schemas:
    x = Record({
        "ip_address":IPv4Address(required=True),
        #"timestamp":Timestamp(required=True),
        "tags":ListOf(String()),
        "metadata": SubRecord({}, allow_unknown=True),
    }, extends=schema)
    zschema.registry.register_schema("%s" % name, x)


ztag_lookup_spf = SubRecord({
    "raw":CensysString(),
})

ztag_lookup_dmarc = SubRecord({
    "raw":CensysString(),
    "p":String(),
})

ztag_lookup_axfr = SubRecord({
    "servers":ListOf(SubRecord({
        "name":FQDN(),
        "support":Boolean(),
        "error":CensysString(),
        "records":ListOf(SubRecord({
            "name":FQDN(),
            "type":String(),
            "data":CensysString(),
            "ttl":Unsigned32BitInteger()
        })),
    })),
    "truncated":Boolean(),
    "support":Boolean()
})

_zdb_location_fields = {
    "continent":String(),
    "country":CensysString(),
    "country_code":String(),
    "city":CensysString(),
    "postal_code":String(),
    "timezone":CensysString(),
    "province":CensysString(),
    "latitude":Double(),
    "longitude":Double(),
    "registered_country":CensysString(),
    "registered_country_code":String(),
}

zdb_location = SubRecord(_zdb_location_fields)
zdb_restricted_location = SubRecord(_zdb_location_fields, exclude=["bigquery",])

zdb_as = SubRecord({
    "asn":Unsigned32BitInteger(),
    "description":CensysString(),
    "path":ListOf(Unsigned32BitInteger()),
    "rir":String(),
    "routed_prefix":FQDN(),
    "name":CensysString(),
    "country_code":String(),
    "organization":CensysString(),
})


__metadata = {}
for key in Annotation.GLOBAL_METADATA_KEYS:
    __metadata[key] = CensysString()
zdb_metadata = SubRecord(__metadata)

CTServerStatus = SubRecord({
    "index":Signed64BitInteger(),
    "added_to_ct_at":Timestamp(),
    "ct_to_censys_at":Timestamp(),
    "censys_to_ct_at":Timestamp(),
    "sct":Binary(),
})

CTStatus = SubRecord({
    # Censys (reserved)
    "censys_dev":CTServerStatus,
    "censys":CTServerStatus,
    # Google
    "google_aviator":CTServerStatus,
    "google_pilot":CTServerStatus,
    "google_rocketeer":CTServerStatus,
    "google_submariner":CTServerStatus,
    "google_testtube":CTServerStatus,
    "google_icarus":CTServerStatus,
    "google_skydiver":CTServerStatus,
    "google_daedalus":CTServerStatus,
    # Google Argon
    "google_argon_2017":CTServerStatus,
    "google_argon_2018":CTServerStatus,
    "google_argon_2019":CTServerStatus,
    "google_argon_2020":CTServerStatus,
    "google_argon_2021":CTServerStatus,
    # Cloudflare
    "cloudflare_nimbus_2017":CTServerStatus,
    "cloudflare_nimbus_2018":CTServerStatus,
    "cloudflare_nimbus_2019":CTServerStatus,
    "cloudflare_nimbus_2020":CTServerStatus,
    "cloudflare_nimbus_2021":CTServerStatus,
    # Digicert
    "digicert_ct1":CTServerStatus,
    "digicert_ct2":CTServerStatus,
    # Izenpe
    "izenpe_com_ct":CTServerStatus,
    "izenpe_eus_ct":CTServerStatus,
    # Symantec
    "symantec_ws_ct":CTServerStatus,
    "symantec_ws_vega":CTServerStatus,
    "symantec_ws_sirius":CTServerStatus,
    "symantec_ws_deneb":CTServerStatus,
    # Comodo
    "comodo_dodo":CTServerStatus,
    "comodo_mammoth":CTServerStatus,
    "comodo_sabre":CTServerStatus,
    # Wosign, StartCom, Wotrus
    "wosign_ctlog":CTServerStatus,
    "wosign_ct":CTServerStatus,
    "startssl_ct":CTServerStatus,
    "wotrus_ctlog":CTServerStatus,
    "wotrus_ctlog3":CTServerStatus,
    # GDCA
    "gdca_ct":CTServerStatus,
    "gdca_ctlog":CTServerStatus,
    "gdca_log":CTServerStatus,
    "gdca_log2":CTServerStatus,
    # Venafi
    "venafi_api_ctlog":CTServerStatus,
    "venafi_api_ctlog_gen2":CTServerStatus,
    # Nordu
    "nordu_ct_plausible":CTServerStatus,
    # Let's Encrypt
    "letsencrypt_ct_clicky":CTServerStatus,
    # Other
    "cnnic_ctserver":CTServerStatus,
    "certly_log":CTServerStatus,
    "sheca_ct":CTServerStatus,
    "behind_the_sofa":CTServerStatus,
    "certificatetransparency_cn_ct":CTServerStatus,

})

CertificateAudit = SubRecord({
    "ccadb":SubRecord({
        "current_in_intermediates":Boolean(),
        "was_in_intermediates":Boolean(),
        "owner_name":CensysString(),
        "parent_name":CensysString(),
        "certificate_name":CensysString(),
        "certificate_policy":CensysString(),
        "certification_practice_statement":CensysString(),
        "cp_same_as_parent":CensysString(), # TODO: Boolean
        "audit_same_as_parent":CensysString(), # TODO: Boolean
        "standard_audit":CensysString(),
        "br_audit":CensysString(),
        "auditor":CensysString(),
        "standard_audit_statement_timestamp":Timestamp(),
        "management_assertions_by":CensysString(),
        "comments":EnglishString(es_include_raw=True),
        #"ev_policy_oids":CensysString(), # TODO
        #"approval_bug":CensysString(), # TODO
        #"first_nss_release":CensysString(), # TODO
        #"first_firefox_release":CensysString(), # TODO
        #"ev_audit":CensysString(),
        "current_in_roots":Boolean(),
        "was_in_roots":Boolean(),
        #"test_website_valid":CensysString(), # TODO
        #"mozilla_applied_constraints":CensysString(), #TODO
        #"company_website":CensysString(), # TODO
        #"geographic_focus":CensysString(), # TODO
        #"standard_audit_type":CensysString(), # TODO
     })
})

ztag_certificate_validation = SubRecord({
    "valid":Boolean(doc="((has_trusted_path && !revoked && !blacklisted) || whitelisted) && !expired"),
    "was_valid":Boolean(doc="True if the certificate is valid now or was ever valid in the past."),
    "trusted_path":Boolean(doc="True if there exists a path from the certificate to the root store."),
    "had_trusted_path":Boolean(doc="True if now or at some point in the past there existed a path "
                                   "from the certificate to the root store."),
    "blacklisted":Boolean(doc="True if the certificate is explicitly blacklisted by some method than OneCRL/CRLSet. "
                              "For example, a set of certificates revoked by Cloudflare are blacklisted by SPKI hash in Chrome."),
    "whitelisted":Boolean(doc="True if the certificate is explicitly whitelisted, "
                              "e.g. the set of trusted WoSign certificates Apple uses."),
    "type":Enum(["leaf","intermediate","root","unknown"], doc="Indicates if the certificate is a root, intermediate, or leaf."),
    "paths":NestedListOf(HexString(), "path"),
    "in_revocation_set":Boolean(doc="True if the certificate is in the revocation set (e.g. OneCRL) associated with this root store."),
    "parents":ListOf(HexString()),
})

class LintBool(String):

    ES_TYPE = "boolean"

# Lints can have any of the following outputs:
#   - RESERVED [should never happen]
#   - NA [not applicable]
#   - NE [not applicable]
#   - PASS [test success]
#   - INFO [failed for info]
#   - WARN [failed for warn]
#   - FAIL [failed for error]
#   - FATAL [test could not complete because cert is broken]
#   - UNKNOWN [should never occur]
# We don't want to store a string for every lint in elasticsearch because
# our index size would explode. Instead we map these to a string:
# {
#     (reserved, unknown, ne, na, pass) -> null,
#     (notice, warning, fail, fatal) -> true
# }
# For BigQuery, we have more options, so we allow some more information:
# {
#     all map to original value
# }
# This is horrible to schema, so define a custom type
Lints = SubRecord({
    "e_basic_constraints_not_critical":LintBool(),
    "e_ca_common_name_missing":LintBool(),
    "e_ca_country_name_invalid":LintBool(),
    "e_ca_country_name_missing":LintBool(),
    "e_ca_crl_sign_not_set":LintBool(),
    "e_ca_is_ca":LintBool(),
    "e_ca_key_cert_sign_not_set":LintBool(),
    "e_ca_key_usage_missing":LintBool(),
    "e_ca_key_usage_not_critical":LintBool(),
    "e_ca_organization_name_missing":LintBool(),
    "e_ca_subject_field_empty":LintBool(),
    "e_cab_dv_conflicts_with_locality":LintBool(),
    "e_cab_dv_conflicts_with_org":LintBool(),
    "e_cab_dv_conflicts_with_postal":LintBool(),
    "e_cab_dv_conflicts_with_province":LintBool(),
    "e_cab_dv_conflicts_with_street":LintBool(),
    "e_cab_iv_requires_personal_name":LintBool(),
    "e_cab_ov_requires_org":LintBool(),
    "e_cert_contains_unique_identifier":LintBool(),
    "e_cert_extensions_version_not_3":LintBool(),
    "e_cert_policy_iv_requires_country":LintBool(),
    "e_cert_policy_iv_requires_province_or_locality":LintBool(),
    "e_cert_policy_ov_requires_country":LintBool(),
    "e_cert_policy_ov_requires_province_or_locality":LintBool(),
    "e_cert_unique_identifier_version_not_2_or_3":LintBool(),
    "e_distribution_point_incomplete":LintBool(),
    "e_dnsname_bad_character_in_label":LintBool(),
    "e_dnsname_contains_bare_iana_suffix":LintBool(),
    "e_dnsname_empty_label":LintBool(),
    "e_dnsname_hyphen_in_sld":LintBool(),
    "e_dnsname_label_too_long":LintBool(),
    "e_dnsname_left_label_wildcard_correct":LintBool(),
    "e_dnsname_not_valid_tld":LintBool(),
    "e_dnsname_underscore_in_sld":LintBool(),
    "e_dnsname_wildcard_only_in_left_label":LintBool(),
    "e_dsa_correct_order_in_subgroup":LintBool(),
    "e_dsa_improper_modulus_or_divisor_size":LintBool(),
    "e_dsa_params_missing":LintBool(),
    "e_dsa_shorter_than_2048_bits":LintBool(),
    "e_dsa_unique_correct_representation":LintBool(),
    "e_ec_improper_curves":LintBool(),
    "e_ev_business_category_missing":LintBool(),
    "e_ev_country_name_missing":LintBool(),
    "e_ev_locality_name_missing":LintBool(),
    "e_ev_organization_name_missing":LintBool(),
    "e_ev_serial_number_missing":LintBool(),
    "e_ev_valid_time_too_long":LintBool(),
    "e_ext_aia_marked_critical":LintBool(),
    "e_ext_authority_key_identifier_critical":LintBool(),
    "e_ext_authority_key_identifier_missing":LintBool(),
    "e_ext_authority_key_identifier_no_key_identifier":LintBool(),
    "e_ext_cert_policy_disallowed_any_policy_qualifier":LintBool(),
    "e_ext_cert_policy_duplicate":LintBool(),
    "e_ext_cert_policy_explicit_text_ia5_string":LintBool(),
    "e_ext_cert_policy_explicit_text_too_long":LintBool(),
    "e_ext_duplicate_extension":LintBool(),
    "e_ext_freshest_crl_marked_critical":LintBool(),
    "e_ext_ian_dns_not_ia5_string":LintBool(),
    "e_ext_ian_empty_name":LintBool(),
    "e_ext_ian_no_entries":LintBool(),
    "e_ext_ian_rfc822_format_invalid":LintBool(),
    "e_ext_ian_space_dns_name":LintBool(),
    "e_ext_ian_uri_format_invalid":LintBool(),
    "e_ext_ian_uri_host_not_fqdn_or_ip":LintBool(),
    "e_ext_ian_uri_not_ia5":LintBool(),
    "e_ext_ian_uri_relative":LintBool(),
    "e_ext_key_usage_cert_sign_without_ca":LintBool(),
    "e_ext_key_usage_without_bits":LintBool(),
    "e_ext_name_constraints_not_critical":LintBool(),
    "e_ext_name_constraints_not_in_ca":LintBool(),
    "e_ext_policy_constraints_empty":LintBool(),
    "e_ext_policy_constraints_not_critical":LintBool(),
    "e_ext_policy_map_any_policy":LintBool(),
    "e_ext_san_contains_reserved_ip":LintBool(),
    "e_ext_san_directory_name_present":LintBool(),
    "e_ext_san_dns_name_too_long":LintBool(),
    "e_ext_san_dns_not_ia5_string":LintBool(),
    "e_ext_san_edi_party_name_present":LintBool(),
    "e_ext_san_empty_name":LintBool(),
    "e_ext_san_missing":LintBool(),
    "e_ext_san_no_entries":LintBool(),
    "e_ext_san_not_critical_without_subject":LintBool(),
    "e_ext_san_other_name_present":LintBool(),
    "e_ext_san_registered_id_present":LintBool(),
    "e_ext_san_rfc822_format_invalid":LintBool(),
    "e_ext_san_rfc822_name_present":LintBool(),
    "e_ext_san_space_dns_name":LintBool(),
    "e_ext_san_uniform_resource_identifier_present":LintBool(),
    "e_ext_san_uri_format_invalid":LintBool(),
    "e_ext_san_uri_host_not_fqdn_or_ip":LintBool(),
    "e_ext_san_uri_not_ia5":LintBool(),
    "e_ext_san_uri_relative":LintBool(),
    "e_ext_subject_directory_attr_critical":LintBool(),
    "e_ext_subject_key_identifier_critical":LintBool(),
    "e_ext_subject_key_identifier_missing_ca":LintBool(),
    "e_generalized_time_does_not_include_seconds":LintBool(),
    "e_generalized_time_includes_fraction_seconds":LintBool(),
    "e_generalized_time_not_in_zulu":LintBool(),
    "e_ian_bare_wildcard":LintBool(),
    "e_ian_dns_name_includes_null_char":LintBool(),
    "e_ian_dns_name_starts_with_period":LintBool(),
    "e_ian_wildcard_not_first":LintBool(),
    "e_inhibit_any_policy_not_critical":LintBool(),
    "e_international_dns_name_not_nfkc":LintBool(),
    "e_international_dns_name_not_unicode":LintBool(),
    "e_invalid_certificate_version":LintBool(),
    "e_issuer_field_empty":LintBool(),
    "e_name_constraint_empty":LintBool(),
    "e_name_constraint_maximum_not_absent":LintBool(),
    "e_name_constraint_minimum_non_zero":LintBool(),
    "e_old_root_ca_rsa_mod_less_than_2048_bits":LintBool(),
    "e_old_sub_ca_rsa_mod_less_than_1024_bits":LintBool(),
    "e_old_sub_cert_rsa_mod_less_than_1024_bits":LintBool(),
    "e_path_len_constraint_improperly_included":LintBool(),
    "e_path_len_constraint_zero_or_less":LintBool(),
    "e_public_key_type_not_allowed":LintBool(),
    "e_root_ca_extended_key_usage_present":LintBool(),
    "e_root_ca_key_usage_must_be_critical":LintBool(),
    "e_root_ca_key_usage_present":LintBool(),
    "e_rsa_exp_negative":LintBool(),
    "e_rsa_mod_less_than_2048_bits":LintBool(),
    "e_rsa_no_public_key":LintBool(),
    "e_rsa_public_exponent_not_odd":LintBool(),
    "e_rsa_public_exponent_too_small":LintBool(),
    "e_san_bare_wildcard":LintBool(),
    "e_san_dns_name_includes_null_char":LintBool(),
    "e_san_dns_name_starts_with_period":LintBool(),
    "e_san_wildcard_not_first":LintBool(),
    "e_serial_number_longer_than_20_octets":LintBool(),
    "e_serial_number_not_positive":LintBool(),
    "e_signature_algorithm_not_supported":LintBool(),
    "e_sub_ca_aia_does_not_contain_ocsp_url":LintBool(),
    "e_sub_ca_aia_marked_critical":LintBool(),
    "e_sub_ca_aia_missing":LintBool(),
    "e_sub_ca_certificate_policies_missing":LintBool(),
    "e_sub_ca_crl_distribution_points_does_not_contain_url":LintBool(),
    "e_sub_ca_crl_distribution_points_marked_critical":LintBool(),
    "e_sub_ca_crl_distribution_points_missing":LintBool(),
    "e_sub_ca_eku_missing":LintBool(),
    "e_sub_ca_eku_name_constraints":LintBool(),
    "e_sub_ca_must_not_contain_any_policy":LintBool(),
    "e_sub_cert_aia_does_not_contain_ocsp_url":LintBool(),
    "e_sub_cert_aia_marked_critical":LintBool(),
    "e_sub_cert_aia_missing":LintBool(),
    "e_sub_cert_cert_policy_empty":LintBool(),
    "e_sub_cert_certificate_policies_missing":LintBool(),
    "e_sub_cert_country_name_must_appear":LintBool(),
    "e_sub_cert_crl_distribution_points_does_not_contain_url":LintBool(),
    "e_sub_cert_crl_distribution_points_marked_critical":LintBool(),
    "e_sub_cert_eku_missing":LintBool(),
    "e_sub_cert_eku_server_auth_client_auth_missing":LintBool(),
    "e_sub_cert_given_name_surname_contains_correct_policy":LintBool(),
    "e_sub_cert_key_usage_cert_sign_bit_set":LintBool(),
    "e_sub_cert_key_usage_crl_sign_bit_set":LintBool(),
    "e_sub_cert_locality_name_must_appear":LintBool(),
    "e_sub_cert_locality_name_must_not_appear":LintBool(),
    "e_sub_cert_not_is_ca":LintBool(),
    "e_sub_cert_or_sub_ca_using_sha1":LintBool(),
    "e_sub_cert_postal_code_must_not_appear":LintBool(),
    "e_sub_cert_province_must_appear":LintBool(),
    "e_sub_cert_province_must_not_appear":LintBool(),
    "e_sub_cert_street_address_should_not_exist":LintBool(),
    "e_sub_cert_valid_time_too_long":LintBool(),
    "e_subject_common_name_max_length":LintBool(),
    "e_subject_common_name_not_from_san":LintBool(),
    "e_subject_contains_noninformational_value":LintBool(),
    "e_subject_contains_reserved_ip":LintBool(),
    "e_subject_country_not_iso":LintBool(),
    "e_subject_empty_without_san":LintBool(),
    "e_subject_info_access_marked_critical":LintBool(),
    "e_subject_locality_name_max_length":LintBool(),
    "e_subject_not_dn":LintBool(),
    "e_subject_organization_name_max_length":LintBool(),
    "e_subject_organizational_unit_name_max_length":LintBool(),
    "e_subject_state_name_max_length":LintBool(),
    "e_utc_time_does_not_include_seconds":LintBool(),
    "e_utc_time_not_in_zulu":LintBool(),
    "e_validity_time_not_positive":LintBool(),
    "e_wrong_time_format_pre2050":LintBool(),
    "n_ca_digital_signature_not_set":LintBool(),
    "n_contains_redacted_dnsname":LintBool(),
    "n_sub_ca_eku_not_technically_constrained":LintBool(),
    "n_subject_common_name_included":LintBool(),
    "w_distribution_point_missing_ldap_or_uri":LintBool(),
    "w_dnsname_underscore_in_trd":LintBool(),
    "w_dnsname_wildcard_left_of_public_suffix":LintBool(),
    "w_eku_critical_improperly":LintBool(),
    "w_ext_aia_access_location_missing":LintBool(),
    "w_ext_cert_policy_contains_noticeref":LintBool(),
    "w_ext_cert_policy_explicit_text_includes_control":LintBool(),
    "w_ext_cert_policy_explicit_text_not_nfc":LintBool(),
    "w_ext_cert_policy_explicit_text_not_utf8":LintBool(),
    "w_ext_crl_distribution_marked_critical":LintBool(),
    "w_ext_ian_critical":LintBool(),
    "w_ext_key_usage_not_critical":LintBool(),
    "w_ext_policy_map_not_critical":LintBool(),
    "w_ext_policy_map_not_in_cert_policy":LintBool(),
    "w_ext_san_critical_with_subject_dn":LintBool(),
    "w_ext_subject_key_identifier_missing_sub_cert":LintBool(),
    "w_ian_iana_pub_suffix_empty":LintBool(),
    "w_issuer_dn_leading_whitespace":LintBool(),
    "w_issuer_dn_trailing_whitespace":LintBool(),
    "w_multiple_issuer_rdn":LintBool(),
    "w_multiple_subject_rdn":LintBool(),
    "w_name_constraint_on_edi_party_name":LintBool(),
    "w_name_constraint_on_registered_id":LintBool(),
    "w_name_constraint_on_x400":LintBool(),
    "w_root_ca_basic_constraints_path_len_constraint_field_present":LintBool(),
    "w_root_ca_contains_cert_policy":LintBool(),
    "w_rsa_mod_factors_smaller_than_752":LintBool(),
    "w_rsa_mod_not_odd":LintBool(),
    "w_rsa_public_exponent_not_in_range":LintBool(),
    "w_san_iana_pub_suffix_empty":LintBool(),
    "w_serial_number_low_entropy":LintBool(),
    "w_sub_ca_aia_does_not_contain_issuing_ca_url":LintBool(),
    "w_sub_ca_certificate_policies_marked_critical":LintBool(),
    "w_sub_ca_eku_critical":LintBool(),
    "w_sub_ca_name_constraints_not_critical":LintBool(),
    "w_sub_cert_aia_does_not_contain_issuing_ca_url":LintBool(),
    "w_sub_cert_certificate_policies_marked_critical":LintBool(),
    "w_sub_cert_eku_extra_values":LintBool(),
    "w_sub_cert_sha1_expiration_too_long":LintBool(),
    "w_subject_dn_leading_whitespace":LintBool(),
    "w_subject_dn_trailing_whitespace":LintBool(),
})


ZLint = SubRecord({
    "version":Unsigned16BitInteger(),
    "notices_present":Boolean(),
    "warnings_present":Boolean(),
    "errors_present":Boolean(),
    "fatals_present":Boolean(),
    "lints":Lints,
})

certificate = Record({
    "parsed":zgrab_parsed_certificate,
    "raw":Binary(),
    "fingerprint_sha256":HexString(),
    "tags":ListOf(CensysString()),
    "metadata":SubRecord({
        "updated_at":Timestamp(),
        "added_at":Timestamp(),
        "post_processed":Boolean(),
        "post_processed_at":Timestamp(),
        "seen_in_scan":Boolean(),
        "source":String(),
        "parse_version":Unsigned16BitInteger(),
        "parse_error":CensysString(),
        "parse_status":String(),
    }),
    "parents":ListOf(String()),
    "parent_spki_subject_fingerprint":HexString(),
    "validation":SubRecord({
        "nss":ztag_certificate_validation,
        "apple":ztag_certificate_validation,
        "microsoft":ztag_certificate_validation,
        #"java":ztag_certificate_validation,
        #"android":ztag_certificate_validation,
        "google_ct_primary":ztag_certificate_validation,
        #"google_ct_submariner":ztag_certificate_validation,
    }),
    "ct":CTStatus,
    "audit":CertificateAudit,
    "zlint":ZLint,
    "precert":Boolean()
})

zschema.registry.register_schema("certificate", certificate)

ipv4_host = Record({
            Port(443):SubRecord({
                "https":SubRecord({
                    "tls":ztag_tls,
                    "heartbleed":ztag_heartbleed,
                    "dhe": ztag_dh,
                    "rsa_export": ztag_rsa_export,
                    "dhe_export": ztag_dh_export,
                    #"ssl_2": ztag_sslv2, # XXX
                    "tls_1_1": ztag_tls_support,
                    "tls_1_2": ztag_tls_support,
                    #"tls_1_3": ztag_tls_support,
                    "ecdhe": ztag_ecdh,
                    #"extended_random":ztag_extended_random,
                })
            }),
            Port(80):SubRecord({
                "http":SubRecord({
                    "get":ztag_http,
                }),
            }),
            Port(8080):SubRecord({
                "http":SubRecord({
                    "get":ztag_http,
                }),
            }),
            Port(8888):SubRecord({
                "http":SubRecord({
                    "get":ztag_http,
                }),
            }),
            Port(25):SubRecord({
                "smtp":SubRecord({
                    "starttls": ztag_smtp_starttls,
                    #"ssl_2": ztag_sslv2, # XXX
                }),
            }),
            Port(23):SubRecord({
                "telnet":SubRecord({
                    "banner":ztag_telnet
                })
            }),
            Port(2323):SubRecord({
                "telnet":SubRecord({
                    "banner":ztag_telnet
                })
            }),
            Port(21):SubRecord({
                "ftp":SubRecord({
                  "banner":ztag_ftp,
                })
            }),
            Port(102):SubRecord({
                "s7":SubRecord({
                    "szl":ztag_s7
                })
            }),
            Port(110):SubRecord({
                "pop3":SubRecord({
                    "starttls":ztag_mail_starttls,
                    #"ssl_2": ztag_sslv2, # XXX
                })
            }),
            Port(143):SubRecord({
                "imap":SubRecord({
                    "starttls":ztag_mail_starttls,
                    #"ssl_2": ztag_sslv2, # XXX
                })
            }),
            Port(445):SubRecord({
                "smb":SubRecord({
                    "banner":ztag_smb
                })
            }),
            Port(993):SubRecord({
                "imaps":SubRecord({
                    "tls":ztag_mail_tls,
                    #"ssl_2": ztag_sslv2, # XXX
                })
            }),
            Port(995):SubRecord({
                "pop3s":SubRecord({
                    "tls":ztag_mail_tls,
                    #"ssl_2": ztag_sslv2, # XXX
                })
            }),
            Port(587):SubRecord({
                "smtp":SubRecord({
                    "starttls": ztag_smtp_starttls,
                    #"ssl_2": ztag_sslv2,  # XXX
                })
            }),
            Port(502):SubRecord({
                "modbus":SubRecord({
                    "device_id":ztag_modbus
                })
            }),
            Port(22):SubRecord({
                "ssh":SubRecord({
                    "v2": ztag_ssh_v2
                }),
            }),
            Port(53):SubRecord({
                "dns":SubRecord({
                    "lookup":ztag_dns_lookup
                })
            }),
            Port(47808):SubRecord({
                "bacnet":SubRecord({
                    "device_id":ztag_bacnet
                })
            }),
            Port(1911):SubRecord({
                "fox":SubRecord({
                    "device_id":ztag_fox
                })
            }),
            Port(20000):SubRecord({
                "dnp3":SubRecord({
                    "status":ztag_dnp3,
                })
            }),
            Port(7547):SubRecord({
                "cwmp":SubRecord({
                    "get":ztag_http,
                })
            }),

            "tags":ListOf(CensysString()),
            "metadata":zdb_metadata,
            "location":zdb_location,
            "__restricted_location":zdb_restricted_location,
            "autonomous_system":zdb_as,
            "notes":CensysString(),
            "ip":IPv4Address(required=True),
            "ipint":Unsigned32BitInteger(required=True, doc="Integer value of IP address in host order"),
            "updated_at":Timestamp(),
            "zdb_version":Unsigned32BitInteger(),
            "protocols":ListOf(CensysString(exclude=["bigquery"])),
            "ports":ListOf(Unsigned16BitInteger())
})

website = Record({
            Port(443):SubRecord({
                "https":SubRecord({
                    "tls":ztag_tls,
                    "heartbleed":ztag_heartbleed,
                    "dhe": ztag_dh,
                    "rsa_export": ztag_rsa_export,
                    "dhe_export": ztag_dh_export,
                    "tls_1_1": ztag_tls_support,
                    "tls_1_2": ztag_tls_support,
                    "ecdhe": ztag_ecdh,
                }),
                "https_www":SubRecord({
                    "tls":ztag_tls,
                })
            }),
            Port(80):SubRecord({
                "http":SubRecord({
                    "get":ztag_http,
                }),
                "http_www":SubRecord({
                    "get":ztag_http,
                }),
            }),
            Port(25):SubRecord({
                "smtp":SubRecord({
                    "starttls": ztag_smtp_starttls,
                })
            }),
            Port(0):SubRecord({
                "lookup":SubRecord({
                    "spf":ztag_lookup_spf,
                    "dmarc":ztag_lookup_dmarc,
                    "axfr":ztag_lookup_axfr,
                })
            }),

            "tags":ListOf(CensysString()),
            "metadata":zdb_metadata,
            "notes":EnglishString(es_include_raw=True),
            "domain":String(),
            "alexa_rank":Unsigned32BitInteger(doc="Rank in the Alexa Top 1 Million. "
                    "Null if not currently in the Top 1 Million sites."),
            "updated_at":Timestamp(),
            "zdb_version":Unsigned32BitInteger(),
            "protocols":ListOf(String()),
            "ports":ListOf(Unsigned16BitInteger())
})


DROP_KEYS = {'ip_address', 'metadata', 'tags', 'timestamp'}

zschema.registry.register_schema("ipv4host", ipv4_host)
zschema.registry.register_schema("website", website)
