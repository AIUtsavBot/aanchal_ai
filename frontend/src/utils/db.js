/**
 * MatruRaksha AI - IndexedDB Database Wrapper
 * Provides offline storage for forms, chats, and cached data
 */

const DB_NAME = 'matruraksha_offline';
const DB_VERSION = 1;

const STORES = {
    PENDING_FORMS: 'pendingForms',
    PENDING_CHATS: 'pendingChats',
    PENDING_DOCUMENTS: 'pendingDocuments',
    CACHED_DATA: 'cachedData',
    SYNC_QUEUE: 'syncQueue'
};

let dbInstance = null;

/**
 * Open or create the IndexedDB database
 */
export const openDatabase = () => {
    return new Promise((resolve, reject) => {
        if (dbInstance) {
            resolve(dbInstance);
            return;
        }

        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            console.error('Failed to open IndexedDB:', request.error);
            reject(request.error);
        };

        request.onsuccess = () => {
            dbInstance = request.result;
            console.log('✅ IndexedDB opened successfully');
            resolve(dbInstance);
        };

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            // Store for pending form submissions
            if (!db.objectStoreNames.contains(STORES.PENDING_FORMS)) {
                const formStore = db.createObjectStore(STORES.PENDING_FORMS, {
                    keyPath: 'id',
                    autoIncrement: true
                });
                formStore.createIndex('formType', 'formType', { unique: false });
                formStore.createIndex('timestamp', 'timestamp', { unique: false });
                formStore.createIndex('syncStatus', 'syncStatus', { unique: false });
            }

            // Store for pending chat messages
            if (!db.objectStoreNames.contains(STORES.PENDING_CHATS)) {
                const chatStore = db.createObjectStore(STORES.PENDING_CHATS, {
                    keyPath: 'id',
                    autoIncrement: true
                });
                chatStore.createIndex('motherId', 'motherId', { unique: false });
                chatStore.createIndex('timestamp', 'timestamp', { unique: false });
                chatStore.createIndex('syncStatus', 'syncStatus', { unique: false });
            }

            // Store for pending document uploads
            if (!db.objectStoreNames.contains(STORES.PENDING_DOCUMENTS)) {
                const docStore = db.createObjectStore(STORES.PENDING_DOCUMENTS, {
                    keyPath: 'id',
                    autoIncrement: true
                });
                docStore.createIndex('motherId', 'motherId', { unique: false });
                docStore.createIndex('timestamp', 'timestamp', { unique: false });
                docStore.createIndex('syncStatus', 'syncStatus', { unique: false });
            }

            // Store for cached API responses
            if (!db.objectStoreNames.contains(STORES.CACHED_DATA)) {
                const cacheStore = db.createObjectStore(STORES.CACHED_DATA, {
                    keyPath: 'cacheKey'
                });
                cacheStore.createIndex('expiresAt', 'expiresAt', { unique: false });
            }

            // Store for sync queue management
            if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
                const queueStore = db.createObjectStore(STORES.SYNC_QUEUE, {
                    keyPath: 'id',
                    autoIncrement: true
                });
                queueStore.createIndex('priority', 'priority', { unique: false });
                queueStore.createIndex('retryCount', 'retryCount', { unique: false });
            }

            console.log('✅ IndexedDB stores created');
        };
    });
};

/**
 * Add an item to a store
 */
export const addItem = async (storeName, data) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readwrite');
        const store = transaction.objectStore(storeName);

        const itemWithMeta = {
            ...data,
            timestamp: Date.now(),
            syncStatus: 'pending'
        };

        const request = store.add(itemWithMeta);

        request.onsuccess = () => {
            console.log(`✅ Item added to ${storeName}:`, request.result);
            resolve(request.result);
        };

        request.onerror = () => {
            console.error(`Failed to add item to ${storeName}:`, request.error);
            reject(request.error);
        };
    });
};

/**
 * Get all items from a store
 */
export const getAllItems = async (storeName) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
};

/**
 * Get items by index
 */
export const getItemsByIndex = async (storeName, indexName, value) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const index = store.index(indexName);
        const request = index.getAll(value);

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
};

/**
 * Update an item in a store
 */
export const updateItem = async (storeName, item) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.put(item);

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
};

/**
 * Delete an item from a store
 */
export const deleteItem = async (storeName, id) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.delete(id);

        request.onsuccess = () => {
            console.log(`✅ Item ${id} deleted from ${storeName}`);
            resolve();
        };
        request.onerror = () => reject(request.error);
    });
};

/**
 * Clear all items from a store
 */
export const clearStore = async (storeName) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.clear();

        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
};

/**
 * Get count of items in a store
 */
export const getCount = async (storeName) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.count();

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
};

/**
 * Get pending items count (items waiting to sync)
 */
export const getPendingCount = async () => {
    const [forms, chats, docs] = await Promise.all([
        getItemsByIndex(STORES.PENDING_FORMS, 'syncStatus', 'pending'),
        getItemsByIndex(STORES.PENDING_CHATS, 'syncStatus', 'pending'),
        getItemsByIndex(STORES.PENDING_DOCUMENTS, 'syncStatus', 'pending')
    ]);

    return {
        forms: forms.length,
        chats: chats.length,
        documents: docs.length,
        total: forms.length + chats.length + docs.length
    };
};

/**
 * Cache API response
 */
export const cacheResponse = async (cacheKey, data, ttlSeconds = 300) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORES.CACHED_DATA, 'readwrite');
        const store = transaction.objectStore(storeName);

        const cacheEntry = {
            cacheKey,
            data,
            cachedAt: Date.now(),
            expiresAt: Date.now() + (ttlSeconds * 1000)
        };

        const request = store.put(cacheEntry);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
};

/**
 * Get cached response
 */
export const getCachedResponse = async (cacheKey) => {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORES.CACHED_DATA, 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.get(cacheKey);

        request.onsuccess = () => {
            const entry = request.result;
            if (entry && entry.expiresAt > Date.now()) {
                resolve(entry.data);
            } else {
                resolve(null);
            }
        };
        request.onerror = () => reject(request.error);
    });
};

/**
 * Clean up expired cache entries
 */
export const cleanupExpiredCache = async () => {
    const db = await openDatabase();
    const transaction = db.transaction(STORES.CACHED_DATA, 'readwrite');
    const store = transaction.objectStore(storeName);
    const index = store.index('expiresAt');

    const now = Date.now();
    const range = IDBKeyRange.upperBound(now);

    return new Promise((resolve) => {
        const request = index.openCursor(range);
        let deletedCount = 0;

        request.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                cursor.delete();
                deletedCount++;
                cursor.continue();
            } else {
                console.log(`🧹 Cleaned up ${deletedCount} expired cache entries`);
                resolve(deletedCount);
            }
        };
    });
};

export { STORES };
export default {
    openDatabase,
    addItem,
    getAllItems,
    getItemsByIndex,
    updateItem,
    deleteItem,
    clearStore,
    getCount,
    getPendingCount,
    cacheResponse,
    getCachedResponse,
    cleanupExpiredCache,
    STORES
};
