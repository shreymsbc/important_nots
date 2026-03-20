// Toast notification system
import { useState } from "react";

const useToast = () => {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000);
  };

  const ToastContainer = () => (
    <div className="fixed bottom-4 right-4 space-y-2 z-50">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`px-4 py-2 rounded shadow text-white text-sm ${
            t.type === "error" ? "bg-red-500" : t.type === "success" ? "bg-green-500" : "bg-gray-700"
          }`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );

  return { addToast, ToastContainer };
};
export default useToast;