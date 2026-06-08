from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    """Convert plain text password to secure hash."""
    return pwd_context.hash(plain_password)
 
 
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if plain password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)