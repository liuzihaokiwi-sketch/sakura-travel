"use client";

import { useMemo } from "react";

const PETAL_COUNT = 15;

interface Petal {
  id: number;
  left: string;
  size: number;
  duration: string;
  delay: string;
  opacity: number;
}

export function SakuraParticles() {
  const petals = useMemo<Petal[]>(() => {
    return Array.from({ length: PETAL_COUNT }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: 8 + Math.random() * 12,
      duration: `${8 + Math.random() * 12}s`,
      delay: `${-Math.random() * 15}s`,
      opacity: 0.3 + Math.random() * 0.4,
    }));
  }, []);

  return (
    <div className="pointer-events-none fixed inset-0 z-[1] overflow-hidden">
      {petals.map((p) => (
        <div
          key={p.id}
          className="sakura-petal absolute"
          style={
            {
              left: p.left,
              top: "-20px",
              width: p.size,
              height: p.size,
              opacity: p.opacity,
              "--duration": p.duration,
              "--delay": p.delay,
              background:
                "radial-gradient(ellipse at 30% 30%, #f8bbd0 0%, #f48fb1 50%, transparent 70%)",
              borderRadius: "50% 0 50% 50%",
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  );
}
