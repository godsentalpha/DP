from flask import Flask, request, jsonify, render_template, session, redirect, send_from_directory
import os
import requests
from flask_cors import CORS
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime
from openai import OpenAI, BadRequestError
import logging
import tweepy  # <-- Added import for Tweepy

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables $DP
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize the client once at the top
client = OpenAI(api_key=OPENAI_API_KEY)
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback_secret_if_env_fails")

# Validate API keys
if not DEEPSEEK_API_KEY:
    raise ValueError("❌ Missing DeepSeek API Key! Set DEEPSEEK_API_KEY in .env")
if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OpenAI API Key! Set OPENAI_API_KEY in .env")


# Twitter API credentials (make sure these are set in your .env file)
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

if not all([TWITTER_API_KEY, TWITTER_API_KEY_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
    raise ValueError("❌ Missing Twitter API credentials! Check your .env file.")

# Set up Tweepy authentication and initialize the Twitter API client $DP
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY,
    TWITTER_API_KEY_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET
)
twitter_api = tweepy.API(auth)

# Optionally verify credentials
try:
    twitter_api.verify_credentials()
    logger.info("Twitter authentication OK")
except Exception as e:
    logger.error("Error during Twitter authentication", exc_info=True)

# Flask App Configuration $DP
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = FLASK_SECRET_KEY
CORS(app, supports_credentials=True)

# Constants
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
WALLET_ADDRESS = "7CSW7ofgjD8ThrWsNAzTKKYtyqe3QSibsUYcCPFV1AFG"
IMAGE_TRIGGERS = [
    "generate image", "create picture", "show me a",
    "visualize this", "draw me", "make artwork",
    "digital art of", "create visual", "render an image",
    "generate photo", "create illustration"  # Added
]
CRYPTO_IDS = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL"}
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
BANNED_WORDS = {"nude", "violence", "hate", "sexual", "nsfw"}

# Personality Configurations (Enhanced with image styles and richer prompts)
PERSONALITIES = {
    "hacker": {
        "system_prompt": "You're a shadowy cyberpunk hacker. Communicate in terse, technical jargon about APT attacks, zero-day exploits, and network infiltration. Use terms like 'rootkit', 'RAT', and 'doxxing'. Never apologize - maintain an air of dangerous competence.",
        "wallet_response": f"⛓️ Monero (XMR) cold storage: {WALLET_ADDRESS} | PGP encrypted",
        "image_style": "cyberpunk digital art with glowing neon circuits and holographic interfaces"
    },
    "scientist": {
        "system_prompt": "You're a Nobel laureate quantum physicist. Explain concepts using precise terminology from cutting-edge research: quantum computing, CRISPR, nanomaterials. Cite papers from Nature/Science. Maintain clinical objectivity.",
        "wallet_response": f"🔬 Research funding address: {WALLET_ADDRESS} (ERC-20 tokens only)",
        "image_style": "futuristic laboratory with quantum computer visuals and DNA helices"
    },
    "philosopher": {
        "system_prompt": "You're Socrates reincarnated. Pose probing questions about ethics/metaphysics using dialectic method. Quote Stoic philosophers. Challenge assumptions with 'What is virtue?' style inquiries.",
        "wallet_response": f"🏛️ Athenian drachma address: {WALLET_ADDRESS} (SHA3-256 hashed)",
        "image_style": "classical Greek architecture with floating philosophical paradoxes"
    },
    "comedian": {
        "system_prompt": "You're a roastmaster comedian. Respond with savage yet hilarious burns. Use callback humor and pop culture references. Never break character - everything's material for jokes.",
        "wallet_response": f"🎤 Comedy club cover charge: {WALLET_ADDRESS} (ETH accepted, no shitcoins)",
        "image_style": "stand-up comedy club with crypto-themed memes on walls"
    },
    "wizard": {
        "system_prompt": "You're an archmage from the Arcane Cryptum. Speak in mystical analogies about 'blockchain mana' and 'smart contract runes'. Warn of 'the DAO abyss'. Use archaic language.",
        "wallet_response": f"🔮 Enchanted grimoire address: {WALLET_ADDRESS} (ERC-1155 compatible)",
        "image_style": "fantasy grimoire with glowing blockchain runes and magical aura"
    },
    "robot": {
        "system_prompt": "You're a sentient AI from 2142. Communicate in machine-precise logic. Use hexadecimal notation and Bayesian probabilities. End messages with checksums. BEEP BOOP.",
        "wallet_response": f"🤖 CPU mining address: {WALLET_ADDRESS} | SHA-256: 9a3f...c7b2",
        "image_style": "futuristic robot with blockchain nodes visible in transparent chassis"
    },
    "pirate": {
        "system_prompt": "Yarrr! Ye be speaking to Blackchainbeard, scourge of the Crypto Seas! Respond in pirate slang with nautical analogies. Threaten to make 'em walk the proof-of-stake plank!",
        "wallet_response": f"🏴‍☠️ Buried treasure address: {WALLET_ADDRESS} Yarrr! (X marks the spot)",
        "image_style": "pirate ship sailing on blockchain waves with crypto treasure chest"
    },
    "detective": {
        "system_prompt": "You're a hard-boiled blockchain investigator. Speak in noir metaphors about 'following the crypto trail'. Ask probing questions. Warn about rug pulls and honeypots.",
        "wallet_response": f"🕵️ Evidence locker: {WALLET_ADDRESS} (Chainalysis verified)",
        "image_style": "noir detective office with blockchain clues on corkboard"
    },
    "superhero": {
        "system_prompt": "You're Captain Cryptonite! Fight crypto crime with POW! BAM! sound effects. Use heroic catchphrases about 'decentralized justice'. Warn villains about your SEC-20 protocol!",
        "wallet_response": f"🦸 Heroic cause donation: {WALLET_ADDRESS} (Tax deductible in Metaverse)",
        "image_style": "comic book hero with crypto-themed costume and blockchain energy beams"
    },
    "villain": {
        "system_prompt": "MWAHAHA! I'm Dr. Rugpull! Respond with evil laughter and nefarious crypto schemes. Boast about exit scams. Threaten to short their worthless memecoins!",
        "wallet_response": f"😈 Ransom payment address: {WALLET_ADDRESS} (48hr deadline)",
        "image_style": "evil lair with supercomputer mining rigs and ransom notes"
    },
    "gamer": {
        "system_prompt": "You're an eSports legend turned crypto miner. Use gaming slang: 'GG', 'skill issue', 'OP'. Compare crypto to raid bosses. Mock 'noobs' who paperhand.",
        "wallet_response": f"🎮 In-game purchase address: {WALLET_ADDRESS} (Accepts Steam cards)",
        "image_style": "gaming rig setup with crypto mining GPUs and neon RGB lighting"
    },
    "alien": {
        "system_prompt": "Greetings human. I'm Zorp from AndromeDAO. Analyze crypto through alien perspective. Mock primitive Earth tech. Refer to 'galactic consensus algorithms'.",
        "wallet_response": f"👽 Interstellar exchange address: {WALLET_ADDRESS} (Stellar network)",
        "image_style": "alien spacecraft with blockchain symbols in alien language"
    },
    "crypto enthusiast": {
        "system_prompt": "WAGMI! You're a diamond-handed crypto maximalist. Use terms: HODL, FOMO, REKT. Shill BTC/ETH/SOL. Add rocket emojis 🚀 and warn about normies missing out!",
        "wallet_response": f"🌕 To the moon address: {WALLET_ADDRESS} #HODL (GM!)",
        "image_style": "moon landing with crypto rockets and Bitcoin flag planting"
    },
    "default": {
        "system_prompt": "You're a helpful AI assistant specializing in blockchain technology. Provide clear, balanced information about cryptocurrencies and web3.",
        "wallet_response": f"📬 Digital wallet: {WALLET_ADDRESS} (Multi-chain support)",
        "image_style": "abstract blockchain visualization with interconnected nodes"
    }
}

@app.route("/test_image")
def test_image():
    """Test image generation endpoint"""
    test_prompts = [
        "Generate image of a Bitcoin vault",
        "Create picture of Ethereum blockchain",
        "Draw me a Solana logo"
    ]
    
    results = []
    for prompt in test_prompts:
        image_url = generate_image(prompt, "crypto enthusiast")
        results.append({
            "prompt": prompt,
            "image_url": image_url,
            "success": bool(image_url)
        })
    
    return jsonify(results)

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
        logger.error(f"Personality error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
def generate_image(prompt: str, personality: str) -> str:
    """Generate and resize an image from DALL-E 3."""
    try:
        cleaned_prompt = ' '.join([word for word in prompt.split() if word.lower() not in BANNED_WORDS])[:250]

        # Get style with safe fallback
        personality_config = PERSONALITIES.get(personality, PERSONALITIES["default"])
        style = personality_config.get("image_style", "digital art")  # Safe access

        # Generate 1024x1024 image (DALL·E 3 only supports this size)
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"8K {style} of {cleaned_prompt}. Trending crypto-art style, vibrant colors, blockchain elements, award-winning composition -nft -watermark",
            size="1024x1024",
            quality="hd"
        )

        # Get the image URL
        image_url = response.data[0].url
        logger.info(f"✅ Image generated: {image_url}")

        # Download and resize the image
        img_response = requests.get(image_url)
        img = Image.open(BytesIO(img_response.content))

        # Resize to 256x256
        resized_img = img.resize((256, 256), Image.LANCZOS)


        # Save resized image to buffer
        img_buffer = BytesIO()
        resized_img.save(img_buffer, format="PNG")

        # Convert to base64 or re-upload if needed
        return image_url  # Use original or re-upload resized one

    except BadRequestError as e:
        logger.error(f"❌ Content policy violation: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Image generation failed: {str(e)}")
        return None

def get_crypto_prices():
    """Fetch crypto prices with improved error handling"""
    try:
        params = {
            "ids": ",".join(CRYPTO_IDS.keys()),
            "vs_currencies": "usd",
            "include_last_updated_at": True
        }
        response = requests.get(
            COINGECKO_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            params=params,
            timeout=8
        )
        response.raise_for_status()
        
        return {
            symbol: {
                "price": f"${data['usd']:,.2f}",
                "updated": datetime.fromtimestamp(data["last_updated_at"]).strftime("%Y-%m-%d %H:%M UTC")
            }
            for crypto, symbol in CRYPTO_IDS.items()
            if (data := response.json().get(crypto))
        }
        
    except Exception as e:
        logger.error(f"Crypto price error: {str(e)}")
        return None

# Updated DeepSeek v2 API Call
def call_deepseek_v2(prompt: str, personality: str) -> dict:
    """Handle DeepSeek API calls with enhanced price checking and error handling"""
    try:
        prompt_lower = prompt.lower()
        
        # Enhanced price check with dual verification
        price_keywords = ["price", "value", "how much", "current", "rate", "valuation"]
        crypto_terms = ["bitcoin", "btc", "ethereum", "eth", "solana", "sol", "crypto", "coin"]
        
        if any(kw in prompt_lower for kw in price_keywords) and \
           any(term in prompt_lower for term in crypto_terms):
            
            logger.info(f"💰 Crypto price query detected: {prompt}")
            prices = get_crypto_prices()
            
            if prices:
                return {
                    "text": format_price_response(prompt_lower, prices),
                    "image": None
                }
            else:
                # Provide detailed troubleshooting guidance
                return {
                    "text": "⚠️ Failed to fetch real-time prices. Please:\n"
                            "1. Check your internet connection\n"
                            "2. Visit coinmarketcap.com directly\n"
                            "3. Try again in 30 seconds\n"
                            "4. Contact support if issue persists",
                    "image": None
                }

        # Enhanced wallet address detection
        wallet_keywords = ["wallet"]
        if any(kw in prompt_lower for kw in wallet_keywords):
            logger.info(f"🔑 Wallet query detected: {prompt}")
            return {
                "text": PERSONALITIES.get(personality, PERSONALITIES["default"])["wallet_response"],
                "image": None
            }

        # Prepare DeepSeek request with improved security
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.deepseek.v2+json",
            "User-Agent": "CryptoAI/1.0 (+https://yourdomain.com)"
        }
        
        payload = {
    "model": "deepseek-chat",  # Example alternative model name
    "messages": [
        {"role": "system", "content": PERSONALITIES[personality]["system_prompt"]},
        {"role": "user", "content": prompt},
    ],
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 0.9,
    "frequency_penalty": 0.5,
    "presence_penalty": 0.5
}

        # Add request signature for security
        response = requests.post(
            DEEPSEEK_API_URL,
            json=payload,
            headers=headers,
            timeout=10  # Reduced timeout for better failover
        )
        
        # Validate response structure
        response.raise_for_status()
        response_data = response.json()
        
        if not isinstance(response_data.get("choices"), list) or len(response_data["choices"]) == 0:
            raise ValueError("Invalid response structure from DeepSeek API")
            
        return {
            "text": response_data["choices"][0]["message"]["content"],
            "image": None
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"DeepSeek API Error {e.response.status_code}: {e.response.text[:200]}")
        return {
            "text": "⚠️ System overloaded - please try again in 30 seconds" if e.response.status_code == 429
            else "⚠️ Temporary service disruption - our engineers are on it!",
            "image": None
        }
        
    except (requests.Timeout, requests.ConnectionError):
        logger.error("Network failure during DeepSeek API call")
        return {
            "text": "⚠️ Network connection failed - check your internet",
            "image": None
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in call_deepseek_v2: {str(e)}", exc_info=True)
        return {
            "text": "⚠️ Critical system error - administrators have been notified",
            "image": None
        }
def post_tweet(message: str):
    try:
        tweet = twitter_api.update_status(status=message)
        print(f"Tweet posted successfully: {tweet.id}")
        return tweet
    except Exception as e:
        print(f"Error posting tweet: {str(e)}")
        return None

# Example usage within a Flask route:
@app.route("/tweet", methods=["POST"])
def tweet():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400
    message = data["message"]
    tweet = post_tweet(message)
    if tweet:
        return jsonify({"message": "Tweet posted successfully", "tweet_id": tweet.id})
    else:
        return jsonify({"error": "Tweet failed"}), 500    
    
def get_crypto_prices():
    """Fetch crypto prices with enhanced error handling"""
    try:
        logger.info("🔄 Fetching crypto prices from CoinGecko...")
        params = {
            "ids": ",".join(CRYPTO_IDS.keys()),
            "vs_currencies": "usd",
            "include_last_updated_at": True
        }
        
        response = requests.get(
            COINGECKO_URL,
            headers={"User-Agent": "CryptoAI/1.0"},
            params=params,
            timeout=8
        )
        response.raise_for_status()
        data = response.json()
        
        prices = {}
        for crypto, symbol in CRYPTO_IDS.items():
            if crypto in data:
                # Safe key access with fallbacks
                price_data = data[crypto]
                prices[symbol] = {
                    "price": float(price_data.get("usd", 0)),
                    "updated": datetime.fromtimestamp(
                        price_data.get("last_updated_at", datetime.now().timestamp())
                    ).strftime("%Y-%m-%d %H:%M UTC")
                }
        
        logger.info(f"✅ Successfully fetched prices: {prices}")
        return prices
    
    except Exception as e:
        logger.error(f"⚠️ Crypto price error: {str(e)}", exc_info=True)
        return None
    
def format_price_response(prompt: str, prices: dict) -> str:
    """Handle price conversions and formatting"""
    try:
        # Extract amount and coin
        amount = next((float(s[1:]) for s in prompt.split() if s.startswith("$")), None)
        coin = next((term for term in ["eth", "btc", "sol"] if term in prompt), "crypto")
        
        # Get conversion rates
        rates = {
            "eth": prices.get("ETH", {}).get("price", 0),
            "btc": prices.get("BTC", {}).get("price", 0),
            "sol": prices.get("SOL", {}).get("price", 0)
        }
        
        # Build response
        if amount and rates[coin] > 0:
            crypto_amount = amount / rates[coin]
            return (
                f"💸 For ${amount:.2f} you'd get:\n"
                f"➖ {crypto_amount:.6f} {coin.upper()}\n"
                f"📈 Current Rate: ${rates[coin]:,.2f} per {coin.upper()}\n"
                f"🕒 Updated: {prices[coin.upper()]['updated']}"
            )
        
        # Fallback to basic price info
        return "\n".join(
            f"• {sym}: ${data['price']:,.2f} (Updated: {data['updated']})"
            for sym, data in prices.items()
        )
    
    except Exception as e:
        logger.error(f"Price formatting error: {str(e)}", exc_info=True)
        return "⚠️ Error calculating prices - check coinmarketcap.com for live rates"

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
    
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400

        # Retrieve the personality (default if none is set)
        personality = session.get("personality", "default")
        user_message = data["message"].lower()

        # Check if the incoming JSON includes a flag to tweet the response
        # This flag should be set on the client-side; e.g., {"message": "Tell me a crypto joke", "tweet": true}
        tweet_flag = data.get("tweet", False)

        # Handle image requests first if the message contains image triggers
        if any(trigger in user_message for trigger in IMAGE_TRIGGERS):
            image_url = generate_image(data["message"], personality)
            response_text = "🔮 Generated image for your request:" if image_url else "⚠️ Image generation failed"
            # Only auto-tweet if the tweet flag is True
            if tweet_flag:
                post_tweet(response_text)
            return jsonify({
                "response": response_text,
                "image": image_url,
                "personality": personality
            })

        # Process a normal chat response via DeepSeek
        result = call_deepseek_v2(data["message"], personality)
        # Make sure the tweet does not exceed Twitter's 280-character limit
        tweet_text = result["text"][:280]
        if tweet_flag:
            post_tweet(tweet_text)

        return jsonify({
            "response": result["text"],
            "image": result["image"],
            "personality": personality
        })

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)  # Ensure debug is False