from cryptography.fernet import Fernet
import base64

# Generate a key (Run this once and keep the key safe)
def generate_key():
    return Fernet.generate_key()

# Save the key in a file
def save_key():
    key = generate_key()
    with open('secret.key', 'wb') as key_file:
        key_file.write(key)

# Load the key from the file
def load_key():
    return open('secret.key', 'rb').read()

def encrypt_data(data):
    key = open('secret.key', 'rb').read()
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())  # Encrypt the data as bytes
    return base64.b64encode(encrypted_data).decode('utf-8')  # Convert bytes to base64 string

# Decrypt data
def decrypt_data(encrypted_data):
    key = load_key()
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data).decode()
    return decrypted_data
