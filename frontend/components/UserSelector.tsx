'use client'

import { useState, useEffect } from 'react'
import { useUserStore } from '@/stores/userStore'
import { User } from '@/stores/userStore'
import { Users, Check } from 'lucide-react'

export function UserSelector() {
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const { availableUsers, loadUsers, setCurrentUser, isLoading } = useUserStore()

  useEffect(() => {
    loadUsers()
  }, [loadUsers])

  const handleUserSelect = (user: User) => {
    setSelectedUser(user)
    setCurrentUser(user)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-2 text-gray-600">ユーザーを読み込み中...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <Users className="mx-auto h-12 w-12 text-primary-600 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          ユーザーを選択してください
        </h3>
        <p className="text-sm text-gray-600">
          家族内使用のため、利用可能なユーザーから選択してください
        </p>
      </div>

      <div className="space-y-3">
        {availableUsers.map((user) => (
          <button
            key={user.id}
            onClick={() => handleUserSelect(user)}
            className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
              selectedUser?.id === user.id
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">{user.name}</h4>
                <div className="flex items-center space-x-4 mt-1">
                  <span className="text-sm text-gray-600">
                    言語: {user.language}
                  </span>
                  <span className="text-sm text-gray-600">
                    スタイル: {user.style_preset}
                  </span>
                </div>
              </div>
              
              {selectedUser?.id === user.id && (
                <Check className="h-5 w-5 text-primary-600" />
              )}
            </div>
          </button>
        ))}
      </div>

      {selectedUser && (
        <div className="text-center">
          <p className="text-sm text-gray-600">
            {selectedUser.name} としてログインしました
          </p>
        </div>
      )}
    </div>
  )
}
