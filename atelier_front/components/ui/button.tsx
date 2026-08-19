import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'quiet' | 'pine' | 'outline'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  variant?: Variant
}

export function Button({ children, onClick, variant = 'primary', disabled = false, type = 'button', className, ...rest }: Props) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`button button-${variant}${className ? ` ${className}` : ''}`}
      {...rest}
    >
      {children}
    </button>
  )
}
