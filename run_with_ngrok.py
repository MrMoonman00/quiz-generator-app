import os
import sys
import subprocess
import time
import json
import requests
from dotenv import load_dotenv
from flask import Flask

# Load environment variables
load_dotenv()

# Set the path to ngrok
def get_ngrok_path():
    """Get the path to ngrok executable"""
    # Check if ngrok is in system PATH (installed via Homebrew)
    try:
        result = subprocess.run(['which', 'ngrok'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    # Check Downloads folder
    downloads_path = os.path.expanduser("~/Downloads/ngrok")
    if os.path.exists(downloads_path):
        return downloads_path
    
    return None

NGROK_PATH = get_ngrok_path()
NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN')

def check_ngrok():
    """Check if ngrok is installed"""
    try:
        subprocess.run([NGROK_PATH, '--version'], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def configure_ngrok():
    """Configure ngrok with auth token"""
    try:
        subprocess.run([NGROK_PATH, 'config', 'add-authtoken', NGROK_AUTH_TOKEN], 
                      capture_output=True)
        return True
    except Exception as e:
        print(f"Error configuring ngrok: {str(e)}")
        return False

def get_ngrok_url():
    """Get the public URL from ngrok"""
    try:
        # Get the tunnel information from ngrok's API
        response = requests.get('http://localhost:4040/api/tunnels')
        tunnels = response.json()['tunnels']
        
        # Look for the tunnel that matches our port
        for tunnel in tunnels:
            if 'localhost:5004' in tunnel['config']['addr']:
                return tunnel['public_url']
                
        print("No tunnel found for port 5004")
        return None
        
    except Exception as e:
        print(f"Error getting ngrok URL: {str(e)}")
        return None

def update_base_url(url):
    """Update the base URL in the Flask app configuration"""
    try:
        print(f"Updated base URL to: {url}")
        from app import app
        app.config['BASE_URL'] = url
        os.environ['BASE_URL'] = url  # Also set in environment for access in templates
    except Exception as e:
        print(f"Error updating base URL: {str(e)}")

def main():
    """Main function to run the Flask app with ngrok"""
    try:
        # Configure ngrok
        print("Configuring ngrok with auth token...")
        NGROK_PATH = os.path.expanduser('~/Downloads/ngrok')
        if not os.path.exists(NGROK_PATH):
            print(f"ngrok not found at {NGROK_PATH}")
            sys.exit(1)
            
        # Get ngrok auth token from environment
        NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN')
        if not NGROK_AUTH_TOKEN:
            print("NGROK_AUTH_TOKEN not found in environment variables")
            sys.exit(1)
            
        # Kill any existing ngrok processes
        try:
            subprocess.run(['pkill', '-f', 'ngrok'], 
                         check=False, capture_output=True)
            time.sleep(1)  # Wait for process to be killed
        except Exception:
            pass  # Ignore if no process exists
            
        # Start ngrok in a separate process with simpler configuration
        print("Starting ngrok tunnel...")
        ngrok_process = subprocess.Popen(
            [NGROK_PATH, 'http', '5004', '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for ngrok to start
        time.sleep(5)  # Increased wait time to ensure ngrok is ready
        
        # Get the public URL
        public_url = None
        retries = 5
        while retries > 0 and not public_url:
            try:
                response = requests.get('http://localhost:4040/api/tunnels')
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    if tunnels:
                        public_url = tunnels[0]['public_url']
                        break
            except Exception as e:
                print(f"Error getting ngrok URL (retries left: {retries}): {str(e)}")
            time.sleep(2)
            retries -= 1
        
        if not public_url:
            print("Failed to get ngrok URL")
            ngrok_process.terminate()
            sys.exit(1)

        # Update the base URL in the Flask app
        update_base_url(public_url)
        
        print("\nStarted Flask server...")
        print("Started ngrok tunnel...")
        print(f"\nYour quiz generator is now accessible at: {public_url}")
        
        # Start Flask app
        from app import app
        app.run(debug=True, port=5004)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
