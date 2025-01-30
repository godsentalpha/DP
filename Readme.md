# 🚀 DEEP-PERSONA AI TERMINAL

### **🔮 AI-Powered Chatbot with DeepSeekR1 & OpenAI API**
An **interactive AI Terminal** powered by **DeepSeekR1** and **OpenAI API**, offering different **personalities** such as **hacker, scientist, philosopher, and more**. It also integrates **image generation**, **crypto price fetching**, and **wallet lookups**.

---

## **📌 Features**
✅ **AI Personalities** (Hacker, Scientist, Philosopher, etc.)  
✅ **DeepSeekR1 Integration** (Upgradable to DeepSeek's latest models)  
✅ **Crypto Price Fetching** (Live prices from CoinGecko API)  
✅ **Blockchain Wallet Queries** (Responds with wallet information)  
✅ **Image Generation** (AI-generated images with style-based rendering)  
✅ **Secure API Handling** (Environment variables for security)  

---

## **🛠 Installation Guide**

### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/your-repo-name.git
cd your-repo-name
```

### **2️⃣ Create a Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4️⃣ Create `.env` File**
Create a `.env` file in the root directory and add:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key
FLASK_SECRET_KEY=your_flask_secret_key
```

---

## **🚀 Running the Project**
Once the setup is complete, start the Flask server:
```bash
python app.py
```
Your AI Terminal will be available at **`http://127.0.0.1:5001`**. 🎉

---

## **🌍 Deploying to Render**
1️⃣ **Create a New Web Service** on [Render](https://render.com/)  
2️⃣ **Connect your GitHub Repo** and select the branch  
3️⃣ **Set Environment Variables** (`DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `FLASK_SECRET_KEY`)  
4️⃣ **Select `Python 3.9+` and use this start command:**
```bash
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```
5️⃣ **Deploy!** 🎉 Your Flask app is now live!

---

## **🔧 API Endpoints**

### **1️⃣ Root Endpoint**
- **`GET /`** → Serves the main terminal UI  

### **2️⃣ Chat with AI**
- **`POST /chat`**  
  ```json
  {
    "message": "Hello AI!"
  }
  ```
  📌 **Response** (Example)
  ```json
  {
    "response": "Hello, how can I assist you today?",
    "image": null
  }
  ```

### **3️⃣ Set AI Personality**
- **`POST /set_personality`**  
  ```json
  {
    "personality": "hacker"
  }
  ```
  📌 **Response**
  ```json
  {
    "message": "Active personality: hacker"
  }
  ```

### **4️⃣ Generate Image**
- **`GET /test_image`**  
  📌 Returns test AI-generated images  

### **5️⃣ Fetch Crypto Prices**
- **`GET /test_prices`**  
  📌 Fetches real-time crypto prices from **CoinGecko API**  

---

## **📜 Technologies Used**
🔹 **Flask** (Backend API)  
🔹 **DeepSeekR1 API** (AI Model)  
🔹 **OpenAI API** (Chat & Image Generation)  
🔹 **CoinGecko API** (Crypto Prices)  
🔹 **PIL (Pillow)** (Image Processing)  
🔹 **Gunicorn** (Production Server)  

---

## **🌍 Live Demo**
🚀 **Hosted on Render:** [🔗 deep-persona.godsent.cx](https://deep-persona.godsent.cx/)  

---

## **📜 License**
This project is licensed under the **MIT License**.  

📌 **Fork, Contribute, and Improve!** 🙌  
📌 Star ⭐ the repo if you find it useful!  

---

### **🎯 Developed by [@GODSENTALPHA](https://github.com/godsentalpha)**
🔥 **Join us for AI, Crypto, and Innovation!** 🔥

