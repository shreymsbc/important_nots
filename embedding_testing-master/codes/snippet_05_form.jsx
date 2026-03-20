// Controlled form with validation
import { useState } from "react";

const Form = ({ onSubmit }) => {
  const [values, setValues] = useState({ name: "", email: "" });
  const [errors, setErrors] = useState({});

  const validate = () => {
    const errs = {};
    if (!values.name) errs.name = "Name is required";
    if (!values.email.includes("@")) errs.email = "Invalid email";
    return errs;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) return setErrors(errs);
    onSubmit(values);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <input
          placeholder="Name"
          value={values.name}
          onChange={(e) => setValues({ ...values, name: e.target.value })}
          className="border rounded px-3 py-2 w-full"
        />
        {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
      </div>
      <div>
        <input
          placeholder="Email"
          value={values.email}
          onChange={(e) => setValues({ ...values, email: e.target.value })}
          className="border rounded px-3 py-2 w-full"
        />
        {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
      </div>
      <Button label="Submit" variant="primary" />
    </form>
  );
};
export default Form;