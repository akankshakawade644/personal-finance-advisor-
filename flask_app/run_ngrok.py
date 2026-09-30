import os
import sys
from dotenv import load_dotenv

load_dotenv()

def start_ngrok_and_flask():
    port = int(os.getenv('FLASK_PORT', 5000))
    ngrok_token = os.getenv('NGROK_AUTHTOKEN', '')

    try:
        from pyngrok import ngrok, conf
        if ngrok_token:
            ngrok.set_auth_token(ngrok_token)

        # Open a HTTP tunnel on port 5000
        public_url = ngrok.connect(port).public_url
        print("\n" + "=" * 60)
        print(f"🚀 Personal Finance Advisor Bot is publicly accessible at:")
        print(f"   👉 {public_url}")
        print("=" * 60 + "\n")
    except ImportError:
        print("pyngrok not installed. Run: pip install pyngrok")
    except Exception as e:
        print(f"Ngrok connection note: {e}")
        print("Continuing with standard localhost execution...\n")

    # Start Flask application
    from app import app, db
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    start_ngrok_and_flask()
