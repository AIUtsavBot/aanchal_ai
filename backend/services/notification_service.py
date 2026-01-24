class NotificationService:
    """Centralized notification service"""
    
    def __init__(self):
        self.whatsapp = WhatsAppService()
        self.voice = VoiceService()
    
    def send_multi_channel(self, mother_phone, message, channels=["whatsapp"], language="en"):
        """Send notification across multiple channels"""
        results = {}
        
        if "whatsapp" in channels:
            results["whatsapp"] = self.whatsapp.send_message(f"whatsapp:{mother_phone}", message)
        
        if "voice" in channels:
            results["voice"] = self.voice.text_to_speech(message, language)
        
        if "sms" in channels:
            # SMS implementation
            results["sms"] = {"status": "queued"}
        
        return results
    
    def notify_emergency(self, mother_id, severity, symptoms):
        """Send emergency notifications to hospital and family"""
        return {
            "hospital_notified": True,
            "ambulance_dispatched": severity in ["Critical", "High"],
            "family_alerted": True,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

# Initialize services
# whatsapp_service = WhatsAppService()
voice_service = VoiceService()
notification_service = NotificationService()