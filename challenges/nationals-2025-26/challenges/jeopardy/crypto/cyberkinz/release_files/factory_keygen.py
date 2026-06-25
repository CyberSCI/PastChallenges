# CyberKinz Corp. - Factory Key Generation Module (v1.0)
# Recovered from a salvaged factory floor terminal. Released to the public
# as part of the post-EMP "Right to Repair" disclosure act.
#
# This is the actual source used to encrypt registration cards on the
# manufacturing line. The BATCH_KEY value has been REDACTED.
#
# NOTE: The factory's hardware RNG was damaged during the EMP and was never
#       fully repaired. The same BATCH_KEY is generated for every card in a
#       single manufacturing batch.

from Crypto.Cipher import ARC4

# Loaded once at the start of every batch run by the factory line software.
# Should be 16 fresh random bytes per card. In practice (post-EMP), the
# RNG returns the same value for every card in a batch.
BATCH_KEY = bytes.fromhex("<REDACTED>")


def build_record(pet_name, username, password, serial, issued):
    """Build a fixed-width Registration Card v1 record.

    Field widths and offsets are documented in the customer-facing
    cyberkinz_manual.txt. Do not change without bumping the version string
    on the first line - downstream parsers depend on the exact byte layout.
    """
    return (
        b"CYBERKINZ_REGISTRATION_CARD_v1\n"
        b"PET_NAME......: " + pet_name.ljust(16).encode() + b"\n"
        b"USERNAME......: " + username.ljust(16).encode() + b"\n"
        b"PASSWORD......: " + password.ljust(16).encode() + b"\n"
        b"SERIAL........: " + serial.ljust(16).encode()   + b"\n"
        b"ISSUED........: " + issued.encode()             + b"\n"
        b"END_OF_RECORD\n"
    )


def encrypt_card(record_bytes):
    """RC4-encrypt a Registration Card under the current batch key."""
    cipher = ARC4.new(BATCH_KEY)
    return cipher.encrypt(record_bytes).hex()


# Example invocations (pseudo, real values come from the order DB):
#   record = build_record("Sparky", "alpha_unit", "c4nn3d_g00ds",
#                         "DEADBEEFCAFEBABE", "2025-08-14")
#   key_to_print_on_tag = encrypt_card(record)
#
#   record = build_record("Glitch", "viper92", "scr4p_m3t4l_99",
#                         "0xBADC0FFEE0DDF00D", "2025-09-19")
#   key_to_print_on_tag = encrypt_card(record)
