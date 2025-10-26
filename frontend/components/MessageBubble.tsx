'use client'

import { Message } from '@/stores/chatStore'
import { Check, CheckCheck, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'

interface MessageBubbleProps {
  message: Message
  isOwn: boolean
}

export function MessageBubble({ message, isOwn }: MessageBubbleProps) {
  const getStatusIcon = () => {
    switch (message.status) {
      case 'sent':
        return <Check className="h-3 w-3 text-gray-400" />
      case 'delivered':
        return <CheckCheck className="h-3 w-3 text-gray-400" />
      case 'read':
        return <CheckCheck className="h-3 w-3 text-blue-600" />
      default:
        return <Clock className="h-3 w-3 text-gray-400" />
    }
  }

  const formatTime = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), {
        addSuffix: true,
        locale: ja
      })
    } catch {
      return '今'
    }
  }

  // 一般的なチャットアプリのルール:
  // - 右側（青色）: 自分が送信したメッセージ (isOwn = true)
  // - 左側（白色）: 相手から受信したメッセージ (isOwn = false)
  
  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-xs lg:max-w-md`}>
        {/* メッセージバブル */}
        <div
          className={`message-bubble ${
            isOwn ? 'message-sent' : 'message-received'
          }`}
        >
          <p className="text-sm leading-relaxed">{message.text}</p>
          
          {/* 要約がある場合 */}
          {message.summary && message.summary !== message.text && (
            <div className={`mt-2 p-2 rounded text-xs ${
              isOwn ? 'bg-white bg-opacity-20' : 'bg-gray-100'
            }`}>
              <p className="font-medium mb-1">要約:</p>
              <p>{message.summary}</p>
            </div>
          )}
        </div>
        
        {/* メタ情報 */}
        <div className={`flex items-center mt-1 space-x-1 ${
          isOwn ? 'justify-end' : 'justify-start'
        }`}>
          <span className="text-xs text-gray-500">
            {formatTime(message.created_at)}
          </span>
          
          {isOwn && (
            <div className="flex items-center">
              {getStatusIcon()}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
