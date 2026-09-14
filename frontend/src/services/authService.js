import api from "./api";

const authService = {
  login(email, password) {
    return api.post("/auth/login", { email, password });
  },
  register(payload) {
    return api.post("/auth/register", payload);
  },
};

export default authService;
