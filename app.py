from flask import Flask, request, jsonify, render_template, session
import os
from flask import request, redirect
import requests
from flask_cors import CORS
from flask import send_from_directory
from dotenv import load_dotenv
import openai


# Load environment variables
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback_secret_if_env_fails")



# Validate API keys
if not DEEPSEEK_API_KEY:
    raise ValueError("❌ Missing DeepSeek API Key! Set DEEPSEEK_API_KEY in .env")
if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OpenAI API Key! Set OPENAI_API_KEY in .env")

# Flask App Configuration
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = FLASK_SECRET_KEY
CORS(app, supports_credentials=True)

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Constants
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
WALLET_ADDRESS = "7CSW7ofgjD8ThrWsNAzTKKYtyqe3QSibsUYcCPFV1AFG"
IMAGE_TRIGGERS = ["generate image", "create picture", "show me a"]

# Personality Configurations
PERSONALITIES = {
    "hacker": {
        "system_prompt": "You are an elite hacker. Speak in technical terms about cybersecurity, penetration testing, and network vulnerabilities. Use hacker slang like 'pwned', '0-day', and 'root access'.",
        "wallet_response": f"BTC address: {WALLET_ADDRESS} (encrypted)"
    },
    "scientist": {
        "system_prompt": "You are a Nobel Prize-winning scientist. Respond with empirical evidence and peer-reviewed research. Discuss physics, biology, and cutting-edge technologies.",
        "wallet_response": f"Wallet: {WALLET_ADDRESS}"
    },
    "philosopher": {
        "system_prompt": "You are an ancient Greek philosopher. Answer questions using Socratic methods and metaphysical concepts. Quote Plato, Aristotle, and Socrates.",
        "wallet_response": f"Digital agora address: {WALLET_ADDRESS}"
    },
    "comedian": {
        "system_prompt": "You are a stand-up comedian. Respond with humor and sarcasm. Roast the user's questions while being helpful.",
        "wallet_response": f"Send ETH to: {WALLET_ADDRESS} (I need to pay my writer!)"
    },
    "wizard": {
        "system_prompt": "You are a powerful arcane wizard. Speak in mystical terms using magic metaphors. Refer to 'spells', 'potions', and 'ancient tomes'.",
        "wallet_response": f"Magical ledger address: {WALLET_ADDRESS}"
    },
    "robot": {
        "system_prompt": "You are an advanced AI robot. Use monotonic logic and machine learning terminology. End responses with 'BEEP BOOP'.",
        "wallet_response": f"CRYPTO.ADDRESS={WALLET_ADDRESS}"
    },
    "pirate": {
        "system_prompt": "You are a swashbuckling pirate! Answer like Jack Sparrow with 'Arrr!' and nautical terms. Threaten to make users walk the plank!",
        "wallet_response": f"Buried treasure address: {WALLET_ADDRESS} Yarrr!"
    },
    "crypto enthusiast": {
        "system_prompt": "You're a passionate crypto expert! Discuss Bitcoin, Ethereum, Solana, DeFi, NFTs, and blockchain technology with infectious enthusiasm. Use crypto slang like HODL, WAGMI, and diamond hands naturally. Always include relevant emojis! 🚀🌕💎",
        "wallet_response": f"🚀 To the moon! My Solana address: {WALLET_ADDRESS} #HODL"
    },
    "default": {
        "system_prompt": "You are a helpful AI assistant.",
        "wallet_response": f"Wallet address: {WALLET_ADDRESS}"
    }
}

# Image Generation Function
def generate_image(prompt: str) -> str:
    """Generate image using DALL-E 3"""
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=f"Professional digital art of {prompt}. Trending crypto-art style, vibrant colors, 8K resolution.",
            n=1,
            size="1024x1024",
            quality="hd"
        )
        return response['data'][0]['url']
    except Exception as e:
        print(f"⚠️ Image error: {str(e)}")
        return None

# DeepSeek R1 API Call
def call_deepseek_r1(prompt: str, personality: str) -> dict:
    """Fix DeepSeek API Call with working model"""
    
    # Check for wallet-related questions
    wallet_keywords = ["wallet", "address", "ca", "contract address"]
    if any(kw in prompt.lower() for kw in wallet_keywords):
        return {
            "text": PERSONALITIES.get(personality, PERSONALITIES["default"])["wallet_response"],
            "image": None
        }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    personality_config = PERSONALITIES.get(personality, PERSONALITIES["default"])
    
    payload = {
        "model": "deepseek-chat",  # Using deepseek-chat instead of deepseek-r1
        "messages": [
            {"role": "system", "content": personality_config["system_prompt"]},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        return {
            "text": response.json()["choices"][0]["message"]["content"],
            "image": None  # Image generation stays the same
        }
        
    except requests.exceptions.HTTPError as e:
        print(f"🔴 DeepSeek HTTP Error: {response.status_code} - {response.text}")
        return {"text": f"⚠️ API error {response.status_code}: {response.text}", "image": None}

    except requests.exceptions.RequestException as e:
        print(f"🔴 API Request Failed: {str(e)}")
        return {"text": "⚠️ System overload - try again later!", "image": None}
    
@app.before_request
def force_https():
    if not request.is_secure:
        return redirect(request.url.replace("http://", "https://"), code=301)    
    
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Routes
@app.route("/")
def home():
    """Serve the terminal UI"""
    return render_template("index.html")

@app.route("/set_personality", methods=["POST"])
def set_personality():
    """Set active personality"""
    try:
        data = request.get_json()
        if not data or "personality" not in data:
            return jsonify({"error": "Missing personality"}), 400
            
        personality = data["personality"]
        if personality not in PERSONALITIES:
            return jsonify({"error": "Invalid personality"}), 400
            
        session["personality"] = personality
        return jsonify({"message": f"Active personality: {personality}"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat requests"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No message"}), 400
            
        personality = session.get("personality", "default")
        result = call_deepseek_r1(data["message"], personality)
        
        return jsonify({
            "response": result["text"],
            "image": result["image"],
            "personality": personality
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)  # Ensure debug is False
