import React, { useEffect, useState, useRef } from "react";
import { supabase } from "../services/auth.js";
import {
  MessageCircle,
  Loader,
  Bot,
  User,
  Stethoscope,
  Users,
  Send,
  AlertCircle,
} from "lucide-react";

/**
 * PatientChatHistory - Unified chat view for patient
 * Displays: telegram bot conversations + doctor/ASHA case discussions
 * Allows doctors/ASHA workers to add new messages
 */
export default function PatientChatHistory({
  motherId,
  userRole = "DOCTOR",
  userName = "Doctor",
}) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef(null);

  const scrollToBottom = () => {
    setTimeout(() => {
      if (listRef.current) {
        listRef.current.scrollTop = listRef.current.scrollHeight;
      }
    }, 100);
  };

  const loadAllMessages = async () => {
    if (!motherId) return;

    try {
      setLoading(true);
      setError("");

      // Fetch telegram bot conversations from telegram_logs table
      const { data: telegramChats, error: telegramErr } = await supabase
        .from("telegram_logs")
        .select("id, message_type, message_content, created_at")
        .eq("mother_id", motherId);

      if (telegramErr) throw telegramErr;

      // Fetch case discussions (doctor/ASHA chats)
      const { data: discussions, error: discErr } = await supabase
        .from("case_discussions")
        .select("id, sender_role, sender_name, message, created_at")
        .eq("mother_id", motherId);

      if (discErr) throw discErr;

      // Normalize telegram messages - message_type: user_query = patient, agent_response = bot
      const normalizedTelegram = (telegramChats || []).map((c) => ({
        id: `tg-${c.id}`,
        role: c.message_type === "user_query" ? "PATIENT" : "BOT",
        senderName:
          c.message_type === "user_query" ? "Patient" : "MatruRaksha Bot",
        content: c.message_content,
        createdAt: new Date(c.created_at),
        source: "telegram",
      }));

      const normalizedDiscussions = (discussions || []).map((d) => ({
        id: `disc-${d.id}`,
        role: d.sender_role?.toUpperCase() || "UNKNOWN",
        senderName: d.sender_name || d.sender_role,
        content: d.message,
        createdAt: new Date(d.created_at),
        source: "discussion",
      }));

      // Combine and sort chronologically
      const allMessages = [
        ...normalizedTelegram,
        ...normalizedDiscussions,
      ].sort((a, b) => a.createdAt - b.createdAt);

      setMessages(allMessages);
      scrollToBottom();
    } catch (err) {
      setError("Failed to load messages: " + err.message);
      console.error("Load messages error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!motherId) return;

    loadAllMessages();

    // Set up real-time subscription for new case discussions
    const channel = supabase
      .channel(`chat_${motherId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "case_discussions",
          filter: `mother_id=eq.${motherId}`,
        },
        (payload) => {
          const newMsg = {
            id: `disc-${payload.new.id}`,
            role: payload.new.sender_role?.toUpperCase() || "UNKNOWN",
            senderName: payload.new.sender_name || payload.new.sender_role,
            content: payload.new.message,
            createdAt: new Date(payload.new.created_at),
            source: "discussion",
          };
          setMessages((prev) => [...prev, newMsg]);
          scrollToBottom();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [motherId]);

  // Send a new message - calls API to store and relay to Telegram
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setSending(true);
    setError("");

    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

    try {
      const response = await fetch(`${API_URL}/case-discussions/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mother_id: motherId,
          sender_role: userRole,
          sender_name: userName,
          message: input.trim(),
          send_to_telegram: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to send message");
      }

      const result = await response.json();
      console.log("Message sent:", result);

      // If telegram wasn't sent, show a non-blocking notice
      if (!result.telegram_sent && result.telegram_error) {
        console.warn("Telegram notification not sent:", result.telegram_error);
      }

      setInput("");
    } catch (err) {
      setError("Failed to send message: " + err.message);
      console.error("Send message error:", err);
    } finally {
      setSending(false);
    }
  };

  // Get background color based on role
  const getRoleBgColor = (role) => {
    switch (role) {
      case "PATIENT":
        return "bg-purple-50 border-purple-200";
      case "BOT":
        return "bg-blue-50 border-blue-200";
      case "DOCTOR":
        return "bg-teal-50 border-teal-200";
      case "ASHA":
        return "bg-green-50 border-green-200";
      case "ADMIN":
        return "bg-orange-50 border-orange-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  // Get icon based on role
  const getRoleIcon = (role) => {
    switch (role) {
      case "PATIENT":
        return <User className="w-4 h-4" />;
      case "BOT":
        return <Bot className="w-4 h-4" />;
      case "DOCTOR":
        return <Stethoscope className="w-4 h-4" />;
      case "ASHA":
        return <Users className="w-4 h-4" />;
      default:
        return <MessageCircle className="w-4 h-4" />;
    }
  };

  // Get label badge color
  const getRoleBadge = (role) => {
    const baseClasses =
      "px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1";
    switch (role) {
      case "PATIENT":
        return `${baseClasses} bg-purple-100 text-purple-800`;
      case "BOT":
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case "DOCTOR":
        return `${baseClasses} bg-teal-100 text-teal-800`;
      case "ASHA":
        return `${baseClasses} bg-green-100 text-green-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header Legend */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
            <User className="w-3 h-3" /> Patient
          </span>
          <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
            <Bot className="w-3 h-3" /> Bot
          </span>
          <span className="flex items-center gap-1 px-2 py-1 bg-teal-100 text-teal-700 rounded-full">
            <Stethoscope className="w-3 h-3" /> Doctor
          </span>
          <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full">
            <Users className="w-3 h-3" /> ASHA
          </span>
        </div>
      </div>

      {/* Messages Container */}
      <div ref={listRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Loader className="w-8 h-8 animate-spin mx-auto mb-2 text-blue-600" />
              <p className="text-gray-600">Loading chat history...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <MessageCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-gray-600 font-medium">No chat history yet</p>
              <p className="text-gray-500 text-sm mt-1">
                Start the conversation by sending a message below
              </p>
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <div key={m.id} className="animate-fade-in">
              <div
                className={`rounded-lg border ${getRoleBgColor(m.role)} p-3`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={getRoleBadge(m.role)}>
                      {getRoleIcon(m.role)}
                      <span>{m.role}</span>
                    </span>
                    {m.senderName && m.senderName !== m.role && (
                      <span className="text-xs text-gray-600">
                        {m.senderName}
                      </span>
                    )}
                    {m.source === "telegram" && (
                      <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                        📱 Telegram
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500">
                    {m.createdAt.toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
                <p className="text-gray-900 text-sm leading-relaxed whitespace-pre-wrap">
                  {m.content}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-4 mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={sendMessage}
        className="border-t border-gray-200 bg-white p-4"
      >
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Add a note or message..."
            disabled={sending}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors disabled:cursor-not-allowed"
          >
            {sending ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Send
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
