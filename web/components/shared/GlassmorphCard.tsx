import * as React from "react";
import { cn } from "@/lib/utils";

interface GlassmorphCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "light" | "dark";
}

export function GlassmorphCard({
  variant = "light",
  className,
  children,
  ...props
}: GlassmorphCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl backdrop-blur-xl border transition-all duration-200",
        variant === "light" &&
          "bg-white/80 border-white/20 shadow-lg shadow-stone-200/20",
        variant === "dark" &&
          "bg-black/60 border-white/10 shadow-lg shadow-black/20 text-white",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
