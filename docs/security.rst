Security Guide
==============

VaultConfig provides two levels of security for protecting sensitive configuration data.

Security Levels
---------------

Password Obscuring
~~~~~~~~~~~~~~~~~~

**Purpose**: Hide passwords from casual viewing (shoulder surfing, accidental exposure)

**Method**: AES-CTR encryption with a fixed key + URL-safe base64 encoding

**Security Level**: Low - This is NOT secure encryption

**Key Points**:

- Anyone with access to the VaultConfig source code can decrypt
- Provides convenience, not security
- Similar to rclone's config obscuring
- Useful for preventing casual exposure in logs, screens, or backups
- A security warning is logged on first use to remind users

**Use When**:

- Config files are in a secure location
- You want to prevent shoulder surfing
- You need quick access without passwords
- Security is not critical

Config File Encryption
~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Strong encryption of entire config files

**Method**: NaCl secretbox (XSalsa20-Poly1305) with PBKDF2-HMAC-SHA256 key derivation

**Security Level**: High - Authenticated encryption with strong algorithms

**Key Points**:

- Uses PyNaCl (libsodium) for encryption
- Password is derived using PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023 recommended)
- Random 16-byte salt generated per encryption
- Authenticated encryption prevents tampering
- Lost password = lost data (no recovery)
- Minimum password length: 4 characters (12+ strongly recommended)
- Warnings shown for weak or short passwords

**Use When**:

- Security is critical
- Config files contain highly sensitive data
- You have a secure password management system
- Config files might be exposed or shared

Encryption Details
------------------

Password Obscuring Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Algorithm:

- AES-256 in CTR mode
- 128-bit random initialization vector (IV)
- Fixed key embedded in code (unique to VaultConfig)
- URL-safe base64 encoding

Format:

.. code-block:: text

   <base64(IV + ciphertext)>

Example:

.. code-block:: text

   eCkF3jAC0hI7TEpStvKvWf64gocJJQ

Security Warning:

.. warning::

   Password obscuring is NOT secure! Anyone with the VaultConfig source code
   can reveal obscured passwords. Use config file encryption for real security.

Config File Encryption Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Algorithm:

- NaCl secretbox (XSalsa20-Poly1305)
- 256-bit key derived from password using PBKDF2-HMAC-SHA256
- 600,000 iterations (OWASP 2023 recommended)
- Random 16-byte salt per encryption
- 192-bit random nonce per encryption
- Authenticated encryption (prevents tampering)

Key Derivation:

.. code-block:: python

   salt = random_bytes(16)  # Random 16-byte salt
   key = PBKDF2-HMAC-SHA256(password, salt, iterations=600000, length=32)

Format:

.. code-block:: text

   VAULTCONFIG_ENCRYPT_V1:
   <base64(salt + nonce + ciphertext + tag)>

Example:

.. code-block:: text

   VAULTCONFIG_ENCRYPT_V1:
   aGVsbG8gd29ybGQgdGhpcyBpcyBhIHRlc3QgZW5jcnlwdGVkIGRhdGE=

Security Improvements in V1:

- Replaced single SHA-256 with PBKDF2 (600,000 iterations)
- Random salt per encryption (prevents rainbow tables)
- Atomic file writes (prevents partial/corrupted files)
- Secure file permissions from creation (0600)
- Secure deletion of temp files on error
- Password validation with warnings

Best Practices
--------------

Password Management
~~~~~~~~~~~~~~~~~~~

**DO**:

- Use strong, unique passwords (12+ characters recommended, 4 minimum)
- Store passwords in a password manager
- Use ``VAULTCONFIG_PASSWORD_COMMAND`` with password managers
- Rotate passwords periodically
- Use different passwords for different environments
- Heed password strength warnings

**DON'T**:

- Use weak or common passwords
- Use passwords shorter than 12 characters for sensitive data
- Store passwords in plain text files
- Reuse passwords across systems
- Share passwords via insecure channels
- Hard-code passwords in scripts
- Use shell=True with untrusted password commands

Example with password manager:

.. code-block:: bash

   # Store password in pass
   pass insert vaultconfig/myapp

   # Use with VaultConfig
   export VAULTCONFIG_PASSWORD_COMMAND="pass show vaultconfig/myapp"
   vaultconfig list ./myapp-config

File Permissions
~~~~~~~~~~~~~~~~

VaultConfig automatically sets secure file permissions (0600 - owner read/write only)
when creating or modifying config files. This prevents other users from reading
sensitive configuration data.

Additional manual steps for directory permissions:

.. code-block:: bash

   # Directory: owner read/write/execute only
   chmod 700 ./myapp-config

   # Files are automatically set to 600 by VaultConfig

On Windows:

.. code-block:: powershell

   # Remove inheritance and set owner-only permissions
   icacls "myapp-config" /inheritance:r /grant:r "$env:USERNAME:(OI)(CI)F"

Security Features:

- Atomic file writes prevent partial/corrupted files
- Secure permissions set from file creation (no race condition)
- Temporary files securely deleted on error
- No exposure window with default permissions

Version Control
~~~~~~~~~~~~~~~

**DO**:

- Add config directories to ``.gitignore``
- Use separate configs for different environments
- Document config structure (without sensitive values)
- Use config file encryption before committing (if necessary)

**DON'T**:

- Commit unencrypted configs with sensitive data
- Commit obscured passwords (not secure!)
- Use weak encryption passwords in version control
- Share decryption passwords via git

Example ``.gitignore``:

.. code-block:: text

   # VaultConfig directories
   .config/
   myapp-config/
   *-config/

   # Except structure documentation
   !config-template/

Environment-Specific Configs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use separate config directories for each environment:

.. code-block:: bash

   ./config/
   ├── development/     # Development configs
   ├── staging/         # Staging configs
   └── production/      # Production configs (encrypted!)

