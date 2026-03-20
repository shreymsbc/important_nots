// Collapsible Sidebar with nav items
import { useState } from "react";

const Sidebar = ({ items }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [active, setActive] = useState(null);

  return (
    <div className={`h-screen bg-gray-900 text-white transition-all ${collapsed ? "w-16" : "w-56"}`}>
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full p-4 text-left text-gray-400 hover:text-white"
      >
        {collapsed ? "→" : "← Collapse"}
      </button>
      <nav className="mt-2">
        {items.map((item) => (
          <div
            key={item.label}
            onClick={() => setActive(item.label)}
            className={`flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-700 ${
              active === item.label ? "bg-gray-700" : ""
            }`}
          >
            <span>{item.icon}</span>
            {!collapsed && <span className="text-sm">{item.label}</span>}
          </div>
        ))}
      </nav>
    </div>
  );
};
export default Sidebar;