import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-accent/20 bg-accent-soft text-accent",
        secondary: "border-line bg-surface-sunken text-ink-soft",
        destructive: "border-negative/20 bg-negative-soft text-negative",
        outline: "border-line-strong text-ink-soft",
        success: "border-positive/20 bg-positive-soft text-positive",
        warning: "border-warning/25 bg-warning-soft text-warning",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}
