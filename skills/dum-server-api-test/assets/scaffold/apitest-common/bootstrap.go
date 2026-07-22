package apitesting

import "fmt"

// resolveToken 取一个账号的 token：优先用预置 Token，否则登录换取。
func resolveToken(cli *Client, loginBaseURL, loginPath string, cr Credential) (string, error) {
	if cr.Token != "" {
		return cr.Token, nil
	}
	return cli.Login(loginBaseURL, loginPath, cr.Email, cr.Password)
}

// Bootstrap 登录换取普通用户 / 管理员 token。
// 登录失败不致命：以 warns 文案返回，由调用方打印（无 token 的鉴权异常用例仍可跑，
// 依赖 token 的正常流用例会显式失败，便于定位是环境/账号问题而非用例问题）。
//
// 这是「邮箱密码 → JWT，双账号」的通用引导；鉴权方式不同的项目可不用本函数，
// 在服务壳 TestMain 里自行装配 token。
func Bootstrap(cli *Client, loginBaseURL, loginPath string, user, admin Credential) (userTok, adminTok string, warns []string) {
	if tok, err := resolveToken(cli, loginBaseURL, loginPath, user); err != nil {
		warns = append(warns, fmt.Sprintf("普通用户登录失败：%v —— 依赖 token 的用例会失败，请检查 auth.testUser", err))
	} else {
		userTok = tok
	}
	if tok, err := resolveToken(cli, loginBaseURL, loginPath, admin); err != nil {
		warns = append(warns, fmt.Sprintf("管理员登录失败：%v —— 需 admin 的正常流用例会失败，请检查 auth.adminUser", err))
	} else {
		adminTok = tok
	}
	return userTok, adminTok, warns
}
