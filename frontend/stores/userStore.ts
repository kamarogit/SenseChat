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
          const response = await fetch('/api/v1/users')
          
          if (!response.ok) {
            throw new Error('ユーザー情報の取得に失敗しました')
          }
          
          const data = await response.json()
          set({ availableUsers: data.users || [] })
          
        } catch (error) {
          console.error('ユーザー読み込みエラー:', error)
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
