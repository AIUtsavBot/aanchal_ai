/**
 * MatruRaksha AI - Offline Sync Service
 * Handles offline data storage and automatic sync when connection is restored
 */

import db, { STORES } from '../utils/db';

class OfflineSyncService {
    constructor() {
        this.isOnline = navigator.onLine;
        this.syncInProgress = false;
        this.retryQueue = [];
        this.maxRetries = 3;
        this.retryDelayMs = 2000;
        this.listeners = new Set();

        // Set up online/offline event listeners
        this._setupNetworkListeners();

        // Initialize database
        db.openDatabase().catch(console.error);
    }

    /**
     * Set up network status listeners
     */
    _setupNetworkListeners() {
        window.addEventListener('online', () => {
            console.log('🌐 Network: Online');
            this.isOnline = true;
            this._notifyListeners('online');
            this.syncAllPending();
        });

        window.addEventListener('offline', () => {
            console.log('📴 Network: Offline');
            this.isOnline = false;
            this._notifyListeners('offline');
        });
    }

    /**
     * Subscribe to sync status changes
     */
    subscribe(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    /**
     * Notify all listeners of status change
     */
    _notifyListeners(status, data = {}) {
        this.listeners.forEach(callback => {
            try {
                callback({ status, ...data });
            } catch (e) {
                console.error('Listener error:', e);
            }
        });
    }

    /**
     * Check if currently online
     */
    getOnlineStatus() {
        return navigator.onLine;
    }

    /**
     * Get pending sync count
     */
    async getPendingCount() {
        return db.getPendingCount();
    }

    // ==================== FORM OPERATIONS ====================

    /**
     * Save form data (offline-first)
     * @param {string} formType - Type of form (e.g., 'mother_registration', 'health_checkin')
     * @param {object} formData - The form data to save
     * @param {string} endpoint - API endpoint to sync to
     */
    async saveForm(formType, formData, endpoint) {
        const entry = {
            formType,
            formData,
            endpoint,
            createdAt: new Date().toISOString()
        };

        if (this.isOnline) {
            // Try to sync immediately
            try {
                const result = await this._syncForm(entry);
                console.log('✅ Form synced immediately');
                return { synced: true, result };
            } catch (error) {
                console.warn('⚠️ Immediate sync failed, storing offline:', error.message);
            }
        }

        // Store offline
        const id = await db.addItem(STORES.PENDING_FORMS, entry);
        console.log('💾 Form saved offline:', id);
        this._notifyListeners('form_queued', { formType, id });
        return { synced: false, offlineId: id };
    }

    /**
     * Sync a single form
     */
    async _syncForm(entry) {
        const response = await fetch(entry.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': this._getAuthHeader()
            },
            body: JSON.stringify(entry.formData)
        });

        if (!response.ok) {
            throw new Error(`Sync failed: ${response.status}`);
        }

