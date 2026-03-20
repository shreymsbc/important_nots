// Pagination component
const Pagination = ({ total, perPage, current, onChange }) => {
  const pages = Math.ceil(total / perPage);

  return (
    <div className="flex items-center gap-2 mt-4">
      <button
        onClick={() => onChange(current - 1)}
        disabled={current === 1}
        className="px-3 py-1 rounded border disabled:opacity-40 hover:bg-gray-100"
      >
        Prev
      </button>
      {Array.from({ length: pages }, (_, i) => i + 1).map((p) => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={`px-3 py-1 rounded border ${
            p === current ? "bg-blue-600 text-white" : "hover:bg-gray-100"
          }`}
        >
          {p}
        </button>
      ))}
      <button
        onClick={() => onChange(current + 1)}
        disabled={current === pages}
        className="px-3 py-1 rounded border disabled:opacity-40 hover:bg-gray-100"
      >
        Next
      </button>
    </div>
  );
};
export default Pagination;