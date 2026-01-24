import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Loader, CheckCircle, AlertCircle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function VoiceInput({ onDataReceived }) {
    const [isListening, setIsListening] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [transcript, setTranscript] = useState('');
    const recognitionRef = React.useRef(null);

    useEffect(() => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognizer = new SpeechRecognition();
            recognizer.continuous = true;
            recognizer.interimResults = true;
            recognizer.lang = 'en-IN';

            recognizer.onresult = (event) => {
                let finalTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    }
                }
                if (finalTranscript) {
                    setTranscript(prev => prev + ' ' + finalTranscript);
                }
            };

            recognizer.onerror = (event) => {
                console.error("Speech recognition error", event.error);
                if (event.error === 'not-allowed') {
                    setError("Microphone access denied.");
                } else {
                    // unexpected error, stop listening UI
                    setIsListening(false);
                }
            };

            recognizer.onend = () => {
                setIsListening(false);
            };

            recognitionRef.current = recognizer;
        } else {
            setError("Voice input not supported in this browser.");
        }

        return () => {
            if (recognitionRef.current) recognitionRef.current.stop();
        };
    }, []);

    const toggleListening = () => {
        if (!recognitionRef.current) return;

        if (isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
            if (transcript.trim().length > 2) {
                processVoiceData(transcript);
            }
        } else {
            setTranscript('');
            setError('');
            try {
                recognitionRef.current.start();
                setIsListening(true);
            } catch (e) {
                console.error("Start error:", e);
            }
        }
    };

    const processVoiceData = async (text) => {
        setIsProcessing(true);
        try {
            const response = await fetch(`${API_URL}/api/v1/voice/parse-vitals`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) throw new Error("Failed to process voice");

            const data = await response.json();
            if (onDataReceived) {
                onDataReceived(data);
            }
        } catch (err) {
            setError("Failed to process voice data.");
            console.error(err);
        } finally {
            setIsProcessing(false);
        }
    };

    if (error && !isListening) {
        return (
            <button onClick={() => setError('')} className="bg-red-50 text-red-600 p-2 rounded-full text-xs flex items-center gap-1">
                <AlertCircle className="w-4 h-4" /> {error}
            </button>
        )
    }

    return (
        <div className="relative inline-flex items-center gap-2">

            {/* Status Text when Active */}
            {(isListening || isProcessing) && (
                <div className={`text-sm font-medium animate-in fade-in slide-in-from-right-2
                    ${isListening ? 'text-red-600' : 'text-blue-600'}
                `}>
                    {isListening ? "Listening..." : "Analysis via AI..."}
                </div>
            )}

            <button
                type="button"
                onClick={toggleListening}
                disabled={isProcessing}
                className={`
                    relative p-3 rounded-full shadow-lg transition-all duration-300
                    ${isListening
                        ? 'bg-red-500 text-white hover:bg-red-600 scale-110 ring-4 ring-red-100'
                        : isProcessing
                            ? 'bg-blue-100 text-blue-500 cursor-wait'
                            : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-xl hover:-translate-y-1'
                    }
                `}
                title="Use Voice Entry"
            >
                {isProcessing ? (
                    <Loader className="w-6 h-6 animate-spin" />
                ) : isListening ? (
                    <MicOff className="w-6 h-6" />
                ) : (
                    <Mic className="w-6 h-6" />
                )}

                {/* Ping animation effect */}
                {isListening && (
                    <span className="absolute -top-1 -right-1 flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                    </span>
                )}
            </button>
        </div>
    );
}
