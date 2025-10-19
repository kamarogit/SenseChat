import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Message {
  id: string
  sender_id: string
  text: string
  summary?: string
  created_at: string
  status: 'sent' | 'delivered' | 'read'
}

interface ChatState {
  messages: Message[]
  currentThread: string | null
  isLoading: boolean
  error: string | null
  
  // Actions
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  loadMessages: () => Promise<void>
  sendMessage: (text: string) => Promise<void>
  clearError: () => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      currentThread: null,
      isLoading: false,
      error: null,
      
      addMessage: (message) => {
        set((state) => ({
          messages: [...state.messages, message]
        }))
      },
      
      updateMessage: (id, updates) => {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, ...updates } : msg
          )
        }))
      },
      
      loadMessages: async () => {
        set({ isLoading: true, error: null })
        
        try {
          // 実際のAPI呼び出し
          const response = await fetch('/api/v1/threads/current/messages')
          
          if (!response.ok) {
            throw new Error('メッセージの読み込みに失敗しました')
          }
          
          const data = await response.json()
          set({ messages: data.messages || [] })
          
        } catch (error) {
          console.error('メッセージ読み込みエラー:', error)
          set({ error: error instanceof Error ? error.message : '不明なエラー' })
        } finally {
          set({ isLoading: false })
        }
      },
      
      sendMessage: async (text: string) => {
        set({ isLoading: true, error: null })
        
        try {
          // 1. Embedding処理
          const embedResponse = await fetch('/api/v1/embed', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-User-ID': 'user_1' // 実際の実装では動的に設定
            },
            body: JSON.stringify({
              text,
              lang_hint: 'auto'
            })
          })
          
          if (!embedResponse.ok) {
            throw new Error('メッセージの処理に失敗しました')
          }
          
          const embedData = await embedResponse.json()
          
          // 2. 一時的なメッセージを追加
          const tempMessage: Message = {
            id: `temp_${Date.now()}`,
            sender_id: 'user_1',
            text,
            summary: embedData.summary,
            created_at: new Date().toISOString(),
            status: 'sent'
          }
          
          set((state) => ({
            messages: [...state.messages, tempMessage]
          }))
          
          // 3. 配信処理
          const deliverResponse = await fetch('/api/v1/deliver', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-User-ID': 'user_1'
            },
            body: JSON.stringify({
              to_user_id: 'user_2', // 実際の実装では動的に設定
              message_id: embedData.message_id,
              thread_id: get().currentThread || 'default'
            })
          })
          
          if (!deliverResponse.ok) {
            throw new Error('メッセージの配信に失敗しました')
          }
          
          // 4. メッセージの状態を更新
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === tempMessage.id
                ? { ...msg, id: embedData.message_id, status: 'delivered' }
                : msg
            )
          }))
          
        } catch (error) {
          console.error('メッセージ送信エラー:', error)
          set({ error: error instanceof Error ? error.message : '不明なエラー' })
          
          // エラー時は一時メッセージを削除
          set((state) => ({
            messages: state.messages.filter((msg) => !msg.id.startsWith('temp_'))
          }))
        } finally {
          set({ isLoading: false })
        }
      },
      
      clearError: () => {
        set({ error: null })
      }
    }),
    {
      name: 'sensechat-messages',
      partialize: (state) => ({ messages: state.messages })
    }
  )
)
