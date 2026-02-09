from django.contrib.auth.hashers import BCryptSHA256PasswordHasher
from django.conf import settings

class PepperedBCryptSHA256PasswordHasher(BCryptSHA256PasswordHasher):
    """
    BCryptSHA256PasswordHasher with a global 'pepper' from settings.
    (This is essentially the default BCryptSHA256PasswordHasher behavior
    in Django, but explicitly shows the intent).
    """
    algorithm = "bcrypt_sha256_with_pepper" 

    def get_pepper(self):
        return settings.SECRET_KEY