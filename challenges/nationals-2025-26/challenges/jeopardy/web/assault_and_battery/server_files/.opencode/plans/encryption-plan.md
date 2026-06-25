# Encrypt bulletin posts with password-derived keys

**Session ID:** ses_336dc642affey44n0dyuVJd5lo
**Created:** 3/7/2026, 11:31:20 AM
**Updated:** 3/7/2026, 11:33:17 AM

---

## User

How would I design a system where, when a bulletin post gets saved, it gets encrypted using a key derived from the user's password? See @bulletin/models.py for reference.

---

## Assistant (Plan · anthropic/claude-opus-4.5 · 65.5s)

Looking at the code, I can see you have a `BulletinPost` model with an `is_classified` field and a TODO comment about encrypting classified posts. The `save()` method currently only saves non-classified posts.

Here's how I'd design a password-derived encryption system:

## Design Overview

### 1. Key Derivation

Use **PBKDF2** or **Argon2** to derive an encryption key from the user's password:

```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key for AES-256
        salt=salt,
        iterations=600_000,  # OWASP recommended minimum
    )
    return kdf.derive(password.encode())
```

### 2. Model Changes

Add fields to store encryption metadata:

```python
class BulletinPost(UserCreatedObject):
    title: models.TextField[str] = title_field()
    body: models.TextField[str] = body_field()
    is_classified: models.BooleanField[bool] = models.BooleanField()

    # Encryption fields
    encryption_salt: models.BinaryField = models.BinaryField(null=True, blank=True)
    encryption_nonce: models.BinaryField = models.BinaryField(null=True, blank=True)
    # Store encrypted body separately or in-place
```

### 3. Encryption/Decryption Flow

Use **AES-GCM** for authenticated encryption:

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_content(plaintext: str, key: bytes) -> tuple[bytes, bytes]:
    """Returns (ciphertext, nonce)"""
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return ciphertext, nonce

def decrypt_content(ciphertext: bytes, key: bytes, nonce: bytes) -> str:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
```

### 4. Modified `save()` Method

```python
def save(self, password: str | None = None, **kwargs):
    if self.is_classified:
        if password is None:
            raise ValueError("Password required for classified posts")

        salt = os.urandom(16)
        key = derive_key(password, salt)
        ciphertext, nonce = encrypt_content(self.body, key)

        self.body = base64.b64encode(ciphertext).decode()  # or use BinaryField
        self.encryption_salt = salt
        self.encryption_nonce = nonce

    super().save(**kwargs)
```

## Critical Design Questions

Before implementing, I need clarification on a few things:

**Tool: question**

**Input:**

```json
{
  "questions": [
    {
      "question": "How should the password be passed to the save() method? Options affect architecture significantly.",
      "header": "Password Passing Strategy",
      "options": [
        {
          "label": "Pass at save time",
          "description": "Caller provides password directly to save(). Simple but requires password available at save."
        },
        {
          "label": "Session-cached key",
          "description": "Derive key at login, cache in session. More complex but better UX - user doesn't re-enter password."
        },
        {
          "label": "Separate encryption step",
          "description": "encrypt() method called separately before save(). More explicit control."
        }
      ]
    },
    {
      "question": "What happens when a user changes their password?",
      "header": "Password Change Handling",
      "options": [
        {
          "label": "Re-encrypt all posts",
          "description": "On password change, decrypt with old password, re-encrypt with new. Requires old password."
        },
        {
          "label": "Key-wrapping approach",
          "description": "Store a master key encrypted by password-derived key. Only re-wrap master key on password change."
        },
        {
          "label": "Posts stay with old key",
          "description": "Old posts remain encrypted with old-password-derived key. User must remember old password."
        }
      ]
    },
    {
      "question": "Should encrypted posts be shareable with other users?",
      "header": "Multi-user Access",
      "options": [
        {
          "label": "Author-only",
          "description": "Only the post author can decrypt. Simplest approach."
        },
        {
          "label": "Shared with specific users",
          "description": "Allow sharing encrypted posts. Requires per-user encrypted keys or shared secrets."
        }
      ]
    }
  ]
}
```

**Output:**

```
User has answered your questions: "How should the password be passed to the save() method? Options affect architecture significantly."="Session-cached key", "What happens when a user changes their password?"="Re-encrypt all posts", "Should encrypted posts be shareable with other users?"="Shared with specific users". You can now continue with the user's answers in mind.
```

---

## Assistant (Plan · anthropic/claude-opus-4.5 · 32.3s)

Thanks for the clarifications. This is a more sophisticated design. Let me outline the full architecture:

## Refined Design: Session-Cached Keys with Multi-User Sharing

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Login                              │
│  password → PBKDF2 → user_key → decrypt(wrapped_master_key) │
│                           ↓                                  │
│                    master_key (cached in session)            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    BulletinPost Save                         │
│  content → AES-GCM(post_key) → ciphertext                   │
│  post_key → AES-GCM(master_key) → wrapped_post_key          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Sharing with User B                       │
│  post_key → AES-GCM(user_B_master_key) → shared_key_entry   │
└─────────────────────────────────────────────────────────────┘
```

