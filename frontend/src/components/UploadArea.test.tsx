import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { UploadArea } from './UploadArea'

describe('UploadArea', () => {
  it('shows a clear validation message for a non-CSV file', () => {
    render(<UploadArea onUploaded={vi.fn()} />)
    const input = document.querySelector('input[type="file"]')!
    fireEvent.change(input, { target: { files: [new File(['not csv'], 'notes.txt', { type: 'text/plain' })] } })
    expect(screen.getByRole('status')).toHaveTextContent('That file is not a CSV.')
  })
})