import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { useAuthStore } from '@/store/authStore';
import { getMe } from '@/api/auth';

export function useAuth() {
  const { user, isAuthenticated, setUser, logout } = useAuthStore();

  const { data, isLoading, error } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    enabled: isAuthenticated && !user,
    retry: 2,
  });

  useEffect(() => {
    if (data) setUser(data);
  }, [data, setUser]);

  useEffect(() => {
    // Only log out on a definitive auth rejection. A network error (server
    // cold-starting, connection dropped) must never wipe the session.
    if (
      isAxiosError(error) &&
      (error.response?.status === 401 || error.response?.status === 403)
    ) {
      logout();
    }
  }, [error, logout]);

  return { user, isAuthenticated, isLoading, logout };
}
