// Full Dashboard Layout shell
import Sidebar from "./snippet_06_sidebar";
import Card from "./snippet_09_card";

const DashboardLayout = ({ children }) => {
  const navItems = [
    { label: "Dashboard", icon: "🏠" },
    { label: "Users", icon: "👥" },
    { label: "Reports", icon: "📊" },
    { label: "Settings", icon: "⚙️" },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar items={navItems} />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card title="Total Users" value="1,240" icon="👤" trend={12} />
          <Card title="Revenue" value="$8,430" icon="💰" trend={-3} />
          <Card title="Active Sessions" value="342" icon="🟢" trend={5} />
        </div>
        {children}
      </main>
    </div>
  );
};
export default DashboardLayout;