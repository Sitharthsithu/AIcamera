from cryptography.fernet import Fernet
import base64
import os

def encrypt_service_account():
    try:
        # Check for credential file
        credential_file = 'credential.json'
        if not os.path.exists(credential_file):
            print(f"Error: {credential_file} not found!")
            print(f"Current directory: {os.getcwd()}")
            print("Please make sure your credential file exists in this directory.")
            return
            
        # Generate key and initialize Fernet
        key = Fernet.generate_key()
        f = Fernet(key)
        
        # Read and encrypt service account file
        with open(credential_file, 'rb') as file:
            credentials = file.read()
        encrypted_credentials = f.encrypt(credentials)
        
        # Save encrypted credentials
        with open('service-account.encrypted', 'wb') as file:
            file.write(encrypted_credentials)
        
        # Save key
        with open('encryption.key', 'wb') as file:
            file.write(key)
            
        print("Encryption successful!")
        print("Files created: service-account.encrypted and encryption.key")
        print("Please keep encryption.key secure")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    encrypt_service_account()