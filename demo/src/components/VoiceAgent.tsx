"use client";

/**
 * VoiceAgent.tsx
 * ==============
 * Floating Voice Command Button — সব পেজে সবসময় দেখা যাবে।
 * বাংলা ও ইংরেজি voice command support করে।
 */

import React, { useState, useEffect } from "react";
import { useVoiceAgent } from "@/hooks/useVoiceAgent";
import { useAppStore } from "@/store/useAppStore";
import {
  Mic,
  MicOff,
  Volume2,
  X,
  Loader2,
  HelpCircle,
  ChevronUp,
  WifiOff,
} from "lucide-react";

const COMMAND_HINTS_BN = [
  { icon: "🌿", cmd: "আলু রোগ স্ক্যান", desc: "আলু নির্বাচন করে রোগ নির্ণয় খুলুন" },
  { icon: "🌾", cmd: "ধানের রোগ", desc: "ধান ফসল রোগ নির্ণয়" },
  { icon: "📸", cmd: "ছবি তোলো", desc: "ক্যামেরা ও ছবি আপলোড শুরু করুন" },
  { icon: "🚜", cmd: "জমি যোগ করো", desc: "নতুন ফসলের জমি যোগ করুন" },
  { icon: "💊", cmd: "নাবী ধসা প্রতিকার", desc: "লেট ব্লাইট রোগের চিকিৎসা জানুন" },
  { icon: "📞", cmd: "১৬১২৩ কল করো", desc: "কৃষি তথ্য সার্ভিস হটলাইন" },
  { icon: "🌾", cmd: "আমার জমি", desc: "Farms পেজ খুলুন" },
  { icon: "📋", cmd: "ইতিহাস", desc: "পূর্ববর্তী কেস হিস্ট্রি দেখুন" },
  { icon: "🏠", cmd: "হোম", desc: "ড্যাশবোর্ডে যান" },
  { icon: "👤", cmd: "প্রোফাইল", desc: "প্রোফাইল পেজ খুলুন" },
  { icon: "🌙", cmd: "ডার্ক মোড", desc: "থিম পরিবর্তন করুন" },
  { icon: "🌐", cmd: "ইংলিশ", desc: "ইংরেজি ভাষায় সুইচ করুন" },
  { icon: "🚪", cmd: "লগআউট", desc: "অ্যাকাউন্ট থেকে লগআউট" },
  { icon: "❓", cmd: "সাহায্য", desc: "সব ভয়েস কমান্ড শুনুন" },
];

const COMMAND_HINTS_EN = [
  { icon: "🌿", cmd: "Potato scan", desc: "Select potato & open diagnosis" },
  { icon: "🌾", cmd: "Rice disease", desc: "Diagnose rice diseases" },
  { icon: "📸", cmd: "Take photo", desc: "Open camera or upload leaf" },
  { icon: "🚜", cmd: "Add farm", desc: "Add new farmland plot" },
  { icon: "💊", cmd: "Late blight remedy", desc: "Get late blight treatments" },
  { icon: "📞", cmd: "Call 16123", desc: "Agriculture Helpline" },
  { icon: "🌾", cmd: "My Farms", desc: "Open farms page" },
  { icon: "📋", cmd: "History", desc: "View diagnosis case history" },
  { icon: "🏠", cmd: "Home", desc: "Go to dashboard" },
  { icon: "👤", cmd: "Profile", desc: "Open user profile" },
  { icon: "🌙", cmd: "Dark mode", desc: "Toggle theme" },
  { icon: "🌐", cmd: "Bangla", desc: "Switch to Bangla" },
  { icon: "🚪", cmd: "Logout", desc: "Sign out" },
  { icon: "❓", cmd: "Help", desc: "List all voice commands" },
];

