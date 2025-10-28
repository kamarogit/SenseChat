import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { useUserStore } from './userStore'
import { websocketClient, NewMessage, UserStatus, TypingStatus } from '../lib/websocket'

export interface Message {
  id: string
  sender_id: string
  text: string  // 送信者: 元のテキスト、受信者: 再構成されたテキスト
  summary?: string  // 要約（サーバーから取得）
  created_at: string
  status: 'sent' | 'delivered' | 'read' | 'received'
  message_type: 'sent' | 'received'  // メッセージの種類
}

interface ChatState {
  messages: Message[]
  currentThread: string | null
  selectedRecipient: string | null // 受信者選択
  isLoading: boolean
  error: string | null
  
  // WebSocket関連
  isWebSocketConnected: boolean
  onlineUsers: string[]
  typingUsers: Record<string, boolean> // user_id -> is_typing
  
  // クライアント側保存: 送信者と受信者で分離
  sentMessages: Record<string, Message[]> // key: "user1_user2", value: 送信者のメッセージ
  receivedMessages: Record<string, Message[]> // key: "user1_user2", value: 受信者のメッセージ
  
  // Actions
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  loadMessages: () => Promise<void>
  sendMessage: (text: string) => Promise<void>
  setSelectedRecipient: (recipientId: string) => void
  clearError: () => void
  clearMessages: () => void
  
  // サーバー側永続化対応
  loadUserChatHistory: (currentUserId: string, recipientId: string) => void
  saveSentMessage: (currentUserId: string, recipientId: string, message: Message) => void
  saveReceivedMessage: (currentUserId: string, recipientId: string, message: Message) => void
  syncFromServer: (currentUserId: string, recipientId?: string) => Promise<void>
  
  // WebSocket関連
  connectWebSocket: (userId: string) => Promise<void>
  disconnectWebSocket: () => void
  sendTypingStatus: (isTyping: boolean, recipientId?: string) => void
  markMessageAsRead: (messageId: string, senderId: string) => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      currentThread: null,
      selectedRecipient: null, // 受信者未選択
      isLoading: false,
      error: null,
      
      // WebSocket関連
      isWebSocketConnected: false,
      onlineUsers: [],
      typingUsers: {},
      
      sentMessages: {}, // 送信者のメッセージ
      receivedMessages: {}, // 受信者のメッセージ
      
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
          // ユーザーが選択されていない場合は空のメッセージリストを設定
          const { currentUser } = get()
          if (!currentUser) {
            set({ messages: [], isLoading: false })
            return
          }
          
