// Offline Sync Queue for field workers
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from './api';

const QUEUE_KEY = 'aanchal_offline_queue';

export async function getQueue() {
    try {
        const raw = await AsyncStorage.getItem(QUEUE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch { return []; }
}

export async function addToQueue(action) {
    const queue = await getQueue();
    queue.push({ ...action, id: Date.now().toString(), createdAt: new Date().toISOString() });
    await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

export async function removeFromQueue(id) {
    const queue = await getQueue();
    const filtered = queue.filter((a) => a.id !== id);
    await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(filtered));
}

export async function syncQueue(onProgress) {
    const queue = await getQueue();
    if (!queue.length) return { synced: 0, failed: 0 };
    let synced = 0;
    let failed = 0;
    for (const action of queue) {
        try {
            await api({ method: action.method, url: action.url, data: action.data });
            await removeFromQueue(action.id);
            synced++;
            onProgress?.({ synced, failed, total: queue.length });
        } catch {
            failed++;
        }
    }
    return { synced, failed };
}
