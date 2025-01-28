import { useState, useEffect } from "react";

export default function Terminal() {
  const [personality, setPersonality] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const API_URL = "YOUR-API-URL"; // Ensure this matches your backend

  const PERSONALITIES = [
    "hacker", "scientist", "philosopher", "comedian", "wizard", "robot",
    "pirate", "detective", "superhero", "villain", "crypto enthusiast"
];

  useEffect(() => {
    // Blinking cursor effect
    const cursorInterval = setInterval(() => {
      const cursor = document.querySelector('.cursor');
      if (cursor) {
        cursor.style.visibility = (cursor.style.visibility === 'hidden' ? 'visible' : 'hidden');
      }
    }, 500);
    return () => clearInterval(cursorInterval);
  }, []);

  const handlePersonalitySelect = async (p) => {
    setPersonality(p);
    setMessages([{ user: "SYSTEM", dp: `🎭 Personality set to ${p.toUpperCase()}! Start chatting.` }]);

    await fetch(`${API_URL}/set_personality`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ personality: p }),
    });
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);

    setMessages([...messages, { user: input, dp: "⏳ Thinking..." }]);

    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ message: input }),
    });

    const data = await res.json();
    setMessages((prev) => [...prev.slice(0, -1), { user: input, dp: data.response }]);
    setInput("");
    setLoading(false);
  };

  return (
    <div className="terminal">
      {!personality ? (
        <div className="personality-selection">
          <h2>Select a Personality</h2>
          <select onChange={(e) => handlePersonalitySelect(e.target.value)}>
            <option value="">Choose One</option>
            {personalities.map((p) => (
              <option key={p} value={p}>{p.toUpperCase()}</option>
            ))}
          </select>
        </div>
      ) : (
        <div className="chat-box">
          {messages.map((m, i) => (
            <p key={i}>
              <span className="user">User:</span> {m.user}
              <br />
              <span className="dp">$DP:</span> {m.dp}
            </p>
          ))}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Type your message..."
          />
          {loading && <p className="loading">Thinking...</p>}
          <span className="cursor">█</span>
        </div>
      )}
    </div>
  );
}