          const apiUrl = 'http://localhost:8000'
          const response = await fetch(`${apiUrl}/api/v1/threads/current/messages/`, {
            headers: {
              'X-User-ID': currentUser.id
            }
          })
          
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
            text: text,
            summary: embedData.summary,
            created_at: embedData.created_at || new Date().toISOString(),
            status: 'sent',
            message_type: 'sent'
          }
          
          // 送信者のメッセージをクライアント側に保存
          get().saveSentMessage(currentUser.id, selectedRecipient, sentMessage)
          
          // UIに表示
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
          
          // 受信者側への表示は WebSocket 通知（new_message）に任せる
          
          console.log('🎉 SenseChat MVP: 完全なフロー完了')
          
          // 6. チャット履歴を自動保存（クライアント側）
          // 送信者と受信者のメッセージは既に個別に保存済み
          
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
        const sentHistory = get().sentMessages[chatKey] || []
        const receivedHistory = get().receivedMessages[chatKey] || []
        
        // 送信者と受信者のメッセージを統合して時系列でソート
        const allMessages = [...sentHistory, ...receivedHistory].sort(
          (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        )
        
        console.log(`📚 チャット履歴を読み込み: ${chatKey}`, {
          sent: sentHistory.length,
          received: receivedHistory.length,
          total: allMessages.length
        })
        
        set({ messages: allMessages })
      },

      saveSentMessage: (currentUserId: string, recipientId: string, message: Message) => {
        const chatKey = [currentUserId, recipientId].sort().join('_')
        console.log(`💾 送信メッセージを保存: ${chatKey}`, message.id)
        set((state) => ({
          sentMessages: {
            ...state.sentMessages,
            [chatKey]: [...(state.sentMessages[chatKey] || []), message]
          }
        }))
      },

      saveReceivedMessage: (currentUserId: string, recipientId: string, message: Message) => {
        const chatKey = [currentUserId, recipientId].sort().join('_')
        console.log(`💾 受信メッセージを保存: ${chatKey}`, message.id)
        set((state) => ({
          receivedMessages: {
            ...state.receivedMessages,
            [chatKey]: [...(state.receivedMessages[chatKey] || []), message]
          }
        }))
      },

      // サーバーからの履歴同期
      syncFromServer: async (currentUserId: string, recipientId?: string) => {
        try {
          console.log('🔄 サーバーから履歴を同期中...', { currentUserId, recipientId })
          
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          const url = recipientId 
            ? `${apiUrl}/api/v1/messages/history?recipient_id=${recipientId}`
            : `${apiUrl}/api/v1/messages/history`
          
          const response = await fetch(url, {
            headers: {
              'X-User-ID': currentUserId
            }
          })
          
          if (!response.ok) {
            throw new Error(`サーバー同期エラー: ${response.status}`)
          }
          
          const data = await response.json()
          console.log('📥 サーバーから履歴を受信:', data.messages.length, '件')
          
          // サーバーからのメッセージをクライアント側ストアに統合
          const serverMessages: Message[] = data.messages.map((msg: any) => ({
            id: msg.id,
            sender_id: msg.user_id,
            text: msg.text,
            created_at: msg.created_at,
            status: 'read' as const,
            message_type: msg.content_type === 'original' ? 'sent' as const : 'received' as const
          }))
          
          // 既存のクライアント側メッセージと統合
          const { sentMessages, receivedMessages } = get()
          const allClientMessages = [
            ...Object.values(sentMessages).flat(),
            ...Object.values(receivedMessages).flat()
          ]
          
          // 重複を除去して統合
          const allMessages = [...allClientMessages, ...serverMessages]
            .filter((msg, index, arr) => 
              arr.findIndex(m => m.id === msg.id) === index
            )
            .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
          
          set({ messages: allMessages })
          console.log('✅ サーバー同期完了:', allMessages.length, '件')
          
        } catch (error) {
          console.error('❌ サーバー同期エラー:', error)
          // エラーが発生してもクライアント側のデータは保持
        }
      },
      
      // WebSocket関連のアクション
      connectWebSocket: async (userId: string) => {
        try {
          console.log('🔌 WebSocket接続を開始:', userId)
          
          // WebSocketイベントハンドラーを設定
          websocketClient.onMessage('new_message', (data: NewMessage) => {
            console.log('📨 新しいメッセージを受信:', data)
            
            // 受信メッセージをチャットに追加
            const message: Message = {
              id: data.message_id,
              sender_id: data.sender_id,
              text: data.text,
              summary: data.summary,
              created_at: data.created_at,
              status: 'received',
              message_type: 'received'
            }
            
            get().addMessage(message)
            
            // クライアント側に保存
            get().saveReceivedMessage(userId, data.sender_id, message)
          })
          
          websocketClient.onMessage('message_delivered', (data) => {
            console.log('✅ メッセージ配信確認:', data)
            // メッセージのステータスを更新
            get().updateMessage(data.message_id, { status: 'delivered' })
          })
          
          websocketClient.onMessage('message_read', (data) => {
            console.log('👁️ メッセージ既読確認:', data)
            // メッセージのステータスを更新
            get().updateMessage(data.message_id, { status: 'read' })
          })
          
          websocketClient.onMessage('user_status', (data: UserStatus) => {
            console.log('👤 ユーザー状態変更:', data)
            
            set((state) => {
              const onlineUsers = [...state.onlineUsers]
              if (data.status === 'online' && !onlineUsers.includes(data.user_id)) {
                onlineUsers.push(data.user_id)
              } else if (data.status === 'offline') {
                const index = onlineUsers.indexOf(data.user_id)
                if (index > -1) {
                  onlineUsers.splice(index, 1)
                }
              }
              
              return { onlineUsers }
            })
          })
          
          websocketClient.onMessage('user_typing', (data: TypingStatus) => {
            console.log('⌨️ タイピング状態:', data)
            
            set((state) => ({
              typingUsers: {
                ...state.typingUsers,
                [data.user_id]: data.is_typing
              }
            }))
          })
          
          websocketClient.onMessage('online_users', (data) => {
            console.log('👥 オンラインユーザー一覧:', data.users)
            set({ onlineUsers: data.users })
          })
          
          websocketClient.onStatus('connection_established', (data) => {
            console.log('✅ WebSocket接続確立:', data)
            set({ isWebSocketConnected: true })
          })
          
          // WebSocket接続を開始
          await websocketClient.connect(userId)
          
        } catch (error) {
          console.error('❌ WebSocket接続エラー:', error)
          set({ error: 'WebSocket接続に失敗しました' })
        }
      },
      
      disconnectWebSocket: () => {
        console.log('🔌 WebSocket接続を切断')
        websocketClient.disconnect()
        set({ 
          isWebSocketConnected: false,
          onlineUsers: [],
          typingUsers: {}
        })
      },
      
      sendTypingStatus: (isTyping: boolean, recipientId?: string) => {
        if (get().isWebSocketConnected) {
          websocketClient.sendTypingStatus(isTyping, recipientId)
        }
      },
      
      markMessageAsRead: (messageId: string, senderId: string) => {
        if (get().isWebSocketConnected) {
          websocketClient.sendMessageRead(messageId, senderId)
        }
      }
    }),
    {
      name: 'sensechat-messages',
      partialize: (state) => ({ 
        messages: state.messages,
        sentMessages: state.sentMessages,
        receivedMessages: state.receivedMessages
      })
    }
  )
)
