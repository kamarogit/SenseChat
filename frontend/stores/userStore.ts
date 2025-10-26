import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface User {
  id: string
  name: string
  language: string
  style_preset: string
}

interface UserState {
  currentUser: User | null
  availableUsers: User[]
  isLoading: boolean
  error: string | null
  
  // Actions
  setCurrentUser: (user: User) => void
  loadUsers: () => Promise<void>
  clearError: () => void
}

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      currentUser: null,
      availableUsers: [],
      isLoading: false,
      error: null,
      
      setCurrentUser: (user) => {
        set({ currentUser: user })
      },
      
      loadUsers: async () => {
        set({ isLoading: true, error: null })
        
        try {
          const apiUrl = 'http://localhost:8000'
          console.log('🔍 loadUsers: API URL:', apiUrl)
          const response = await fetch(`${apiUrl}/api/v1/users/`)
          console.log('🔍 loadUsers: レスポンス受信', response.status, response.url)
          
          if (!response.ok) {
            throw new Error(`ユーザー情報の取得に失敗しました: ${response.status}`)
          }
          
          const data = await response.json()
          console.log('🔍 loadUsers: データ受信', data)
          set({ availableUsers: data || [] })
          
        } catch (error) {
          console.error('❌ ユーザー読み込みエラー:', error)
          set({ error: error instanceof Error ? error.message : '不明なエラー' })
        } finally {
          set({ isLoading: false })
        }
      },
      
      clearError: () => {
        set({ error: null })
      }
    }),
    {
      name: 'sensechat-user',
      partialize: (state) => ({ currentUser: state.currentUser })
    }
  )
)
