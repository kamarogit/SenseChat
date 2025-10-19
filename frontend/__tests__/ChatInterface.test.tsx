import { render, screen } from '@testing-library/react'
import { ChatInterface } from '@/components/ChatInterface'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'

// モック
jest.mock('@/stores/chatStore')
jest.mock('@/stores/userStore')

const mockUseChatStore = useChatStore as jest.MockedFunction<typeof useChatStore>
const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('ChatInterface', () => {
  beforeEach(() => {
    mockUseChatStore.mockReturnValue({
      messages: [],
      currentThread: null,
      isLoading: false,
      error: null,
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      loadMessages: jest.fn(),
      sendMessage: jest.fn(),
      clearError: jest.fn()
    })

    mockUseUserStore.mockReturnValue({
      currentUser: {
        id: 'user_1',
        name: 'テストユーザー',
        language: 'ja',
        style_preset: 'biz_formal'
      },
      availableUsers: [],
      isLoading: false,
      error: null,
      setCurrentUser: jest.fn(),
      loadUsers: jest.fn(),
      clearError: jest.fn()
    })
  })

  it('空のメッセージリストを表示する', () => {
    render(<ChatInterface />)
    
    expect(screen.getByText('まだメッセージがありません')).toBeInTheDocument()
    expect(screen.getByText('下の入力欄からメッセージを送信してください')).toBeInTheDocument()
  })

  it('エラー状態を表示する', () => {
    mockUseChatStore.mockReturnValue({
      messages: [],
      currentThread: null,
      isLoading: false,
      error: 'テストエラー',
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      loadMessages: jest.fn(),
      sendMessage: jest.fn(),
      clearError: jest.fn()
    })

    render(<ChatInterface />)
    
    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
    expect(screen.getByText('テストエラー')).toBeInTheDocument()
  })

  it('ローディング状態を表示する', () => {
    mockUseChatStore.mockReturnValue({
      messages: [],
      currentThread: null,
      isLoading: true,
      error: null,
      addMessage: jest.fn(),
      updateMessage: jest.fn(),
      loadMessages: jest.fn(),
      sendMessage: jest.fn(),
      clearError: jest.fn()
    })

    render(<ChatInterface />)
    
    expect(screen.getByText('処理中...')).toBeInTheDocument()
  })
})
