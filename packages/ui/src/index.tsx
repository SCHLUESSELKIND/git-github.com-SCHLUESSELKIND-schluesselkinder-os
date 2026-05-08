import type { ReactNode } from "react";

export function SectionLabel({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <p className="text-xs font-black uppercase tracking-normal text-red-700">
      {children}
    </p>
  );
}

export function TrackList({ tracks }: Readonly<{ tracks: readonly string[] }>) {
  return (
    <ul className="mt-5 grid gap-3" aria-label="Track list">
      {tracks.map((track) => (
        <li
          className="flex items-center justify-between border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-bold text-zinc-950"
          key={track}
        >
          <span>{track}</span>
        </li>
      ))}
    </ul>
  );
}
