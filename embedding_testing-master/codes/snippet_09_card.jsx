// Stat / Info Card
const Card = ({ title, value, icon, trend }) => {
  return (
    <div className="bg-white rounded-xl shadow p-5 flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
        {trend && (
          <p className={`text-xs mt-1 ${trend > 0 ? "text-green-500" : "text-red-500"}`}>
            {trend > 0 ? "▲" : "▼"} {Math.abs(trend)}% vs last month
          </p>
        )}
      </div>
      <div className="text-3xl">{icon}</div>
    </div>
  );
};
export default Card;