### New Models Required

```python
class UserEncryptionKey(models.Model):
    """Stores user's master key, wrapped by their password-derived key"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wrapped_master_key = models.BinaryField()  # master_key encrypted with password-derived key
    key_salt = models.BinaryField()  # salt for PBKDF2
    key_nonce = models.BinaryField()  # nonce for AES-GCM

class PostEncryptionKey(models.Model):
    """Per-post symmetric key, wrapped by author's master key"""
    post = models.OneToOneField(BulletinPost, on_delete=models.CASCADE)
    wrapped_key = models.BinaryField()  # post_key encrypted with author's master_key
    key_nonce = models.BinaryField()

class SharedPostAccess(models.Model):
    """Allows other users to access a post's key"""
    post = models.ForeignKey(BulletinPost, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wrapped_key = models.BinaryField()  # post_key encrypted with this user's master_key
    key_nonce = models.BinaryField()

    class Meta:
        unique_together = ['post', 'user']
```

### Key Flows

**1. User Registration/Master Key Setup:**

```python
def setup_user_encryption(user: User, password: str):
    master_key = os.urandom(32)  # Generate random master key
    salt = os.urandom(16)
    password_key = derive_key(password, salt)
    wrapped_master, nonce = encrypt_content(master_key, password_key)

    UserEncryptionKey.objects.create(
        user=user,
        wrapped_master_key=wrapped_master,
        key_salt=salt,
        key_nonce=nonce
    )
```

**2. Login (Cache Master Key in Session):**

```python
def login_and_cache_key(request, user: User, password: str):
    user_key = UserEncryptionKey.objects.get(user=user)
    password_key = derive_key(password, user_key.key_salt)
    master_key = decrypt_content(user_key.wrapped_master_key, password_key, user_key.key_nonce)

    request.session['master_key'] = base64.b64encode(master_key).decode()
```

**3. Save Classified Post:**

```python
def save(self, request=None, **kwargs):
    if self.is_classified:
        master_key = base64.b64decode(request.session['master_key'])

        # Generate per-post key
        post_key = os.urandom(32)

        # Encrypt content
        ciphertext, content_nonce = encrypt_content(self.body, post_key)
        self.body = base64.b64encode(ciphertext).decode()
        self.encryption_nonce = content_nonce

        super().save(**kwargs)

        # Store wrapped post key
        wrapped_post_key, key_nonce = encrypt_content(post_key, master_key)
        PostEncryptionKey.objects.create(
            post=self,
            wrapped_key=wrapped_post_key,
            key_nonce=key_nonce
        )
```

**4. Password Change (Re-encrypt All):**

```python
def change_password(user: User, old_password: str, new_password: str):
    user_key = UserEncryptionKey.objects.get(user=user)

    # Decrypt master key with old password
    old_password_key = derive_key(old_password, user_key.key_salt)
    master_key = decrypt_content(user_key.wrapped_master_key, old_password_key, user_key.key_nonce)

    # Re-wrap master key with new password
    new_salt = os.urandom(16)
    new_password_key = derive_key(new_password, new_salt)
    new_wrapped, new_nonce = encrypt_content(master_key, new_password_key)

    user_key.wrapped_master_key = new_wrapped
    user_key.key_salt = new_salt
    user_key.key_nonce = new_nonce
    user_key.save()
```

**5. Share Post with Another User:**

```python
def share_post(post: BulletinPost, target_user: User, sharer_master_key: bytes):
    # Get post key
    post_key_record = PostEncryptionKey.objects.get(post=post)
    post_key = decrypt_content(post_key_record.wrapped_key, sharer_master_key, post_key_record.key_nonce)

    # Get target user's master key (requires their session or a key exchange mechanism)
    target_key = UserEncryptionKey.objects.get(user=target_user)
    # NOTE: This is where it gets tricky - see question below
```

## Important Security Consideration

**Tool: question**

**Input:**

```json
{
  "questions": [
    {
      "question": "For sharing, how should user A get user B's public key to wrap the post key? This is a fundamental challenge in multi-user encryption.",
      "header": "Key Exchange for Sharing",
      "options": [
        {
          "label": "Asymmetric keypair per user",
          "description": "Each user has RSA/EC keypair. Public key stored in DB. Share by encrypting post_key with recipient's public key."
        },
        {
          "label": "Server-mediated sharing",
          "description": "Server temporarily has access to keys during share operation. Simpler but less secure - server sees plaintext keys."
        },
        {
          "label": "Out-of-band shared secret",
          "description": "Users exchange a shared passphrase out-of-band, used to derive a shared key. Most secure but worst UX."
        }
      ]
    }
  ]
}
```