export default function VoiceAgent() {
  const { language } = useAppStore();
  const isBn = language === "bn";

  const {
    status,
    transcript,
    lastResponse,
    isSupported,
    startListening,
    stopListening,
    executeCommand,
  } = useVoiceAgent();

  const [showPanel, setShowPanel] = useState(false);
  const [showHints, setShowHints] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const isListening = status === "listening";
  const isProcessing = status === "processing";
  const isSpeaking = status === "speaking";

  const hints = isBn ? COMMAND_HINTS_BN : COMMAND_HINTS_EN;

  const quickActions = [
    { label: isBn ? "🌿 আলু স্ক্যান" : "🌿 Potato Scan", cmd: isBn ? "আলু রোগ স্ক্যান" : "Potato scan" },
    { label: isBn ? "📸 ছবি তোলো" : "📸 Take Photo", cmd: isBn ? "ছবি তোলো" : "Take photo" },
    { label: isBn ? "🚜 জমি যোগ" : "🚜 Add Farm", cmd: isBn ? "জমি যোগ করো" : "Add farm" },
    { label: isBn ? "🌾 ধানের রোগ" : "🌾 Rice Disease", cmd: isBn ? "ধানের রোগ" : "Rice disease" },
    { label: isBn ? "💊 নাবী ধসা" : "💊 Late Blight", cmd: isBn ? "নাবী ধসা প্রতিকার" : "Late blight" },
    { label: isBn ? "📞 ১৬১২৩ কল" : "📞 Call 16123", cmd: isBn ? "১৬১২৩ কল করো" : "Call 16123" },
  ];

  const handleMicClick = () => {
    if (!isSupported) return;
    if (isListening) {
      stopListening();
    } else if (!isSpeaking && !isProcessing) {
      setShowPanel(true);
      startListening();
    }
  };

  const getStatusText = () => {
    if (!isSupported) return isBn ? "সাপোর্টেড নয়" : "Not supported";
    switch (status) {
      case "listening": return isBn ? "বলুন..." : "Listening...";
      case "processing": return isBn ? "বুঝছি..." : "Processing...";
      case "speaking": return isBn ? "উত্তর দিচ্ছি..." : "Responding...";
      case "error": return isBn ? "মাইক অনুমতি দিন" : "Allow mic access";
      default: return isBn ? "ভয়েস কমান্ড" : "Voice Command";
    }
  };

  const getBubbleColor = () => {
    if (!isSupported) return "bg-slate-400 shadow-slate-400/40";
    if (isListening) return "bg-red-500 shadow-red-500/50";
    if (isProcessing) return "bg-amber-500 shadow-amber-500/50";
    if (isSpeaking) return "bg-blue-500 shadow-blue-500/50";
    return "bg-emerald-600 shadow-emerald-600/50";
  };

  const getHeaderColor = () => {
    if (isListening) return "from-red-600 to-rose-600";
    if (isProcessing) return "from-amber-500 to-orange-600";
    if (isSpeaking) return "from-blue-600 to-indigo-600";
    return "from-emerald-600 to-teal-700";
  };

  return (
    /* Fixed bottom-right — সব পেজে সবসময় থাকবে */
    <div className="fixed bottom-6 right-6 z-[9999] flex flex-col items-end gap-3 pointer-events-none">

      {/* ── Expanded Panel ─────────────────────────────── */}
      {showPanel && (
        <div className="pointer-events-auto w-80 rounded-2xl bg-card border border-border shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 duration-200">

          {/* Panel Header */}
          <div className={`p-4 text-white flex items-center justify-between bg-gradient-to-r transition-all duration-300 ${getHeaderColor()}`}>
            <div className="flex items-center gap-2.5">
              {isListening ? (
                <div className="relative">
                  <Mic className="h-5 w-5" />
                  <span className="absolute -inset-2 rounded-full border border-white/40 animate-ping" />
                </div>
              ) : isProcessing ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : isSpeaking ? (
                <Volume2 className="h-5 w-5 animate-pulse" />
              ) : (
                <Mic className="h-5 w-5" />
              )}
              <div>
                <p className="text-[10px] font-semibold opacity-80 uppercase tracking-wider">
                  KrishiBondhu {isBn ? "ভয়েস এজেন্ট" : "Voice Agent"}
                </p>
                <p className="text-sm font-bold">{getStatusText()}</p>
              </div>
            </div>
            <button
              onClick={() => { setShowPanel(false); stopListening(); }}
              className="h-7 w-7 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Transcript / Response Display */}
          <div className="px-4 py-3 min-h-[52px] border-b border-border/60 bg-muted/30">
            {!isSupported ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <WifiOff className="h-4 w-4 shrink-0" />
                <p className="text-xs">
                  {isBn
                    ? "আপনার ব্রাউজার Voice API সাপোর্ট করে না। Chrome বা Edge ব্যবহার করুন।"
                    : "Your browser doesn't support Voice API. Use Chrome or Edge."}
                </p>
              </div>
            ) : transcript ? (
              <div className="flex items-start gap-2">
                <span className="text-lg leading-none">🎙️</span>
                <p className="text-sm font-medium text-foreground">&ldquo;{transcript}&rdquo;</p>
              </div>
            ) : lastResponse ? (
              <div className="flex items-start gap-2">
                <span className="text-lg leading-none">🤖</span>
                <p className="text-sm text-muted-foreground italic">{lastResponse}</p>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                {isBn ? "নিচের বাটন চেপে বাংলায় বলুন..." : "Press the button below and speak..."}
              </p>
            )}
          </div>

          {/* Mic Action Button */}
          <div className="p-3 flex items-center gap-2">
            <button
              onClick={handleMicClick}
              disabled={!isSupported || isProcessing || isSpeaking}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-bold transition-all ${
                !isSupported
                  ? "bg-muted text-muted-foreground cursor-not-allowed"
                  : isListening
                  ? "bg-red-500 hover:bg-red-600 text-white"
                  : isProcessing || isSpeaking
                  ? "bg-muted text-muted-foreground cursor-not-allowed"
                  : "bg-emerald-600 hover:bg-emerald-700 text-white active:scale-95"
              }`}
            >
              {isListening ? (
                <><MicOff className="h-4 w-4" /><span>{isBn ? "থামুন" : "Stop"}</span></>
              ) : isProcessing ? (
                <><Loader2 className="h-4 w-4 animate-spin" /><span>{isBn ? "বুঝছি..." : "Processing..."}</span></>
              ) : isSpeaking ? (
                <><Volume2 className="h-4 w-4 animate-pulse" /><span>{isBn ? "বলছি..." : "Speaking..."}</span></>
              ) : (
                <><Mic className="h-4 w-4" /><span>{isBn ? "কথা বলুন" : "Speak Now"}</span></>
              )}
            </button>

            {/* Help toggle */}
            <button
              onClick={() => setShowHints((v) => !v)}
              className="h-10 w-10 rounded-xl bg-muted hover:bg-muted/80 flex items-center justify-center transition-colors text-muted-foreground hover:text-foreground shrink-0"
              title={isBn ? "কমান্ড তালিকা" : "Command list"}
            >
              <HelpCircle className="h-4 w-4" />
            </button>
          </div>

          {/* Quick Action Chips */}
          <div className="px-3 pb-3 pt-1 border-t border-border/40">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block mb-1.5">
              {isBn ? "কুইক ভয়েস অ্যাকশন:" : "Quick Voice Actions:"}
            </span>
            <div className="flex flex-wrap gap-1.5">
              {quickActions.map((qa, i) => (
                <button
                  key={i}
                  onClick={() => executeCommand(qa.cmd)}
                  className="px-2.5 py-1 rounded-lg bg-muted hover:bg-emerald-500/10 hover:text-emerald-600 border border-border/60 text-xs font-semibold text-foreground transition-all active:scale-95"
                >
                  {qa.label}
                </button>
              ))}
            </div>
          </div>

          {/* Command Hints Accordion */}
          {showHints && (
            <div className="border-t border-border/60">
              <button
                onClick={() => setShowHints(false)}
                className="w-full px-4 py-2 flex items-center justify-between text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
              >
                <span>{isBn ? "ভয়েস কমান্ড তালিকা" : "Voice Commands"}</span>
                <ChevronUp className="h-3.5 w-3.5" />
              </button>
              <div className="max-h-52 overflow-y-auto px-3 pb-3 space-y-1">
                {hints.map((h, i) => (
                  <div
                    key={i}
                    onClick={() => executeCommand(h.cmd)}
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:bg-muted/60 cursor-pointer transition-colors"
                  >
                    <span className="text-base leading-none">{h.icon}</span>
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-bold text-foreground block">&ldquo;{h.cmd}&rdquo;</span>
                      <span className="text-[10px] text-muted-foreground">{h.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Floating Mic Bubble — সবসময় visible ─── */}
      <div
        className="pointer-events-auto flex items-center gap-2.5 relative"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Label pill — panel বন্ধ থাকলে দেখা যাবে */}
        {(!showPanel || isHovered) && (
          <div
            onClick={() => {
              setShowPanel(true);
              if (isSupported) startListening();
            }}
            className={`cursor-pointer bg-card/95 backdrop-blur border border-emerald-500/40 shadow-xl rounded-full px-3.5 py-2 flex items-center gap-2.5 transition-all duration-300 ${
              isHovered ? "scale-105 ring-2 ring-emerald-500/30" : ""
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span className="text-sm">🎙️</span>
              <div className="flex flex-col text-left">
                <span className="text-xs font-black text-foreground leading-tight">
                  {isListening
                    ? isBn
                      ? "শুনছি... বলুন"
                      : "Listening..."
                    : isSpeaking
                    ? isBn
                      ? "উত্তর দিচ্ছি..."
                      : "Responding..."
                    : isBn
                    ? "ভয়েস সহকারী"
                    : "Voice Assistant"}
                </span>
                <span className="text-[10px] text-muted-foreground hidden sm:block">
                  {isBn ? "কথা বলতে চাপুন" : "Click to speak"}
                </span>
              </div>
            </div>

            {/* Sound Wave Animation Bars when active */}
            {(isListening || isSpeaking) && (
              <div className="flex items-end gap-0.5 h-3.5 pl-1 border-l border-border">
                <span className="w-1 bg-emerald-500 rounded-full animate-bounce h-2" style={{ animationDelay: "0ms" }} />
                <span className="w-1 bg-emerald-500 rounded-full animate-bounce h-3.5" style={{ animationDelay: "150ms" }} />
                <span className="w-1 bg-emerald-500 rounded-full animate-bounce h-2" style={{ animationDelay: "300ms" }} />
                <span className="w-1 bg-emerald-500 rounded-full animate-bounce h-3" style={{ animationDelay: "450ms" }} />
              </div>
            )}
          </div>
        )}

        {/* Main Mic Button */}
        <button
          onClick={() => {
            if (showPanel) {
              setShowPanel(false);
              stopListening();
            } else {
              setShowPanel(true);
              if (isSupported) startListening();
            }
          }}
          className={`relative h-14 w-14 rounded-full text-white shadow-2xl flex items-center justify-center transition-all duration-300 hover:scale-110 active:scale-95 ring-4 ring-emerald-500/20 hover:ring-emerald-400/50 ${getBubbleColor()}`}
          title={isBn ? "ভয়েস কমান্ড দিন" : "Voice command"}
        >
          {/* Pulsing rings when listening */}
          {isListening && (
            <>
              <span className="absolute inset-0 rounded-full border-2 border-red-300 animate-ping opacity-75" />
              <span
                className="absolute inset-0 rounded-full border-2 border-red-200 animate-ping opacity-40"
                style={{ animationDelay: "0.4s" }}
              />
            </>
          )}

          {/* Icon */}
          {isListening ? (
            <Mic className="h-6 w-6 animate-pulse" />
          ) : isProcessing ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : isSpeaking ? (
            <Volume2 className="h-6 w-6 animate-bounce" />
          ) : showPanel ? (
            <X className="h-6 w-6" />
          ) : (
            <Mic className="h-6 w-6" />
          )}
        </button>
      </div>
    </div>
  );
}
