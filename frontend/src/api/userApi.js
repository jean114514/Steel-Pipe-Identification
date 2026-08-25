import request from './index'

// 用户注册（不需要传role）
export function register(data) {
  return request({
    url: '/user/register',
    method: 'post',
    data
  })
}

// 用户登录
export function login(data) {
  return request({
    url: '/user/login',
    method: 'post',
    data
  })
}

// 获取所有用户（管理员）- 只显示员工
export function getUsers(params) {
  return request({
    url: '/user/users',
    method: 'get',
    params
  })
}

// 更新用户状态
export function updateUserStatus(userId, status) {
  return request({
    url: `/user/user/${userId}/status`,
    method: 'put',
    params: { status }
  })
}

// 重置用户密码
export function resetPassword(userId) {
  return request({
    url: `/user/user/${userId}/reset-password`,
    method: 'post'
  })
}

// 删除用户
export function deleteUser(userId) {
  return request({
    url: `/user/user/${userId}`,
    method: 'delete'
  })
}

// 获取统计数据
export function getStatistics() {
  return request({
    url: '/user/statistics',
    method: 'get'
  })
}

// 获取所有识别记录
export function getAllRecords(params) {
  return request({
    url: '/user/all-records',
    method: 'get',
    params
  })
}