**Output:**

```
User has answered your questions: "For sharing, how should user A get user B's public key to wrap the post key? This is a fundamental challenge in multi-user encryption."="Asymmetric keypair per user". You can now continue with the user's answers in mind.
```

---

## Assistant (Plan · anthropic/claude-opus-4.5 · 19.5s)

Good choice - that's the most robust approach. Here's the complete design:

## Final Design: Hybrid Encryption with Asymmetric Key Exchange

### Updated Model Structure

```python
class UserEncryptionKey(models.Model):
    """User's encryption keys"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Master symmetric key (wrapped by password-derived key)
    wrapped_master_key = models.BinaryField()
    master_key_salt = models.BinaryField()
    master_key_nonce = models.BinaryField()

    # Asymmetric keypair for receiving shared content
    public_key = models.BinaryField()  # X25519 or RSA public key (stored plaintext)
    wrapped_private_key = models.BinaryField()  # Private key wrapped by master_key
    private_key_nonce = models.BinaryField()
```

### Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER REGISTRATION                          │
├──────────────────────────────────────────────────────────────────┤
│  1. Generate master_key (random 32 bytes)                        │
│  2. Generate asymmetric keypair (X25519 recommended)             │
│  3. password → PBKDF2(salt) → password_key                       │
│  4. AES-GCM(password_key, master_key) → wrapped_master_key       │
│  5. AES-GCM(master_key, private_key) → wrapped_private_key       │
│  6. Store: wrapped_master_key, salt, public_key, wrapped_private │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                           LOGIN                                   │
├──────────────────────────────────────────────────────────────────┤
│  1. password → PBKDF2(stored_salt) → password_key                │
│  2. Decrypt wrapped_master_key → master_key                      │
│  3. Decrypt wrapped_private_key → private_key                    │
│  4. Cache master_key + private_key in session (encrypted)        │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    SAVE CLASSIFIED POST                           │
├──────────────────────────────────────────────────────────────────┤
│  1. Generate post_key (random 32 bytes)                          │
│  2. AES-GCM(post_key, content) → encrypted_body                  │
│  3. AES-GCM(master_key, post_key) → wrapped_post_key             │
│  4. Store encrypted_body in post, wrapped_post_key in PostKey    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    SHARE POST WITH USER B                         │
├──────────────────────────────────────────────────────────────────┤
│  1. Decrypt post_key using author's master_key                   │
│  2. Fetch User B's public_key from DB                            │
│  3. ECIES/RSA-OAEP(B_public_key, post_key) → shared_wrapped_key  │
│  4. Store in SharedPostAccess for User B                         │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                 USER B DECRYPTS SHARED POST                       │
├──────────────────────────────────────────────────────────────────┤
│  1. Fetch SharedPostAccess entry for this post                   │
│  2. ECIES/RSA-OAEP(B_private_key, shared_wrapped_key) → post_key │
│  3. AES-GCM(post_key, encrypted_body) → plaintext                │
└──────────────────────────────────────────────────────────────────┘
```

### Recommended Libraries

```python
# For symmetric encryption (AES-GCM)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# For key derivation (PBKDF2)
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# For asymmetric encryption (X25519 + HKDF + AES-GCM = ECIES-like)
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Or simpler: RSA-OAEP
from cryptography.hazmat.primitives.asymmetric import rsa, padding
```

### Session Security Note

For session storage, consider encrypting the cached keys with a session-specific key or using Django's signed cookies:

```python
# Don't store raw keys - at minimum base64 encode, ideally encrypt
request.session['_enc_keys'] = fernet.encrypt(json.dumps({
    'master_key': base64.b64encode(master_key).decode(),
    'private_key': base64.b64encode(private_key).decode(),
}).encode()).decode()
```

---

## Summary: Files to Create/Modify

| File                              | Changes                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `bulletin/models.py`              | Add `UserEncryptionKey`, `PostEncryptionKey`, `SharedPostAccess` models; modify `BulletinPost` and `Comment` |
| `bulletin/crypto.py` (new)        | Encryption/decryption utilities                                                                              |
| `bulletin/views.py` or auth views | Login flow to cache decrypted keys                                                                           |
| `bulletin/signals.py` (new)       | User registration signal to create keypair                                                                   |
| `settings.py`                     | Add `cryptography` to requirements                                                                           |

Would you like me to proceed with implementation, or do you have any questions about this design?

---
