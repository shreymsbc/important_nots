snippet_01_button// Reusable Button Component with variants
const Button = ({ label, onClick, variant = "primary", disabled = false }) => {
  const styles = {
    primary: "bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700",
    secondary: "bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300",
    danger: "bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${styles[variant]} disabled:opacity-50 cursor-pointer`}
    >
      {label}
    </button>
  );
};
export default Button;