<template>
  <div class="markdown-body" v-html="rendered"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps({
  content: { type: String, default: '' }
})

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

const rendered = computed(() => {
  if (!props.content) return ''
  return md.render(props.content)
})
</script>

<style scoped>
.markdown-body {
  font-size: 14px;
  line-height: 1.7;
  color: #333;
}
.markdown-body h1 { font-size: 20px; font-weight: 700; margin: 16px 0 8px; }
.markdown-body h2 { font-size: 17px; font-weight: 700; margin: 14px 0 6px; }
.markdown-body h3 { font-size: 15px; font-weight: 700; margin: 12px 0 4px; }
.markdown-body h4 { font-size: 14px; font-weight: 700; margin: 10px 0 4px; }
.markdown-body p { margin: 6px 0; }
.markdown-body ul, .markdown-body ol { margin: 4px 0; padding-left: 22px; }
.markdown-body li { margin: 2px 0; }
.markdown-body strong { font-weight: 700; }
.markdown-body code {
  background: #f5f5f5;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 13px;
  color: #d63384;
  font-family: 'Menlo', 'Consolas', monospace;
}
.markdown-body pre { background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; margin: 8px 0; }
.markdown-body pre code { background: none; padding: 0; color: #333; }
.markdown-body blockquote {
  border-left: 3px solid #1677ff;
  margin: 8px 0;
  padding: 6px 12px;
  color: #666;
  background: #f8f9ff;
  border-radius: 0 4px 4px 0;
}
.markdown-body table { border-collapse: collapse; width: 100%; margin: 8px 0; }
.markdown-body th, .markdown-body td { border: 1px solid #e0e0e0; padding: 6px 10px; text-align: left; }
.markdown-body th { background: #f5f5f5; font-weight: 600; }
.markdown-body a { color: #1677ff; text-decoration: none; }
.markdown-body a:hover { text-decoration: underline; }
.markdown-body hr { border: none; border-top: 1px solid #e8e8e8; margin: 12px 0; }
</style>
