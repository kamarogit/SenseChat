'use client'

import { useState } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'

export function MessageInput() {
  const [text, setText] = useState('')
  const { sendMessage, isLoading, selectedRecipient, error, clearError } = useChatStore()
  const { currentUser } = useUserStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!text.trim() || isLoading || !currentUser || !selectedRecipient) {
      return
    }

    try {
      await sendMessage(text.trim())
      setText('')
      clearError() // エラーをクリア
    } catch (error) {
      console.error('メッセージ送信エラー:', error)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="space-y-2">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
          <button
            onClick={clearError}
            className="mt-1 text-xs text-red-500 hover:text-red-700 underline"
          >
            エラーをクリア
          </button>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="flex space-x-2">
        <div className="flex-1">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              !currentUser ? "ユーザーを選択してください" :
              !selectedRecipient ? "受信者を選択してください" :
              "メッセージを入力してください..."
            }
            className="input min-h-[40px] max-h-32 resize-none"
            rows={1}
            disabled={isLoading || !currentUser || !selectedRecipient}
          />
        </div>
        
        <button
          type="submit"
          disabled={!text.trim() || isLoading || !currentUser || !selectedRecipient}
          className="btn btn-primary px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </form>
    </div>
  )
}
