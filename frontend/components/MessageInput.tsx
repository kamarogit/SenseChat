'use client'

import { useState } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'

export function MessageInput() {
  const [text, setText] = useState('')
  const { sendMessage, isLoading } = useChatStore()
  const { currentUser } = useUserStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!text.trim() || isLoading || !currentUser) {
      return
    }

    try {
      await sendMessage(text.trim())
      setText('')
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
    <form onSubmit={handleSubmit} className="flex space-x-2">
      <div className="flex-1">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="メッセージを入力してください..."
          className="input min-h-[40px] max-h-32 resize-none"
          rows={1}
          disabled={isLoading || !currentUser}
        />
      </div>
      
      <button
        type="submit"
        disabled={!text.trim() || isLoading || !currentUser}
        className="btn btn-primary px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </button>
    </form>
  )
}
