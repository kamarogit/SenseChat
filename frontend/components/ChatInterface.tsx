'use client'

import { useEffect, useRef } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import { MessageBubble } from './MessageBubble'
import { Loader2 } from 'lucide-react'

export function ChatInterface() {
  const { messages, isLoading, error } = useChatStore()
  const { currentUser } = useUserStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  return (
    <div className="flex flex-col h-96">
      {/* メッセージリスト */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-gray-50 rounded-lg">
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
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              isOwn={message.sender_id === currentUser?.id}
            />
          ))
        )}
        
        {isLoading && (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
            <span className="ml-2 text-sm text-gray-600">処理中...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}
