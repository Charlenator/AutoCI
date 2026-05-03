"use client";

interface CitationChipProps {
  index: number;
  onClick: () => void;
  active?: boolean;
}

// A small inline [N] chip that sits next to a piece of text, telling the user
// they can click it to see the source. Restyled per style_guide.css §9.
export default function CitationChip({ index, onClick, active = false }: CitationChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`cite-chip${active ? " active" : ""}`}
      aria-label={`Open source ${index}`}
    >
      {index}
    </button>
  );
}
