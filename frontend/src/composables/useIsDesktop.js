import { ref, onMounted, onUnmounted } from 'vue'

// 判断是否桌面端（宽度 >= 768px），供日期/时间字段等做响应式交互切换
export function useIsDesktop() {
  const isDesktop = ref(false)
  let mql = null

  function update() {
    isDesktop.value = mql.matches
  }

  onMounted(() => {
    mql = window.matchMedia('(min-width: 768px)')
    update()
    mql.addEventListener('change', update)
  })
  onUnmounted(() => {
    mql?.removeEventListener('change', update)
  })

  return { isDesktop }
}
