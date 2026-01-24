// FILE: frontend/src/services/telegram.js
import { telegramAPI } from './api'

class TelegramService {
  constructor() {
    this.botName = import.meta.env.VITE_TELEGRAM_BOT_NAME || 'MaatruRaksha_AI_bot'
    this.botURL = `https://t.me/${this.botName}`
  }

  /**
   * Get Telegram bot link
   */
  getBotLink() {
    return this.botURL
  }

  /**
   * Send risk alert via Telegram
   */
  async sendRiskAlert(chatId, motherName, status, riskScore) {
    try {
      const response = await telegramAPI.sendRiskAlert({
        chat_id: chatId,
        mother_name: motherName,
        status: status,
        risk_score: riskScore
      })
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Failed to send risk alert:', error)
      return { success: false, error: error.message }
    }
  }

  /**
   * Send appointment reminder via Telegram
   */
  async sendAppointmentReminder(chatId, motherName, facility, date, time = '10:00 AM') {
    try {
      const response = await telegramAPI.sendAppointment({
        chat_id: chatId,
        mother_name: motherName,
        facility: facility,
        appointment_date: date,
        appointment_time: time
      })
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Failed to send appointment:', error)
      return { success: false, error: error.message }
    }
  }

  /**
   * Send medication reminder via Telegram
   */
  async sendMedicationReminder(chatId, medications) {
    try {
      const response = await telegramAPI.sendMedication({
        chat_id: chatId,
        medications: medications
      })
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Failed to send medication reminder:', error)
      return { success: false, error: error.message }
    }
  }

  /**
   * Send nutrition plan via Telegram
   */
  async sendNutritionPlan(chatId, motherName, plan, language = 'en') {
    try {
      const response = await telegramAPI.sendNutrition({
        chat_id: chatId,
        mother_name: motherName,
        plan: plan,
        language: language
      })
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Failed to send nutrition plan:', error)
      return { success: false, error: error.message }
    }
  }

  /**
   * Send emergency alert via Telegram
   */
  async sendEmergencyAlert(chatId, motherName, symptoms, nearestFacility) {
    try {
      const response = await telegramAPI.sendEmergency({
        chat_id: chatId,
        mother_name: motherName,
        symptoms: symptoms,
        nearest_facility: nearestFacility
      })
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Failed to send emergency alert:', error)
      return { success: false, error: error.message }
    }
  }

  /**
   * Send ASHA task via Telegram
   */
  async sendASHATask(chatId, ashaName, motherName, priority, taskDescription) {
    try {
      const response = await telegramAPI.sendASHATask({
        chat_id: chatId,
        asha_name: ashaName,
        mother_name: motherName,
        priority: priority,
        task_description: taskDescription
      })
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Failed to send ASHA task:', error)
      return { success: false, error: error.message }
    }
  }

  /**
   * Test Telegram connection
   */
  async testConnection(chatId) {
    try {
      const response = await telegramAPI.testConnection(chatId)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Failed to test Telegram connection:', error)
      return { success: false, error: error.message }
    }
  }

  /**
   * Format instructions for user to get Telegram chat ID
   */
  getInstructions() {
    return `
To get your Telegram Chat ID:
1. Open Telegram app
2. Search for: @${this.botName}
3. Click "Start"
4. The bot will send you your chat ID
5. Copy it and paste in the registration form
    `
  }
}

export default new TelegramService()