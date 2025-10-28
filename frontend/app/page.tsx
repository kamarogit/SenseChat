'use client'

import { useState, useEffect } from 'react'
import { MessageCircle, Users, Settings, Send, ChevronDown } from 'lucide-react'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import { ChatInterface } from '@/components/ChatInterface'
import { UserSelector } from '@/components/UserSelector'
import { MessageInput } from '@/components/MessageInput'

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(true)
  const [showUserSelector, setShowUserSelector] = useState(false)
  const { currentUser, setCurrentUser, availableUsers, loadUsers } = useUserStore()
  const { messages, loadMessages, clearMessages, loadUserChatHistory, saveUserChatHistory, connectWebSocket, disconnectWebSocket, isWebSocketConnected } = useChatStore()

  useEffect(() => {
    // 初期化処理
    const initializeApp = async () => {
      try {
        // ユーザー情報の取得
        await loadUsers()
        
        // メッセージの読み込み
        await loadMessages()
        
      } catch (error) {
        console.error('初期化エラー:', error)
      } finally {
        setIsLoading(false)
      }
    }

    initializeApp()
    
    // クリーンアップ
    return () => {
      disconnectWebSocket()
    }
  }, [setCurrentUser, loadUsers, loadMessages, disconnectWebSocket])

  // 既にユーザーが選択されている（永続化されている）場合、自動でWebSocket接続
  useEffect(() => {
    const autoConnect = async () => {
      if (currentUser && !isWebSocketConnected) {
        try {
          await connectWebSocket(currentUser.id)
          console.log('WebSocket自動接続完了:', currentUser.id)
        } catch (e) {
          console.error('WebSocket自動接続エラー:', e)
        }
      }
    }
    autoConnect()
  }, [currentUser, isWebSocketConnected, connectWebSocket])

  const handleUserChange = async (user: any) => {
    setCurrentUser(user)
    setShowUserSelector(false)
    // ユーザー切り替え時にチャット内容をクリア（新しいユーザーとの履歴は空）
    clearMessages()
    
    // WebSocket接続を確立
    try {
      await connectWebSocket(user.id)
      console.log('WebSocket接続完了:', user.id)
    } catch (error) {
      console.error('WebSocket接続エラー:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">SenseChat MVP を読み込み中...</p>
        </div>
      </div>
    )
  }

  if (!currentUser && availableUsers.length > 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <MessageCircle className="mx-auto h-12 w-12 text-primary-600" />
            <h2 className="mt-6 text-3xl font-bold text-gray-900">
              SenseChat MVP
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              家族内使用・技術検証版
            </p>
          </div>
          
          <UserSelector />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50" onClick={() => setShowUserSelector(false)}>
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <MessageCircle className="h-8 w-8 text-primary-600" />
              <h1 className="ml-2 text-xl font-semibold text-gray-900">
                SenseChat MVP
              </h1>
            </div>
            
            <div className="flex items-center space-x-4 relative">
              <div className="flex items-center space-x-2">
                <Users className="h-5 w-5 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {currentUser.name}
                </span>
              </div>
              
              <button 
                onClick={(e) => {
                  e.stopPropagation()
                  setShowUserSelector(!showUserSelector)
                }}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <Settings className="h-5 w-5" />
              </button>
              
              {/* ユーザー選択ドロップダウン */}
              {showUserSelector && (
                <div 
                  className="absolute right-0 top-12 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="py-1">
                    {availableUsers.length === 0 ? (
                      <div className="px-4 py-2 text-sm text-gray-500">
                        ユーザーを読み込み中...
                      </div>
                    ) : (
                      availableUsers.map((user) => (
                        <button
                          key={user.id}
                          onClick={() => handleUserChange(user)}
                          className={`w-full text-left px-4 py-3 text-sm hover:bg-gray-100 transition-colors ${
                            currentUser?.id === user.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
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
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* チャットエリア */}
          <div className="lg:col-span-2">
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                チャット
              </h2>
              
              <ChatInterface />
              
              <div className="mt-4">
                <MessageInput />
              </div>
            </div>
          </div>
          
          {/* サイドバー */}
          <div className="space-y-6">
            {/* ユーザー情報 */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                ユーザー情報
              </h3>
              
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    名前
                  </label>
                  <p className="text-sm text-gray-900">{currentUser.name}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    言語
                  </label>
                  <p className="text-sm text-gray-900">{currentUser.language}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    スタイル
                  </label>
                  <p className="text-sm text-gray-900">{currentUser.style_preset}</p>
                </div>
              </div>
            </div>
            
            {/* 統計情報 */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                統計
              </h3>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">送信メッセージ</span>
                  <span className="text-sm font-medium text-gray-900">
                    {messages.filter(m => m.sender_id === currentUser.id).length}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">受信メッセージ</span>
                  <span className="text-sm font-medium text-gray-900">
                    {messages.filter(m => m.sender_id !== currentUser.id).length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
