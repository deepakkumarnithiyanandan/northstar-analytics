import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Sidebar } from './Sidebar'

describe('Sidebar', () => {
  it('shows the current page and changes views when navigation is selected', () => {
    const onChange = vi.fn()
    render(<Sidebar active="dashboard" onChange={onChange} />)
    expect(screen.getByRole('button', { name: /overview/i })).toHaveClass('active')
    fireEvent.click(screen.getByRole('button', { name: /data explorer/i }))
    expect(onChange).toHaveBeenCalledWith('data')
  })
})