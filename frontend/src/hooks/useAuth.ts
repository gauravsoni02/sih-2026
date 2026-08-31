import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { getMe } from '@/api/auth';

export function useAuth() {
  const { user, isAuthenticated, setUser, logout } = useAuthStore();

  const { data, isLoading, error } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    enabled: isAuthenticated && !user,
    retry: false,
  });

  useEffect(() => {
    if (data) setUser(data);
  }, [data, setUser]);

  useEffect(() => {
    if (error) logout();
  }, [error, logout]);

  return { user, isAuthenticated, isLoading, logout };
}
