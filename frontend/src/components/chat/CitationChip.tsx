"use client";

interface CitationChipProps {
  index: number;
  onClick: () => void;
  active?: boolean;
}

// A small inline [N] chip that sits next to a piece of text, telling the user
// they can click it to see the source. Kept dumb on purpose — design pass
// will redo the look.
export default function CitationChip({ index, onClick, active = false }: CitationChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "inline-flex items-center justify-center align-baseline",
        "h-5 min-w-[1.25rem] px-1 mx-0.5 rounded",
        "text-[11px] font-semibold tabular-nums",
        "border transition-colors",
        active
          ? "bg-blue-600 text-white border-blue-700"
          : "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100",
      ].join(" ")}
      aria-label={`Open source ${index}`}
    >
      [{index}]
    </button>
  );
}