Python example:

.. code-block:: python

   import os
   from pathlib import Path
   from vaultconfig import ConfigManager

   env = os.getenv("APP_ENV", "development")
   config_dir = Path(f"./config/{env}")

   manager = ConfigManager(
       config_dir=config_dir,
       password=os.getenv("VAULTCONFIG_PASSWORD"),
   )

Password Storage Options
------------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Simple but less secure:

.. code-block:: bash

   export VAULTCONFIG_PASSWORD="my-password"

Pros:

- Easy to use
- Works in CI/CD
- No external dependencies

Cons:

- Visible in process list
- May be logged
- Less secure than dedicated tools

Password Command
~~~~~~~~~~~~~~~~

Use a password manager or secret store:

.. code-block:: bash

   # With pass
   export VAULTCONFIG_PASSWORD_COMMAND="pass show vaultconfig/myapp"

   # With macOS Keychain
   export VAULTCONFIG_PASSWORD_COMMAND="security find-generic-password -s vaultconfig -w"

   # With 1Password CLI
   export VAULTCONFIG_PASSWORD_COMMAND="op item get vaultconfig --fields password"

   # With AWS Secrets Manager
   export VAULTCONFIG_PASSWORD_COMMAND="aws secretsmanager get-secret-value --secret-id vaultconfig --query SecretString --output text"

Pros:

- More secure
- Centralized password management
- Audit trails
- MFA support (some managers)

Cons:

- Requires external tool
- More complex setup

Interactive Prompt
~~~~~~~~~~~~~~~~~~

Manual entry when needed:

.. code-block:: python

   from vaultconfig import ConfigManager

   # Will prompt if password needed
   manager = ConfigManager(config_dir="./config")

Pros:

- Most secure (password not stored)
- Simple for manual operations

Cons:

- Not suitable for automation
- Requires TTY

Threat Model
------------

What VaultConfig Protects Against
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Password Obscuring**:

- ✓ Shoulder surfing
- ✓ Accidental exposure in logs
- ✓ Casual viewing of config files
- ✓ Accidental commits (minimal protection)

**Config File Encryption**:

- ✓ Unauthorized file access
- ✓ Stolen backups
- ✓ Accidental exposure
- ✓ Insider threats (with strong passwords)
- ✓ File tampering (authenticated encryption)

What VaultConfig Does NOT Protect Against
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ✗ Memory inspection (keys in RAM)
- ✗ Root/admin access to running processes
- ✗ Malware on the system
- ✗ Weak passwords
- ✗ Social engineering
- ✗ Side-channel attacks
- ✗ Quantum computers (future threat)

Attack Scenarios
----------------

Scenario 1: Config File Leaked
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**With Password Obscuring Only**:

Attacker can easily decrypt passwords using VaultConfig source code.

**With Config File Encryption**:

Attacker needs the encryption password. Config is secure unless password is weak.

Scenario 2: Source Code + Config Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**With Password Obscuring Only**:

Complete compromise - attacker has everything needed.

**With Config File Encryption**:

Config is still secure if password is not stored in source code.

Scenario 3: Running Process Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Both Methods**:

Attacker with process access can read decrypted data from memory. Use system-level
protections (user isolation, containers, etc.).

Security Checklist
------------------

For Development
~~~~~~~~~~~~~~~

- [ ] Use password obscuring for convenience
- [ ] Set file permissions (700/600)
- [ ] Add config directories to ``.gitignore``
- [ ] Document config structure
- [ ] Use environment-specific configs

For Production
~~~~~~~~~~~~~~

- [ ] Enable config file encryption
- [ ] Use strong, unique passwords (20+ characters)
- [ ] Store passwords in password manager
- [ ] Use ``VAULTCONFIG_PASSWORD_COMMAND``
- [ ] Set strict file permissions (700/600)
- [ ] Separate configs by environment
- [ ] Regular password rotation
- [ ] Audit access logs
- [ ] Backup encrypted configs
- [ ] Test password recovery process
- [ ] Document security procedures

For CI/CD
~~~~~~~~~

- [ ] Use encrypted configs
- [ ] Store passwords in CI/CD secrets
- [ ] Use ``VAULTCONFIG_PASSWORD`` environment variable
- [ ] Never log decrypted values
- [ ] Clean up after builds
- [ ] Use separate passwords per environment
- [ ] Rotate passwords regularly

Compliance Considerations
-------------------------

GDPR
~~~~

If config files contain personal data:

- Use config file encryption
- Document data retention policies
- Implement access controls
- Enable audit logging
- Provide data export capabilities

HIPAA
~~~~~

If config files contain PHI:

- Use config file encryption (required)
- Strong password requirements
- Access controls and logging
- Regular security assessments
- Encrypted backups

PCI DSS
~~~~~~~

If config files contain payment card data:

- Use config file encryption (required)
- Strong cryptographic controls
- Key management procedures
- Access restrictions
- Regular security testing

Reporting Security Issues
-------------------------

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email security@example.com with details
3. Include steps to reproduce
4. Allow time for a fix before disclosure
5. We'll credit you in the security advisory

Response time: Within 48 hours for critical issues.

Security Updates
----------------

Subscribe to security advisories:

- GitHub Security Advisories
- Mailing list: security-announce@example.com
- RSS feed: https://example.com/security.xml

Always use the latest version for security fixes.

Additional Resources
--------------------

- `OWASP Secure Configuration Guide <https://owasp.org>`_
- `NaCl/libsodium Documentation <https://doc.libsodium.org/>`_
- `Password Manager Resources <https://www.passwordstore.org/>`_
- `NIST Password Guidelines <https://pages.nist.gov/800-63-3/>`_

For questions, see :doc:`examples` or contact support.
