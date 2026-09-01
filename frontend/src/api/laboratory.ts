import apiClient from './client';

export interface Laboratory {
  id: number;
  name: string;
  address: string;
  accreditation_number: string;
  lab_code: string;
  contact_person: string;
}

export async function fetchLaboratories(): Promise<Laboratory[]> {
  const res = await apiClient.get<{ results: Laboratory[] }>('/laboratories/', { params: { page_size: '100' } });
  return res.data.results;
}

export async function updateLaboratory(id: number, data: Partial<Laboratory>): Promise<Laboratory> {
  const res = await apiClient.patch<Laboratory>(`/laboratories/${id}/`, data);
  return res.data;
}
