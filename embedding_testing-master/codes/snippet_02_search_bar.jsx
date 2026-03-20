// Search bar with debounce
import { useState, useEffect } from "react";

const SearchBar = ({ onSearch, placeholder = "Search..." }) => {
  const [query, setQuery] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => onSearch(query), 400);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <input
      type="text"
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      placeholder={placeholder}
      className="border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-400"
    />
  );
};
export default SearchBar;