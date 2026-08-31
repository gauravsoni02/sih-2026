import apiClient from './client';
import type { Instrument, InstrumentCreatePayload } from '@/types/instrument';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function fetchInstruments(params?: Record<string, string>): Promise<PaginatedResponse<Instrument>> {
  const res = await apiClient.get<PaginatedResponse<Instrument>>('/instruments/', { params });
  return res.data;
}

export async function fetchInstrument(id: number): Promise<Instrument> {
  const res = await apiClient.get<Instrument>(`/instruments/${id}/`);
  return res.data;
}

export async function createInstrument(data: InstrumentCreatePayload): Promise<Instrument> {
  const res = await apiClient.post<Instrument>('/instruments/', data);
  return res.data;
}

export async function updateInstrument(id: number, data: Partial<InstrumentCreatePayload>): Promise<Instrument> {
  const res = await apiClient.patch<Instrument>(`/instruments/${id}/`, data);
  return res.data;
}

export async function deleteInstrument(id: number): Promise<void> {
  await apiClient.delete(`/instruments/${id}/`);
}
