import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { useUserStore } from './userStore'

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
  selectedRecipient: string | null // 受信者選択
  isLoading: boolean
  error: string | null
  // ユーザー間のメッセージ履歴を管理
  userChatHistory: Record<string, Message[]> // key: "user1_user2", value: messages[]
  
  // Actions
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  loadMessages: () => Promise<void>
  sendMessage: (text: string) => Promise<void>
  setSelectedRecipient: (recipientId: string) => void
  clearError: () => void
  clearMessages: () => void
  loadUserChatHistory: (currentUserId: string, recipientId: string) => void
  saveUserChatHistory: (currentUserId: string, recipientId: string) => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      currentThread: null,
      selectedRecipient: null, // 受信者未選択
      isLoading: false,
      error: null,
      userChatHistory: {}, // ユーザー間のチャット履歴
      
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
                 const apiUrl = 'http://localhost:8000'
                 const response = await fetch(`${apiUrl}/api/v1/threads/current/messages/`)
                 
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
          const apiUrl = 'http://localhost:8000'
          // currentUserは外部から取得する必要がある
          const { currentUser } = useUserStore.getState()
          if (!currentUser) {
            throw new Error('ユーザーが選択されていません')
          }
          const selectedRecipient = get().selectedRecipient
          
          // 受信者が選択されていない場合はエラー
          if (!selectedRecipient) {
            throw new Error('受信者を選択してください')
          }
          
          console.log('🚀 SenseChat MVP: メッセージ送信開始', { 
            text, 
            sender: currentUser.id, 
            recipient: selectedRecipient 
          })
          
          // 1. Embedding処理（要約・ベクトル化）
          console.log('📝 Step 1: Embedding処理（要約・ベクトル化）')
          const embedResponse = await fetch(`${apiUrl}/api/v1/embed/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-User-ID': currentUser.id
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
          console.log('✅ Step 1完了:', { summary: embedData.summary, vector_id: embedData.vector_id })
          
          // 2. 送信者側のメッセージ表示（元のテキスト）
          const sentMessage: Message = {
            id: embedData.message_id,
            sender_id: currentUser.id,
            text: text, // 元のテキストを表示
            created_at: new Date().toISOString(),
            status: 'sent'
          }
          
          set((state) => ({
            messages: [...state.messages, sentMessage]
          }))
          
          // 3. 配信処理（選択された受信者にのみ配信）
          console.log('📤 Step 2: 配信処理')
          const deliverResponse = await fetch(`${apiUrl}/api/v1/deliver/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-User-ID': currentUser.id
            },
            body: JSON.stringify({
              to_user_id: selectedRecipient, // 選択された受信者
              message_id: embedData.message_id,
              thread_id: get().currentThread || 'default'
            })
          })
          
          if (!deliverResponse.ok) {
            throw new Error('メッセージの配信に失敗しました')
          }
          
          console.log('✅ Step 2完了: 配信成功')
          
          // 4. 受信者側での意味検索・LLM再構成
          console.log('🔍 Step 3: 意味検索・LLM再構成')
          const renderResponse = await fetch(`${apiUrl}/api/v1/render`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-User-ID': selectedRecipient // 選択された受信者のID
            },
            body: JSON.stringify({
              message_id: embedData.message_id,
              recipient_id: selectedRecipient // 選択された受信者のID
            })
          })
          
          if (!renderResponse.ok) {
            throw new Error('メッセージの再構成に失敗しました')
          }
          
          const renderData = await renderResponse.json()
          console.log('✅ Step 3完了:', { 
            original: text, 
            reconstructed: renderData.text,
            style_applied: renderData.style_applied,
            confidence: renderData.confidence
          })
          
          // 5. 受信者側のメッセージ表示（再構成されたテキスト）
          // 受信者のメッセージは左側に表示するため、sender_idを受信者に設定
          const receivedMessage: Message = {
            id: `rec_${embedData.message_id}`,
            sender_id: selectedRecipient, // 受信者として表示（左側に配置）
            text: renderData.text, // 再構成されたテキスト
            created_at: new Date().toISOString(),
            status: 'received'
          }
          
          set((state) => ({
            messages: [...state.messages, receivedMessage]
          }))
          
          console.log('🎉 SenseChat MVP: 完全なフロー完了')
          
        } catch (error) {
          console.error('❌ メッセージ送信エラー:', error)
          set({ error: error instanceof Error ? error.message : '不明なエラー' })
        } finally {
          set({ isLoading: false })
        }
      },
      
      setSelectedRecipient: (recipientId: string) => {
        set({ selectedRecipient: recipientId })
      },

      clearError: () => {
        set({ error: null })
      },

      clearMessages: () => {
        set({ messages: [] })
      },

      loadUserChatHistory: (currentUserId: string, recipientId: string) => {
        const chatKey = [currentUserId, recipientId].sort().join('_')
        const history = get().userChatHistory[chatKey] || []
        set({ messages: history })
      },

      saveUserChatHistory: (currentUserId: string, recipientId: string) => {
        const chatKey = [currentUserId, recipientId].sort().join('_')
        const currentMessages = get().messages
        set((state) => ({
          userChatHistory: {
            ...state.userChatHistory,
            [chatKey]: currentMessages
          }
        }))
      }
    }),
    {
      name: 'sensechat-messages',
      partialize: (state) => ({ 
        messages: state.messages,
        userChatHistory: state.userChatHistory 
      })
    }
  )
)
