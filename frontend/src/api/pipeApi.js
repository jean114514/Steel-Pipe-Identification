import request from './index'

// 钢管识别接口
export function recognizePipe(data) {
  return request({
    url: '/recognize',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 保存识别结果
export function saveResult(data) {
  return request({
    url: '/save',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 仅保存识别记录（不对比）
export function saveRecordOnly(data) {
  return request({
    url: '/inventory/save-record-only',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 更新识别记录（重新对比）
export function updateRecord(recordId, data) {
  return request({
    url: `/update/${recordId}`,
    method: 'put',
    data,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

// 手动标记保存
export function saveManualMarks(data) {
  return request({
    url: '/manual/save',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 获取历史记录
export function getHistoryRecords(params) {
  return request({
    url: '/records',
    method: 'get',
    params
  })
}

// 蒙版裁剪接口
export function cropWithMask(data) {
  return request({
    url: '/crop',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// ========== 入库相关API ==========

// 添加入库记录
export function addInventory(data) {
  return request({
    url: '/inventory/add',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 获取入库列表
export function getInventoryList(params) {
  return request({
    url: '/inventory/list',
    method: 'get',
    params
  })
}

// 更新入库数量
export function updateInventory(inventoryId, data) {
  return request({
    url: `/inventory/update/${inventoryId}`,
    method: 'put',
    data,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

// 删除入库记录
export function deleteInventory(inventoryId) {
  return request({
    url: `/inventory/delete/${inventoryId}`,
    method: 'delete'
  })
}

// 根据钢管编号查询入库信息
export function searchInventory(pipeNumber) {
  return request({
    url: '/inventory/search',
    method: 'get',
    params: { pipe_number: pipeNumber }
  })
}

// 提交反馈（支持类型区分）
export function submitFeedback(data) {
  return request({
    url: '/inventory/feedback',
    method: 'post',
    data,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

// 获取待处理反馈
export function getPendingFeedback() {
  return request({
    url: '/inventory/pending-feedback',
    method: 'get'
  })
}

// 获取已处理反馈
export function getResolvedFeedback() {
  return request({
    url: '/inventory/resolved-feedback',
    method: 'get'
  })
}

// 获取用户自己的反馈
export function getMyFeedback(userId) {
  return request({
    url: '/inventory/my-feedback',
    method: 'get',
    params: { user_id: userId }
  })
}

// 获取反馈详情
export function getFeedbackDetail(feedbackId) {
  return request({
    url: `/inventory/feedback/${feedbackId}`,
    method: 'get'
  })
}

// 处理反馈
export function resolveFeedback(data) {
  return request({
    url: '/inventory/resolve-feedback',
    method: 'post',
    data,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

// 请求新增入库
export function requestAddInventory(data) {
  return request({
    url: '/inventory/request-add',
    method: 'post',
    data,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}