package apitest

import apitesting "apitest-common"

// Envelope 复用共享统一响应体 {code,message,data}（别名，测试文件里的 Envelope 即此类型）。
// 项目无此封套时删掉本别名与下面的 Env* 便捷方法，改用 cli.RawDo。
type Envelope = apitesting.Envelope

// cli 在 TestMain 里按配置超时初始化。
var cli *apitesting.Client

// 包级 token，在 TestMain 里通过登录换取。
var (
	UserToken  string // 普通用户
	AdminToken string // 管理员
)

// GenerateRandomString 复用共享随机串工具（re-export，避免测试文件大量调用改名）。
func GenerateRandomString(n int) string { return apitesting.RandString(n) }

// ---- 便捷方法：按目标服务的 baseURL / 鉴权语义命名（下面是通用示例，按服务改名）----

// Do 用普通用户 token 请求被测服务。
func Do(method, path string, body any) (int, Envelope, error) {
	return cli.EnvDo(GetConfig().App.BaseURL, method, path, body, UserToken, nil)
}

// DoAdmin 用管理员 token 请求（需 admin 角色的接口）。
func DoAdmin(method, path string, body any) (int, Envelope, error) {
	return cli.EnvDo(GetConfig().App.BaseURL, method, path, body, AdminToken, nil)
}

// DoToken 用指定 token 请求（token 传 "" 即不带鉴权，用于鉴权异常用例）。
func DoToken(token, method, path string, body any) (int, Envelope, error) {
	return cli.EnvDo(GetConfig().App.BaseURL, method, path, body, token, nil)
}

// DoH 用普通用户 token 请求，并追加额外 header。
func DoH(method, path string, body any, headers map[string]string) (int, Envelope, error) {
	return cli.EnvDo(GetConfig().App.BaseURL, method, path, body, UserToken, headers)
}

// DoRaw 返回原始字节 + HTTP 状态 + Content-Type（用于非统一封套 / 非 JSON 接口）。
func DoRaw(method, path string, body any) (int, []byte, string, error) {
	return cli.RawDo(GetConfig().App.BaseURL, method, path, body, UserToken, nil)
}

// 示例：带内部密钥的内部接口（按项目补 config 字段后启用）。
// func DoInternal(method, path string, body any) (int, Envelope, error) {
// 	h := map[string]string{"X-Internal-Key": GetConfig().Auth.InternalKey}
// 	return cli.EnvDo(GetConfig().App.BaseURL, method, path, body, "", h)
// }
