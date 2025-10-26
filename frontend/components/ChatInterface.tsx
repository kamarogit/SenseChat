'use client'

import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import { MessageBubble } from './MessageBubble'
import { Loader2, ChevronDown, UserPlus } from 'lucide-react'

export function ChatInterface() {
  const { messages, isLoading, error, selectedRecipient, setSelectedRecipient, clearMessages, loadUserChatHistory, saveUserChatHistory } = useChatStore()
  const { currentUser, availableUsers, loadUsers } = useUserStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showRecipientSelector, setShowRecipientSelector] = useState(false)

  // ユーザー一覧を読み込む
  useEffect(() => {
    if (availableUsers.length === 0) {
      loadUsers()
    }
  }, [availableUsers.length, loadUsers])


  // メッセージが更新されたら自動スクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-2">エラーが発生しました</p>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

         const handleRecipientChange = (user: any) => {
           // 現在のチャット履歴を保存
           if (currentUser && selectedRecipient) {
             saveUserChatHistory(currentUser.id, selectedRecipient)
           }
           
           setSelectedRecipient(user.id)
           setShowRecipientSelector(false)
           
           // 新しいチャット相手との履歴を読み込み
           if (currentUser) {
             loadUserChatHistory(currentUser.id, user.id)
           }
         }

         const getRecipientName = () => {
           if (!selectedRecipient) return 'チャット相手を選択'
           const recipient = availableUsers.find(u => u.id === selectedRecipient)
           return recipient ? recipient.name : 'チャット相手を選択'
         }

  return (
    <div className="flex flex-col h-96 relative">
      {/* チャットヘッダー */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <UserPlus className="h-5 w-5 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">チャット相手:</span>
            <button
              onClick={() => setShowRecipientSelector(!showRecipientSelector)}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-100 hover:bg-blue-200 rounded-lg transition-colors"
            >
              <span className="text-sm font-medium">{getRecipientName()}</span>
              <ChevronDown className="h-4 w-4 text-gray-600" />
            </button>
          </div>
        </div>
        
        {/* チャット相手選択ドロップダウン */}
        {showRecipientSelector && (
          <div className="absolute left-0 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
            <div className="py-1">
              {availableUsers.length === 0 ? (
                <div className="px-4 py-2 text-sm text-gray-500">
                  ユーザーを読み込み中...
                </div>
              ) : (
                availableUsers
                  .filter(user => user.id !== currentUser?.id) // 自分以外を表示
                  .map((user) => (
                    <button
                      key={user.id}
                      onClick={() => handleRecipientChange(user)}
                      className={`w-full text-left px-4 py-3 text-sm hover:bg-gray-100 transition-colors ${
                        selectedRecipient === user.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                      }`}
                    >
                      <div className="font-medium">{user.name}</div>
                      <div className="text-xs text-gray-500">
                        {user.language === 'ja' ? '日本語' : 'English'} • {user.style_preset}
                      </div>
                    </button>
                  ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* メッセージリスト */}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50 rounded-lg">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-gray-500 mb-2">まだメッセージがありません</p>
              <p className="text-sm text-gray-400">
                下の入力欄からメッセージを送信してください
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isOwn={message.sender_id === currentUser?.id}
              />
            ))}
          </div>
        )}
        
        {isLoading && (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2 text-sm text-gray-600">処理中...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}
