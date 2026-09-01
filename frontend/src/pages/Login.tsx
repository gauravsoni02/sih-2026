import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Form, Input, Button } from 'antd';
import { login } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { getMe } from '@/api/auth';

export default function Login() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    setError('');
    try {
      const tokens = await login(values);
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      const user = await getMe();
      // Drop everything cached for the previous account, then seed the
      // fresh profile so useAuth's ['me'] query can't resurrect stale data.
      queryClient.clear();
      queryClient.setQueryData(['me'], user);
      setUser(user);
      navigate('/');
    } catch (err: unknown) {
      if (isAxiosError(err) && err.response?.status === 401) {
        setError('Invalid username or password');
      } else {
        setError('Cannot reach the server — it may be waking up (can take ~60s on free hosting). Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: '#ffffff',
    }}>
      <div style={{ width: 320 }}>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: '#1a1a1a', marginBottom: 32, textAlign: 'center' }}>
          NAWI Test Report Generator
        </h1>
        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            label="Username"
            name="username"
            rules={[{ required: true, message: 'Username is required' }]}
          >
            <Input size="large" autoFocus />
          </Form.Item>
          <Form.Item
            label="Password"
            name="password"
            rules={[{ required: true, message: 'Password is required' }]}
          >
            <Input.Password size="large" />
          </Form.Item>
          {error && (
            <div style={{ color: '#cf1322', fontSize: 12, marginBottom: 16 }}>{error}</div>
          )}
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              Sign in
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  );
}
