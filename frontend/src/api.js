// API 请求封装：所有后端接口统一走 axios
// baseURL 设为 /api，实际请求会由 Vite 代理转发到后端 8000 端口
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 60000, // 大模型回答可能较慢，给足 60 秒
});

// 文档管理接口
export const documentApi = {
  // 上传文件：用 FormData 传 multipart/form-data
  upload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/documents/upload", form);
  },
  list: () => api.get("/documents"),
  remove: (id) => api.delete(`/documents/${id}`),
};

// 对话接口
export const chatApi = {
  createConversation: (title) => api.post("/conversations", { title }),
  listConversations: () => api.get("/conversations"),
  listMessages: (id) => api.get(`/conversations/${id}/messages`),
  send: (conversationId, question) =>
    api.post("/chat", { conversation_id: conversationId, question }),
};

export default api;
