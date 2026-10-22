<template>
  <div class="app">
    <!-- 顶部栏 -->
    <header class="header">
      <h1>AI 知识库问答助手</h1>
      <el-button type="primary" size="small" @click="drawer = true">
        知识库管理
      </el-button>
    </header>

    <div class="body">
      <!-- 左侧：会话列表 -->
      <aside class="sidebar">
        <el-button type="primary" style="width: 100%" @click="newConversation">
          ＋ 新建对话
        </el-button>
        <div class="conv-list">
          <div
            v-for="c in conversations"
            :key="c.id"
            class="conv-item"
            :class="{ active: c.id === currentId }"
            @click="openConversation(c)"
          >
            {{ c.title }}
            <span class="count">（{{ c.msg_count }}）</span>
          </div>
          <div v-if="!conversations.length" class="empty-tip">暂无会话</div>
        </div>
      </aside>

      <!-- 右侧：对话区 -->
      <main class="chat">
        <div class="messages" ref="msgBox">
          <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
            <div class="bubble">{{ m.content }}</div>
          </div>
          <div v-if="loading" class="msg assistant">
            <div class="bubble">思考中…</div>
          </div>
        </div>

        <div class="input">
          <el-input
            v-model="question"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="输入你的问题，例如：数据库事务是什么？"
            @keydown.enter.exact.prevent="send"
          />
          <el-button
            type="primary"
            :disabled="!question.trim() || loading"
            @click="send"
          >
            发送
          </el-button>
        </div>
      </main>
    </div>

    <!-- 右侧抽屉：知识库管理（上传/删除文档） -->
    <el-drawer v-model="drawer" title="知识库管理" size="380px">
      <el-upload
        :auto-upload="false"
        :limit="1"
        accept=".txt,.md,.pdf"
        :on-change="onFileChange"
        :on-remove="() => (file = null)"
      >
        <el-button>选择文件（txt / md / pdf）</el-button>
      </el-upload>
      <el-button
        type="primary"
        :disabled="!file"
        :loading="uploading"
        style="margin-top: 12px"
        @click="upload"
      >
        上传并解析
      </el-button>
      <el-divider />
      <div v-if="!docs.length" class="empty-tip">知识库为空，先上传一份文档吧</div>
      <div v-for="d in docs" :key="d.id" class="doc-item">
        <div style="flex: 1; min-width: 0">
          <div class="doc-title">{{ d.title }}</div>
          <div class="doc-meta">{{ d.status }} · {{ d.chunk_count }} 个分块</div>
        </div>
        <el-button type="danger" size="small" @click="removeDoc(d.id)">
          删除
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { chatApi, documentApi } from "./api";

// ---- 状态 ----
const conversations = ref([]); // 会话列表
const messages = ref([]); // 当前会话的消息
const currentId = ref(null); // 当前会话 id
const question = ref(""); // 输入框内容
const loading = ref(false); // 是否在等待大模型回复
const drawer = ref(false); // 知识库抽屉开关
const docs = ref([]); // 文档列表
const file = ref(null); // 待上传的文件
const uploading = ref(false);
const msgBox = ref(null);

// ---- 初始化：进入页面先加载会话列表和文档列表 ----
onMounted(async () => {
  const [c, d] = await Promise.all([
    chatApi.listConversations(),
    documentApi.list(),
  ]);
  conversations.value = c.data;
  docs.value = d.data;
  if (c.data.length) openConversation(c.data[0]);
});

// ---- 会话操作 ----
async function newConversation() {
  const r = await chatApi.createConversation("新对话");
  const conv = { id: r.data.conversation_id, title: "新对话", msg_count: 0 };
  conversations.value.unshift(conv);
  openConversation(conv);
}

async function openConversation(c) {
  currentId.value = c.id;
  const r = await chatApi.listMessages(c.id);
  messages.value = r.data;
  scrollBottom();
}

// ---- 发送消息（核心交互） ----
async function send() {
  const q = question.value.trim();
  if (!q || loading.value) return;
  if (!currentId.value) await newConversation(); // 没会话就先建一个

  question.value = "";
  messages.value.push({ role: "user", content: q });
  loading.value = true;
  scrollBottom();

  try {
    const r = await chatApi.send(currentId.value, q);
    messages.value.push({ role: "assistant", content: r.data.answer });
    // 回答完成后刷新会话列表（消息数会变化）
    const c = await chatApi.listConversations();
    conversations.value = c.data;
  } catch (e) {
    ElMessage.error("请求失败：" + (e.response?.data?.detail || e.message));
  } finally {
    loading.value = false;
    scrollBottom();
  }
}

// ---- 文档操作 ----
function onFileChange(f) {
  file.value = f.raw;
}

async function upload() {
  uploading.value = true;
  try {
    const r = await documentApi.upload(file.value);
    ElMessage.success(`上传成功，共 ${r.data.chunks} 个分块`);
    const d = await documentApi.list();
    docs.value = d.data;
    file.value = null;
  } catch (e) {
    ElMessage.error("上传失败：" + (e.response?.data?.detail || e.message));
  } finally {
    uploading.value = false;
  }
}

async function removeDoc(id) {
  await documentApi.remove(id);
  const d = await documentApi.list();
  docs.value = d.data;
  ElMessage.success("已删除");
}

// ---- 工具：让消息区滚动到底部 ----
function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight;
  });
}
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
html,
body,
#app {
  height: 100%;
}
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
}
.header {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #1f6feb;
  color: #fff;
}
.header h1 {
  font-size: 18px;
  font-weight: 600;
}
.body {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.sidebar {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid #eee;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
}
.conv-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  background: #f5f6f7;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-item.active {
  background: #e6f0ff;
  color: #1f6feb;
  font-weight: 600;
}
.count {
  color: #999;
  font-size: 12px;
}
.empty-tip {
  color: #999;
  font-size: 13px;
  text-align: center;
  padding: 16px 0;
}
.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.msg {
  margin-bottom: 12px;
  display: flex;
}
.msg.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  font-size: 14px;
  background: #f0f2f5;
}
.msg.user .bubble {
  background: #1f6feb;
  color: #fff;
}
.input {
  padding: 12px 20px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.input .el-textarea {
  flex: 1;
}
.doc-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}
.doc-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.doc-meta {
  color: #999;
  font-size: 12px;
  margin-top: 2px;
}
</style>