        return response.json();
    }

    // ==================== CHAT OPERATIONS ====================

    /**
     * Save chat message (offline-first)
     * @param {string} motherId - Mother's ID
     * @param {string} message - Chat message content
     * @param {object} metadata - Additional metadata
     */
    async saveChat(motherId, message, metadata = {}) {
        const entry = {
            motherId,
            message,
            metadata,
            createdAt: new Date().toISOString()
        };

        if (this.isOnline) {
            try {
                const result = await this._syncChat(entry);
                console.log('✅ Chat synced immediately');
                return { synced: true, result };
            } catch (error) {
                console.warn('⚠️ Chat sync failed, storing offline:', error.message);
            }
        }

        const id = await db.addItem(STORES.PENDING_CHATS, entry);
        console.log('💾 Chat saved offline:', id);
        this._notifyListeners('chat_queued', { motherId, id });
        return { synced: false, offlineId: id };
    }

    /**
     * Sync a single chat
     */
    async _syncChat(entry) {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/agent/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': this._getAuthHeader()
            },
            body: JSON.stringify({
                mother_id: entry.motherId,
                query: entry.message,
                use_context: true
            })
        });

        if (!response.ok) {
            throw new Error(`Chat sync failed: ${response.status}`);
        }

        return response.json();
    }

    // ==================== DOCUMENT OPERATIONS ====================

    /**
     * Save document for upload (offline-first)
     * @param {string} motherId - Mother's ID
     * @param {File} file - The file to upload
     * @param {string} documentType - Type of document
     */
    async saveDocument(motherId, file, documentType) {
        // Convert file to base64 for storage
        const fileData = await this._fileToBase64(file);

        const entry = {
            motherId,
            fileName: file.name,
            fileType: file.type,
            fileSize: file.size,
            fileData,
            documentType,
            createdAt: new Date().toISOString()
        };

        if (this.isOnline) {
            try {
                const result = await this._syncDocument(entry, file);
                console.log('✅ Document synced immediately');
                return { synced: true, result };
            } catch (error) {
                console.warn('⚠️ Document sync failed, storing offline:', error.message);
            }
        }

        const id = await db.addItem(STORES.PENDING_DOCUMENTS, entry);
        console.log('💾 Document saved offline:', id);
        this._notifyListeners('document_queued', { motherId, fileName: file.name, id });
        return { synced: false, offlineId: id };
    }

    /**
     * Convert file to base64
     */
    _fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
        });
    }

    /**
     * Convert base64 back to File
     */
    _base64ToFile(base64, fileName, mimeType) {
        const arr = base64.split(',');
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new File([u8arr], fileName, { type: mimeType });
    }

    /**
     * Sync a single document
     */
    async _syncDocument(entry, file = null) {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

        // Reconstruct file if needed
        if (!file && entry.fileData) {
            file = this._base64ToFile(entry.fileData, entry.fileName, entry.fileType);
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('mother_id', entry.motherId);
        formData.append('document_type', entry.documentType);

        const response = await fetch(`${apiUrl}/api/documents/upload`, {
            method: 'POST',
            headers: {
                'Authorization': this._getAuthHeader()
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Document sync failed: ${response.status}`);
        }

        return response.json();
    }

    // ==================== SYNC ALL ====================

    /**
     * Sync all pending data
     */
    async syncAllPending() {
        if (this.syncInProgress) {
            console.log('⏳ Sync already in progress');
            return;
        }

        if (!this.isOnline) {
            console.log('📴 Cannot sync: offline');
            return;
        }

        this.syncInProgress = true;
        this._notifyListeners('sync_started');

        try {
            const results = {
                forms: await this._syncAllForms(),
                chats: await this._syncAllChats(),
                documents: await this._syncAllDocuments()
            };

            console.log('✅ Sync complete:', results);
            this._notifyListeners('sync_complete', results);
            return results;
        } catch (error) {
            console.error('❌ Sync error:', error);
            this._notifyListeners('sync_error', { error: error.message });
            throw error;
        } finally {
            this.syncInProgress = false;
        }
    }

    /**
     * Sync all pending forms
     */
    async _syncAllForms() {
        const pending = await db.getItemsByIndex(STORES.PENDING_FORMS, 'syncStatus', 'pending');
        let synced = 0;
        let failed = 0;

        for (const form of pending) {
            try {
                await this._syncForm(form);
                await db.deleteItem(STORES.PENDING_FORMS, form.id);
                synced++;
            } catch (error) {
                console.error('Form sync failed:', form.id, error);
                await this._handleRetry(STORES.PENDING_FORMS, form);
                failed++;
            }
        }

        return { synced, failed, total: pending.length };
    }

    /**
     * Sync all pending chats
     */
    async _syncAllChats() {
        const pending = await db.getItemsByIndex(STORES.PENDING_CHATS, 'syncStatus', 'pending');
        let synced = 0;
        let failed = 0;

        for (const chat of pending) {
            try {
                await this._syncChat(chat);
                await db.deleteItem(STORES.PENDING_CHATS, chat.id);
                synced++;
            } catch (error) {
                console.error('Chat sync failed:', chat.id, error);
                await this._handleRetry(STORES.PENDING_CHATS, chat);
                failed++;
            }
        }

        return { synced, failed, total: pending.length };
    }

    /**
     * Sync all pending documents
     */
    async _syncAllDocuments() {
        const pending = await db.getItemsByIndex(STORES.PENDING_DOCUMENTS, 'syncStatus', 'pending');
        let synced = 0;
        let failed = 0;

        for (const doc of pending) {
            try {
                await this._syncDocument(doc);
                await db.deleteItem(STORES.PENDING_DOCUMENTS, doc.id);
                synced++;
            } catch (error) {
                console.error('Document sync failed:', doc.id, error);
                await this._handleRetry(STORES.PENDING_DOCUMENTS, doc);
                failed++;
            }
        }

        return { synced, failed, total: pending.length };
    }

    /**
     * Handle retry logic for failed syncs
     */
    async _handleRetry(storeName, item) {
        const retryCount = (item.retryCount || 0) + 1;

        if (retryCount >= this.maxRetries) {
            // Mark as failed after max retries
            await db.updateItem(storeName, {
                ...item,
                syncStatus: 'failed',
                retryCount,
                lastError: 'Max retries exceeded'
            });
        } else {
            // Increment retry count
            await db.updateItem(storeName, {
                ...item,
                retryCount
            });
        }
    }

    /**
     * Get auth header from localStorage
     */
    _getAuthHeader() {
        try {
            const keys = Object.keys(localStorage).filter(
                k => k.startsWith('sb-') && k.endsWith('-auth-token')
            );
            if (keys.length > 0) {
                const stored = JSON.parse(localStorage.getItem(keys[0]));
                if (stored?.access_token) {
                    return `Bearer ${stored.access_token}`;
                }
            }
        } catch (e) {
            console.warn('Could not get auth token:', e);
        }
        return '';
    }

    /**
     * Clear all pending data
     */
    async clearAllPending() {
        await Promise.all([
            db.clearStore(STORES.PENDING_FORMS),
            db.clearStore(STORES.PENDING_CHATS),
            db.clearStore(STORES.PENDING_DOCUMENTS)
        ]);
        console.log('🧹 All pending data cleared');
    }
}

// Export singleton instance
export const offlineSync = new OfflineSyncService();

// Also export the class for testing
export default OfflineSyncService;
