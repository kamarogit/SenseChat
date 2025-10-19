'use client'

import { ReactNode } from 'react'
import { Toaster } from 'sonner'

interface ProvidersProps {
  children: ReactNode
}

export function Providers({ children }: ProvidersProps) {
  return (
    <>
      {children}
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#fff',
            color: '#374151',
            border: '1px solid #e5e7eb',
          },
        }}
      />
    </>
  )
}
