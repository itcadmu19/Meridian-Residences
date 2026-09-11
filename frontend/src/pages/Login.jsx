import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import Card from "../components/Card.jsx";
import Input from "../components/Input.jsx";
import Button from "../components/Button.jsx";

export default function Login() {
  const { login, isSubmitting } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    // Read straight from the submitted form, not just React state — some
    // browsers/password managers autofill the DOM without firing onChange,
    // which would otherwise silently submit stale/empty credentials.
    const formData = new FormData(event.currentTarget);
    const submittedEmail = String(formData.get("email") || "").trim();
    const submittedPassword = String(formData.get("password") || "");

    try {
      await login(submittedEmail, submittedPassword);
      navigate("/");
    } catch (err) {
      setError(err.message || "Invalid email or password");
    }
  }

  return (
    <div className="page" style={{ maxWidth: 420, margin: "80px auto" }}>
      <Card>
        <h1 className="page-header__title" style={{ marginBottom: 4 }}>
          Meridian Residences
        </h1>
        <p className="page-header__description" style={{ marginBottom: 24 }}>
          Sign in to your resident portal.
        </p>
        <form onSubmit={handleSubmit}>
          <Input
            id="email"
            name="email"
            label="Email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <Input
            id="password"
            name="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={error}
            required
          />
          <Button type="submit" disabled={isSubmitting} style={{ width: "100%", justifyContent: "center" }}>
            {isSubmitting ? "Signing in..." : "Sign In"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
