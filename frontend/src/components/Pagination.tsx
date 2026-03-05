interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onOffsetChange: (offset: number) => void;
}

export default function Pagination({
  total,
  limit,
  offset,
  onOffsetChange,
}: PaginationProps) {
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + limit, total);
  const hasPrev = offset > 0;
  const hasNext = offset + limit < total;

  return (
    <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
      <span>
        Showing {start}–{end} of {total}
      </span>
      <div className="flex space-x-2">
        <button
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
          disabled={!hasPrev}
          className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-100 disabled:hover:bg-transparent"
        >
          Prev
        </button>
        <button
          onClick={() => onOffsetChange(offset + limit)}
          disabled={!hasNext}
          className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-100 disabled:hover:bg-transparent"
        >
          Next
        </button>
      </div>
    </div>
  );
}
