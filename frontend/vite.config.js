import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Vite 开发服务器配置：
// 前端跑在 5173 端口，后端 FastAPI 跑在 8000 端口。
// 通过 proxy 把 /api 开头的请求转发给后端，前端代码里只写相对路径 /api/xxx，
// 从而避免跨域问题，也方便以后部署时统一改一处。
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
