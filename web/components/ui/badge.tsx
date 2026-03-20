import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-sakura-100 text-sakura-600",
        warm: "border-transparent bg-warm-100 text-warm-500",
        bloom: "border-transparent bg-gradient-to-r from-sakura-200 to-sakura-300 text-sakura-600",
        secondary: "border-transparent bg-stone-100 text-stone-600",
        outline: "border-stone-200 text-stone-600",
        success: "border-transparent bg-emerald-50 text-emerald-600",
        warning: "border-transparent bg-amber-50 text-amber-600",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
