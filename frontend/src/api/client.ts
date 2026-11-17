import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export class ApiError extends Error {
  status?: number
  code?: string | number

  constructor(message: string, status?: number, code?: string | number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export interface PageData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface ScienceKnowledgeItem {
  id: string
  title: string
  summary: string
  category: string
  keywords: string[]
  readingMinutes?: number
  updatedAt?: string
}

export interface ScienceResourceItem {
  id: string
  title: string
  description: string
  format: 'article' | 'course' | 'experiment' | 'video' | 'dataset'
  topic: string
  level?: '入门' | '进阶' | '拓展'
  estimatedMinutes?: number
}

export interface ExperimentRun {
  id: string
  experimentId: string
  variables: Record<string, number | string | boolean>
  observations: string[]
  createdAt: string
}

export interface RecognitionRecord {
  id: string
  label: string
  confidence: number
  threshold: number
  createdAt: string
  note?: string
}

export interface ScienceSource {
  id: string
  title: string
  organization: string
  publishedAt?: string
  url: string
  summary?: string
}

export interface ChatAnalyzeResponse {
  answer: string
  references: ScienceSource[]
  followUpQuestions?: string[]
  generatedAt?: string
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  response: string
  sessionId: string
  timestamp: string
  persisted: boolean
}

type ApiEnvelope<T> = {
  code?: string | number
  message?: string
  data?: T
}

function errorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiEnvelope<unknown>>(error)) {
    const body = error.response?.data
    const detail = body?.message || (typeof body?.data === 'string' ? body.data : undefined)
    return detail || error.message || `请求失败(${error.response?.status ?? 'NETWORK'})`
  }
  return error instanceof Error ? error.message : '请求失败，请稍后重试'
}

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    const response: AxiosResponse<T | ApiEnvelope<T>> = await axios.request({
      baseURL: BASE_URL,
      timeout: 20000,
      ...config,
    })
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body) {
      const envelope = body as ApiEnvelope<T>
      if (envelope.code !== undefined && envelope.code !== 0 && envelope.code !== 'SUCCESS') {
        throw new ApiError(envelope.message || '请求失败', response.status, envelope.code)
      }
      return envelope.data as T
    }
    return body as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (axios.isAxiosError(error)) {
      const envelope = error.response?.data as ApiEnvelope<unknown> | undefined
      throw new ApiError(errorMessage(error), error.response?.status, envelope?.code)
    }
    throw new ApiError(errorMessage(error))
  }
}

export function toQuery(params: Record<string, unknown>): string {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    if (Array.isArray(value)) {
      value.forEach((item) => query.append(key, String(item)))
      return
    }
    query.set(key, String(value))
  })
  return query.toString()
}

export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function download(path: string, filename: string, params?: Record<string, unknown>): Promise<void> {
  const query = params ? toQuery(params) : ''
  const blob = await request<Blob>({
    url: query ? `${path}?${query}` : path,
    method: 'GET',
    responseType: 'blob',
  })
  saveBlob(blob, filename)
}

export const scienceApi = {
  ask: (data: { question: string; audience?: string; context?: string[] }) =>
    request<ChatAnalyzeResponse>({
      url: '/v1/science/ask',
      method: 'POST',
      data,
    }),
  runExperiment: (experimentId: string, variables: ExperimentRun['variables']) =>
    request<ExperimentRun>({
      url: `/v1/science/experiments/${experimentId}/runs`,
      method: 'POST',
      data: { variables },
    }),
  recognize: (file: File) => {
    const form = new FormData()
    form.append('image', file)
    return request<RecognitionRecord>({
      url: '/v1/science/recognition',
      method: 'POST',
      data: form,
    })
  },
  searchSources: (keyword: string, page = 1, pageSize = 10) =>
    request<PageData<ScienceSource>>({
      url: `/v1/science/sources?${toQuery({ keyword, page, pageSize })}`,
      method: 'GET',
    }),
}

export const chatApi = {
  analyze: (data: {
    message: string
    sessionId: string
    history: ChatHistoryMessage[]
  }) =>
    request<ChatResponse>({
      url: '/v1/chat/analyze',
      method: 'POST',
      data,
      timeout: 90000,
    }),
  clearHistory: (sessionId: string) =>
    request<{ sessionId: string; deleted: number }>({
      url: `/v1/chat/history/${encodeURIComponent(sessionId)}`,
      method: 'DELETE',
    }),
}
