<template>
  <div>
    <van-nav-bar title="数据管理" left-arrow @click-left="$router.back()" />

    <van-cell-group inset title="整体数据" style="margin-top: 12px">
      <van-cell title="导出全部数据" is-link class="all-cell" @click="onExport('all')" />
      <van-cell title="导入全部数据" is-link class="all-cell" @click="triggerImport('all')" />
    </van-cell-group>

    <van-cell-group inset title="按功能导出" style="margin-top: 16px">
      <van-cell
        v-for="s in scopeOptions"
        :key="s.value"
        :title="'导出' + s.label"
        is-link
        @click="onExport(s.value)"
      />
    </van-cell-group>

    <van-cell-group inset title="按功能导入" style="margin-top: 16px">
      <van-cell
        v-for="s in scopeOptions"
        :key="s.value"
        :title="'导入' + s.label"
        is-link
        @click="triggerImport(s.value)"
      />
    </van-cell-group>

    <div style="margin: 16px">
      <p class="hint">
        导入为「合并追加」：不删除现有数据，只新增。账号密码导出时密码列为空，
        已存在账号不会改密码；新账号将使用默认密码。引用不到的科目 / 缴款人 /
        账号 / 活动会被跳过并提示。
      </p>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="application/json,.json"
      style="display: none"
      @change="onFileChange"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { exportData, importData } from '../api'
import { showToast, showConfirmDialog } from 'vant'

const fileInput = ref(null)
const pendingScope = ref('all')

const scopeOptions = [
  { value: 'accounts', label: '科目' },
  { value: 'funders', label: '缴款人' },
  { value: 'users', label: '账号密码' },
  { value: 'activities', label: '活动' },
  { value: 'transactions', label: '记账明细' },
  { value: 'votes', label: '投票' },
]

async function onExport(scope) {
  try {
    const blob = await exportData(scope)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cashui-data${scope === 'all' ? '' : '-' + scope}.json`
    a.click()
    URL.revokeObjectURL(url)
    showToast('已导出')
  } catch (e) {}
}

function triggerImport(scope) {
  pendingScope.value = scope
  fileInput.value?.click()
}

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const scope = pendingScope.value
  try {
    const text = await file.text()
    let payload
    try {
      payload = JSON.parse(text)
    } catch (err) {
      showToast('文件不是有效的 JSON')
      return
    }
    await showConfirmDialog({
      title: '确认导入？',
      message: '将以合并追加方式导入，不删除现有数据',
    })
    const res = await importData(payload, scope)
    const skipped = res.skipped || []
    const total = Object.keys(res).filter((k) => k !== 'skipped').reduce((n, k) => n + (res[k] || 0), 0)
    if (skipped.length) {
      showToast(`已导入 ${total} 条，跳过 ${skipped.length} 条`)
      console.warn('跳过明细：', skipped)
    } else {
      showToast(`导入成功，共 ${total} 条`)
    }
  } catch (e) {
    // 用户取消或请求失败
  } finally {
    e.target.value = ''
  }
}
</script>

<style scoped>
.hint {
  color: #999;
  font-size: 13px;
  line-height: 1.6;
}
.all-cell {
  font-weight: 600;
}
</style>
