'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, UserRole, Notification } from '@/types';
import { authApi, LoginResponse } from '@/lib/api';

// ===== Auth Store =====
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  loginWithCredentials: (email: string, password: string) => Promise<boolean>;
  loginAsRole: (role: UserRole) => Promise<boolean>;
  logout: () => void;
  setError: (err: string | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      loginWithCredentials: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const res: LoginResponse = await authApi.login(email, password);
          const rawRole = res.user?.role || res.role || 'moderator';
          const role: UserRole =
            (rawRole === 'admin' || rawRole === 'authority' || email === 'admin@safety.gov.in')
              ? 'authority'
              : 'moderator';

          const mappedUser: User = {
            id: res.user?.id || res.user_id || `user-${Date.now()}`,
            name: res.user?.full_name || res.full_name || (email.split('@')[0]),
            email: res.user?.email || res.email || email,
            role,
            department: role === 'authority' ? 'Law Enforcement / CWC' : 'Child Protection Division',
            assignedChildren: 12,
          };

          if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', res.access_token);
            localStorage.setItem('refresh_token', res.refresh_token);
          }

          set({
            user: mappedUser,
            accessToken: res.access_token,
            refreshToken: res.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
          return true;
        } catch (err: any) {
          const message = err.response?.data?.detail || 'Authentication failed. Please check your credentials.';
          set({ error: message, isLoading: false });
          return false;
        }
      },

      loginAsRole: async (role: UserRole) => {
        set({ isLoading: true, error: null });
        // Seeded credentials matching section 3 of BACKEND_CONTEXT_FOR_REACT_PORTAL.txt
        let email = 'moderator@safety.gov.in';
        let password = 'Moderator@123';

        if (role === 'admin' || role === 'authority') {
          email = 'admin@safety.gov.in';
          password = 'Admin@123';
        }

        try {
          const success = await get().loginWithCredentials(email, password);
          if (success) {
            const current = get().user;
            if (current && (role === 'authority' || role === 'admin')) {
              set({ user: { ...current, role } });
            }
            return true;
          }
        } catch (e) {
          console.warn('[AuthStore] Backend login failed');
        }

        set({ error: 'Login failed. Please check your credentials.', isLoading: false });
        return false;
      },

      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        });
      },

      setError: (err) => set({ error: err }),
    }),
    {
      name: 'auth-storage-v2',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// ===== Notification Store =====
interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  setNotifications: (items: Notification[]) => void;
  addNotification: (n: Notification) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  setNotifications: (items) =>
    set({
      notifications: items,
      unreadCount: items.filter((n) => !n.read).length,
    }),
  addNotification: (n) =>
    set((state) => ({
      notifications: [n, ...state.notifications],
      unreadCount: state.unreadCount + (n.read ? 0 : 1),
    })),
  markAsRead: (id: string) =>
    set((state) => {
      const updated = state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      );
      return {
        notifications: updated,
        unreadCount: updated.filter((n) => !n.read).length,
      };
    }),
  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),
}));

// ===== UI Store =====
interface UIState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
}));
