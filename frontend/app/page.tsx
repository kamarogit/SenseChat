'use client'

import { useState, useEffect } from 'react'
import { MessageCircle, Users, Settings, Send } from 'lucide-react'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import { ChatInterface } from '@/components/ChatInterface'
import { UserSelector } from '@/components/UserSelector'
import { MessageInput } from '@/components/MessageInput'

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(true)
  const { currentUser, setCurrentUser } = useUserStore()
  const { messages, loadMessages } = useChatStore()

  useEffect(() => {
    // 初期化処理
    const initializeApp = async () => {
      try {
        // ユーザー情報の取得
        const response = await fetch('/api/v1/users')
        if (response.ok) {
          const data = await response.json()
          if (data.users && data.users.length > 0) {
            setCurrentUser(data.users[0])
          }
        }
        
        // メッセージの読み込み
        await loadMessages()
        
      } catch (error) {
        console.error('初期化エラー:', error)
      } finally {
        setIsLoading(false)
      }
    }

    initializeApp()
  }, [setCurrentUser, loadMessages])

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

  if (!currentUser) {
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
    <div className="min-h-screen bg-gray-50">
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
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Users className="h-5 w-5 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {currentUser.name}
                </span>
              </div>
              
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <Settings className="h-5 w-5" />
              </button>
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
