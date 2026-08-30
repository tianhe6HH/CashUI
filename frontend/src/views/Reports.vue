<template>
  <div>
    <van-nav-bar title="报表下载" left-arrow @click-left="$router.back()" />

    <!-- 生成报表卡片 -->
    <div class="card">
      <div class="card-title">生成月度报表</div>
      <div class="card-body row">
        <el-date-picker
          v-if="isDesktop"
          v-model="month"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择月份"
          class="month-picker"
        />
        <van-field
          v-if="!isDesktop"
          v-model="month"
          readonly
          is-link
          label="月份"
          placeholder="YYYY-MM"
          class="month-field"
          @click="showMonthPicker = true"
        />
        <van-button type="primary" class="gen-btn" @click="onGenerate">
          生成报表
        </van-button>
      </div>
    </div>

    <!-- 已有报表 -->
    <div class="card">
      <div class="card-title">已有报表</div>
      <div v-if="list.length" class="report-list">
        <div v-for="r in list" :key="r.month" class="report-item">
          <div class="report-info">
            <div class="report-month">{{ r.month }}</div>
            <div class="report-time">生成于 {{ (r.generated_at || '').replace('T', ' ').slice(0, 16) }}</div>
          </div>
          <van-button size="small" type="primary" plain @click="onDownload(r.month)">下载</van-button>
        </div>
      </div>
      <van-empty v-else description="暂无报表" />
    </div>

    <van-popup v-model:show="showMonthPicker" position="bottom" round>
      <van-date-picker v-model="monthValue" type="year-month" title="选择月份" @confirm="onMonthConfirm" @cancel="showMonthPicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getReports, generateReport, downloadReport } from '../api'
import { useIsDesktop } from '../composables/useIsDesktop'
import { showToast } from 'vant'

const { isDesktop } = useIsDesktop()
const list = ref([])
const month = ref('')
const showMonthPicker = ref(false)
const _now = new Date()
const monthValue = ref([String(_now.getFullYear()), String(_now.getMonth() + 1).padStart(2, '0')])

function onMonthConfirm({ selectedValues }) {
  const [y, m] = selectedValues
  month.value = `${y}-${m}`
  showMonthPicker.value = false
}

async function load() {
  try {
    list.value = await getReports()
  } catch (e) {}
}

async function onGenerate() {
  if (!month.value) {
    showToast('请选择月份')
    return
  }
  try {
    await generateReport(month.value)
    showToast('已生成')
    load()
  } catch (e) {}
}

async function onDownload(m) {
  try {
    const blob = await downloadReport(m)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `备用金报表-${m}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {}
}

onMounted(load)
</script>

<style scoped>
.card {
  margin: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
.card-title {
  padding: 14px 16px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  border-bottom: 1px solid #f2f3f5;
}
.card-body {
  padding: 16px;
}
.card-body.row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.month-picker {
  flex: 1;
  min-width: 0;
}
.month-field {
  flex: 1;
  min-width: 0;
}
.gen-btn {
  flex-shrink: 0;
}
.report-list {
  padding: 0 16px;
}
.report-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f7f8fa;
}
.report-item:last-child {
  border-bottom: none;
}
.report-month {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}
.report-time {
  font-size: 12px;
  color: #969799;
  margin-top: 2px;
}
</style>
