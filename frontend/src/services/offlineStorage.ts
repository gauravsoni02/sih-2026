type StoreName = 'instruments' | 'tests' | 'drafts' | 'reports' | 'settings';

const DB_NAME = 'nawi-offline';
const DB_VERSION = 1;
const STORES: StoreName[] = ['instruments', 'tests', 'drafts', 'reports', 'settings'];

class OfflineStorage {
  private db: IDBDatabase | null = null;
  private initPromise: Promise<void> | null = null;

  private init(): Promise<void> {
    if (this.initPromise) return this.initPromise;

    this.initPromise = new Promise((resolve, reject) => {
      try {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = () => {
          const db = request.result;
          for (const store of STORES) {
            if (!db.objectStoreNames.contains(store)) {
              db.createObjectStore(store);
            }
          }
        };

        request.onsuccess = () => {
          this.db = request.result;
          resolve();
        };

        request.onerror = () => {
          reject(request.error);
        };
      } catch {
        reject(new Error('IndexedDB not available'));
      }
    });

    return this.initPromise;
  }

  async get<T>(store: StoreName, key: string): Promise<T | null> {
    try {
      await this.init();
      if (!this.db) return this.localGet<T>(store, key);

      return new Promise((resolve) => {
        const tx = this.db!.transaction(store, 'readonly');
        const req = tx.objectStore(store).get(key);
        req.onsuccess = () => resolve(req.result ?? null);
        req.onerror = () => resolve(this.localGet<T>(store, key));
      });
    } catch {
      return this.localGet<T>(store, key);
    }
  }

  async set<T>(store: StoreName, key: string, value: T): Promise<void> {
    try {
      await this.init();
      if (!this.db) {
        this.localSet(store, key, value);
        return;
      }

      return new Promise((resolve) => {
        const tx = this.db!.transaction(store, 'readwrite');
        tx.objectStore(store).put(value, key);
        tx.oncomplete = () => resolve();
        tx.onerror = () => {
          this.localSet(store, key, value);
          resolve();
        };
      });
    } catch {
      this.localSet(store, key, value);
    }
  }

  async remove(store: StoreName, key: string): Promise<void> {
    try {
      await this.init();
      if (!this.db) {
        this.localRemove(store, key);
        return;
      }

      return new Promise((resolve) => {
        const tx = this.db!.transaction(store, 'readwrite');
        tx.objectStore(store).delete(key);
        tx.oncomplete = () => resolve();
        tx.onerror = () => resolve();
      });
    } catch {
      this.localRemove(store, key);
    }
  }

  private localKey(store: StoreName, key: string): string {
    return `${DB_NAME}:${store}:${key}`;
  }

  private localGet<T>(store: StoreName, key: string): T | null {
    try {
      const raw = localStorage.getItem(this.localKey(store, key));
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  private localSet<T>(store: StoreName, key: string, value: T): void {
    try {
      localStorage.setItem(this.localKey(store, key), JSON.stringify(value));
    } catch {
      // storage full or unavailable
    }
  }

  private localRemove(store: StoreName, key: string): void {
    try {
      localStorage.removeItem(this.localKey(store, key));
    } catch {
      // ignore
    }
  }
}

export const offlineStorage = new OfflineStorage();
