// 获取cookies的JavaScript代码
const cookies = document.cookie.split(';').reduce((acc, cookie) => {
  const [name, value] = cookie.trim().split('=');
  if (name && value) {
    acc[name] = value;
  }
  return acc;
}, {});

console.log('Current cookies:');
console.log(JSON.stringify(cookies, null, 2));

// 特别关注认证相关的cookies
const authCookies = {
  '_ams_token': cookies['_ams_token'],
  '_common_token': cookies['_common_token'],
  'HWWAFSESID': cookies['HWWAFSESID'],
  'HWWAFSESTIME': cookies['HWWAFSESTIME']
};

console.log('\nAuth cookies:');
console.log(JSON.stringify(authCookies, null, 2));
