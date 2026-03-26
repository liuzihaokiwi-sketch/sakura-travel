import { cn } from "@/lib/utils"

type SeparatorProps = {
  className?: string
}

export function Separator({ className }: SeparatorProps) {
  return <div aria-hidden="true" className={cn("h-px w-full bg-stone-200", className)} />
}
