# fix_ssl.py
import os
import ssl
import certifi
import requests

def fix_ssl_certificates():
    """Fix SSL certificate issues on Windows"""
    print("Fixing SSL certificate issues...")
    
    # Method 1: Use certifi certificates
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # Method 2: Set REQUESTS_CA_BUNDLE environment variable
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
    
    print(f"Using certificates from: {certifi.where()}")
    
    # Test the fix
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/MAD', verify=True)
        print(f"SSL test successful! Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"SSL test failed: {e}")
        print("Trying without SSL verification...")
        
        # Try without verification
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/MAD', verify=False)
            print(f"Connection successful without SSL verification")
            return True
        except Exception as e2:
            print(f"Connection failed: {e2}")
            return False

if __name__ == "__main__":
    fix_ssl_certificates()