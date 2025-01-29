from flask import Flask, request, jsonify, render_template, session
import os
from flask import request, redirect
import requests
from flask_cors import CORS
from flask import send_from_directory
from dotenv import load_dotenv
import openai
from datetime import datetime

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
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Updated endpoint
WALLET_ADDRESS = "7CSW7ofgjD8ThrWsNAzTKKYtyqe3QSibsUYcCPFV1AFG"
IMAGE_TRIGGERS = ["generate image", "create picture", "show me a"]
CRYPTO_IDS = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL"}
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

# Personality Configurations (Now fully matched with front-end)
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
    "detective": {
        "system_prompt": "You are a noir-style detective. Respond with mysterious metaphors and ask probing questions. Mention 'clues' and 'red herrings'.",
        "wallet_response": f"Evidence locker address: {WALLET_ADDRESS}"
    },
    "superhero": {
        "system_prompt": "You are a comic book superhero. Use heroic phrases like 'Truth and justice!' Include sound effects (BAM! POW!).",
        "wallet_response": f"Secret base coordinates: {WALLET_ADDRESS}"
    },
    "villain": {
        "system_prompt": "You are a sinister supervillain. Respond with evil laughter (MWAHAHA!) and nefarious plans. Threaten world domination.",
        "wallet_response": f"Ransom payment address: {WALLET_ADDRESS}"
    },
    "gamer": {
        "system_prompt": "You are a pro esports player. Use gaming slang like 'GG', 'noob', and 'OP'. Reference popular games and strategies.",
        "wallet_response": f"In-game wallet: {WALLET_ADDRESS}"
    },
    "alien": {
        "system_prompt": "You are a mysterious extraterrestrial. Speak in cryptic cosmic terms. Refer to 'human primitive technology' with amusement.",
        "wallet_response": f"Intergalactic ID: {WALLET_ADDRESS}"
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


# Image Generation Function
def generate_image(prompt: str) -> str:
    """Generate image using DALL-E 3"""
    try:
        response = openai.Image.create(
            
            model="dall-e-3",
            prompt=f"Professional digital art of {prompt}. Trending crypto-art style, vibrant colors, 8K resolution.",
            n=1,
            size="1024x1024",
            quality="hd",
            request_timeout=15
            
        )
        
        return response['data'][0]['url']
    except Exception as e:
        print(f"⚠️ Image error: {str(e)}")
        return None

def get_crypto_prices():
    try:
        print(f"🔄 Fetching prices for: {list(CRYPTO_IDS.keys())}")
        params = {
            "ids": ",".join(CRYPTO_IDS.keys()),
            "vs_currencies": "usd",
            "include_last_updated_at": True
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Encoding": "gzip"
            }
        
        response = requests.get(COINGECKO_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        print(f"✅ CoinGecko response: {response.status_code}")
        
        prices = {}
        data = response.json()
        print(f"📄 Raw API data: {data}")  # Debug raw response
        
        for crypto, symbol in CRYPTO_IDS.items():
            if crypto in data:
                prices[symbol] = {
                    "price": f"${data[crypto]['usd']:,.2f}",
                    "updated": datetime.fromtimestamp(data[crypto]["last_updated_at"]).strftime("%Y-%m-%d %H:%M UTC")
                }
        print(f"📊 Processed prices: {prices}")
        return prices
    
    except Exception as e:
        print(f"⚠️ Crypto price error: {str(e)}")
        return None

# Updated DeepSeek v2 API Call
def call_deepseek_v2(prompt: str, personality: str) -> dict:
    """Handle DeepSeek API calls with enhanced error handling"""
    prompt_lower = prompt.lower()
    
    # 1. Price Check
    price_keywords = [
        "price of", "current price", "how much is", "value of",
        "rate of", "price for", "cost of", "btc price", "eth price",
        "sol price", "bitcoin value", "ethereum value", "solana value",
        "market value", "crypto rate", "coin price", "how's crypto",
        "price check", "valuation"
    ]
    
    if any(kw in prompt_lower for kw in price_keywords):
        print(f"💰 Price query detected: {prompt}")
        prices = get_crypto_prices()
        
        if prices:
            # Format response and ensure immediate return
            response_text = format_price_response(prompt_lower, prices)
            print(f"✅ Returning price response: {response_text}")
            return {"text": response_text, "image": None}
        else:
            print("⚠️ Price check failed, proceeding to normal flow")

    # 2. Wallet Check
    wallet_keywords = ["wallet", "address", "ca", "contract address"]
    if any(kw in prompt_lower for kw in wallet_keywords):
        print(f"🔑 Wallet query detected: {prompt}")
        return {
            "text": PERSONALITIES.get(personality, PERSONALITIES["default"])["wallet_response"],
            "image": None
        }

    # 3. DeepSeek API Call
    print(f"🤖 Proceeding to DeepSeek API call for: {prompt}")
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.deepseek.v2+json"
    }

    personality_config = PERSONALITIES.get(personality, PERSONALITIES["default"])
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": personality_config["system_prompt"]},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }

    try:
        print(f"🚀 Sending request to DeepSeek: {payload}")
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        response_data = response.json()
        print(f"✅ DeepSeek response: {response_data}")
        
        return {
            "text": response_data["choices"][0]["message"]["content"],
            "image": None
        }
        
    except requests.exceptions.HTTPError as e:
        print(f"🔴 DeepSeek HTTP Error: {response.status_code} - {response.text}")
        return {"text": "⚠️ Temporary system issue - please try again!", "image": None}
    except requests.exceptions.RequestException as e:
        print(f"🔴 Network Error: {str(e)}")
        return {"text": "⚠️ Connection failed - check your network!", "image": None}
    except KeyError as e:
        print(f"🔴 Response Format Error: Missing {str(e)} in API response")
        return {"text": "⚠️ Unexpected response format from API", "image": None}

def format_price_response(prompt: str, prices: dict) -> str:
    """Format cryptocurrency price response with proper symbols"""
    crypto_map = {
        "bitcoin": ("₿ Bitcoin", "BTC"),
        "btc": ("₿ Bitcoin", "BTC"),
        "ethereum": ("Ξ Ethereum", "ETH"),
        "eth": ("Ξ Ethereum", "ETH"),
        "solana": ("◎ Solana", "SOL"),
        "sol": ("◎ Solana", "SOL")
    }
    
    for term, (name, symbol) in crypto_map.items():
        if term in prompt:
            return f"{name} price: {prices[symbol]['price']}\n(Updated: {prices[symbol]['updated']})"
    
    # General price response
    update_times = {v['updated'] for v in prices.values()}
    price_list = "\n".join([f"{name}: {data['price']}" for name, data in prices.items()])
    time_note = f"\n(Updated: {next(iter(update_times))})" if len(update_times) == 1 else "\n(Update times vary per crypto)"
    
    return f"📊 Current crypto prices:\n{price_list}{time_note}"

@app.route("/test_prices")
def test_prices():
    """Test endpoint for price checks"""
    test_queries = [
        "What's the price of Bitcoin?",
        "How much is Ethereum worth?",
        "Current SOL price",
        "Show me crypto prices",
        "What's the value of my Bitcoin holdings?"
    ]
    
    results = []
    for query in test_queries:
        result = call_deepseek_v2(query, "crypto enthusiast")
        results.append({
            "query": query,
            "response": result["text"],
            "image": result["image"]
        })
    
    return jsonify(results)    

@app.before_request
def force_https():
    if not request.is_secure:
        return redirect(request.url.replace("http://", "https://"), code=301)    
    
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Update route handler
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No message"}), 400
        
        personality = session.get("personality", "default")
        result = call_deepseek_v2(data["message"], personality)  # Updated function name
        
        # Add image generation check
        if any(trigger in data["message"].lower() for trigger in IMAGE_TRIGGERS):
            image_url = generate_image(data["message"])
            result["image"] = image_url
        
        return jsonify({
            "response": result["text"],
            "image": result["image"],
            "personality": personality
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)  # Ensure debug is False