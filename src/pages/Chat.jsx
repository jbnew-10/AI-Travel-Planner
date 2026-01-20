import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Send, Loader2, Copy, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

function Chat() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [speakingId, setSpeakingId] = useState(null);

  const messagesEndRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  const activeChat = chats.find((c) => c.id === activeChatId);

  /* Create first chat */
  useEffect(() => {
    if (chats.length === 0) {
      const id = Date.now().toString();
      setChats([
        {
          id,
          title: "Chat",
          messages: [],
          createdAt: new Date(),
        },
      ]);
      setActiveChatId(id);
    }
  }, [chats]);

  /* Auto scroll */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chats]);

  /* Backend call */
  const sendToWatson = async (msg) => {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg }),
    });
    const data = await res.json();
    return data.response;
  };

  /* Send message */
  const handleSend = async () => {
    if (!message.trim() || loading) return;

    const id = Date.now().toString();
    const userMsg = {
      id,
      text: message,
      sender: "user",
      timestamp: new Date(),
    };

    setChats((prev) =>
      prev.map((chat) =>
        chat.id === activeChatId
          ? { ...chat, messages: [...chat.messages, userMsg] }
          : chat
      )
    );

    setMessage("");
    setLoading(true);

    try {
      const reply = await sendToWatson(message);
      const botMsg = {
        id: id + "_bot",
        text: reply,
        sender: "bot",
        timestamp: new Date(),
      };

      setChats((prev) =>
        prev.map((chat) =>
          chat.id === activeChatId
            ? { ...chat, messages: [...chat.messages, botMsg] }
            : chat
        )
      );
    } catch {
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === activeChatId
            ? {
                ...chat,
                messages: [
                  ...chat.messages,
                  {
                    id: id + "_err",
                    text: "⚠️ Something went wrong",
                    sender: "bot",
                    timestamp: new Date(),
                  },
                ],
              }
            : chat
        )
      );
    } finally {
      setLoading(false);
    }
  };

  /* Text to speech */
  const handleSpeakToggle = (id, text) => {
    if (speakingId === id) {
      synthRef.current.cancel();
      setSpeakingId(null);
    } else {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onend = () => setSpeakingId(null);
      synthRef.current.speak(utterance);
      setSpeakingId(id);
    }
  };

  return (
    <div className="flex h-screen bg-[#0f1318] text-gray-100">
      {/* LEFT INFO SIDEBAR */}
      <aside className="hidden sm:flex w-64 bg-[#0b0f14] border-r border-gray-800 p-5 flex-col">
        <h1 className="text-xl font-bold text-cyan-400">AI Travel Agent</h1>

        <p className="text-sm text-gray-400 mt-2">
          Smart AI assistant for travel planning and destination ideas.
        </p>

        <div className="mt-6">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
            Features
          </p>
          <ul className="text-sm text-gray-300 space-y-2">
            <li>🌍 Trip planning</li>
            <li>🧭 Route suggestions</li>
            <li>🏨 Hotel ideas</li>
            <li>🍽 Food recommendations</li>
            <li>📍 Local tips</li>
          </ul>
        </div>

        <div className="mt-6">
          <span className="inline-flex items-center gap-2 px-2 py-1 rounded-md text-xs bg-green-500/20 text-green-400">
            ● Online
          </span>
        </div>

        <div className="mt-auto text-xs text-gray-500">
          © {new Date().getFullYear()} AI Travel Agent Built by{" "}
          <span className="text-white font-medium">Jeet</span>
          <div className="mt-3 space-x-4">
            <a href="#" className="text-cyan-400 hover:underline">
              About Me
            </a>
            <Link to="/privacypolicy" className="text-cyan-400 hover:underline">
              Privacy Policy
            </Link>
          </div>
        </div>
      </aside>

      {/* MAIN CHAT */}
      <main className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {activeChat?.messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] px-4 py-2 rounded-xl text-sm ${
                  msg.sender === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800"
                }`}
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw]}
                >
                  {msg.text || "sorry..."}
                </ReactMarkdown>

                {msg.sender === "bot" && (
                  <div className="flex justify-end gap-2 mt-2">
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => handleSpeakToggle(msg.id, msg.text)}
                    >
                      <Volume2 className="w-4 h-4 text-cyan-400" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => navigator.clipboard.writeText(msg.text)}
                    >
                      <Copy className="w-4 h-4 text-cyan-400" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              Thinking...
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* INPUT */}
        <div className="border-t border-gray-700 p-3 flex gap-2">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a message..."
            rows={2}
            className="flex-1 resize-none rounded-md bg-gray-800 border border-gray-700 p-2 text-sm text-gray-100 placeholder-gray-400"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />

          <Button
            onClick={handleSend}
            disabled={!message.trim() || loading}
            className="bg-cyan-600 hover:bg-cyan-700"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </main>
    </div>
  );
}

export default Chat;
