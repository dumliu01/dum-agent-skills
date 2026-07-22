package apitest

import (
	"flag"
	"fmt"
	"os"
	"testing"

	apitesting "apitest-common"
)

// TestMain 加载配置并登录换取普通用户 / 管理员 token。
//
// 登录失败不直接退出：鉴权类异常用例（无 token / 非 admin）仍可跑；
// 依赖 token 的正常流用例会显式失败，便于阶段④定位是环境/账号问题。
func TestMain(m *testing.M) {
	path := flag.String("c", "./test.yml", "-c 配置文件路径（默认 ./test.yml）")
	flag.Parse()
	if err := c.Init(*path); err != nil {
		fmt.Println("load config failed:", err)
		os.Exit(1)
	}
	fmt.Printf("load config success: %s (baseURL=%s)\n", *path, c.App.BaseURL)

	cli = apitesting.NewClient(c.App.RequestTimeout)
	// 通用「邮箱密码 → JWT，双账号」引导；鉴权方式不同的项目在此自行装配 token。
	userTok, adminTok, warns := apitesting.Bootstrap(
		cli, c.App.LoginBaseURL, c.App.LoginPath, c.Auth.TestUser, c.Auth.AdminUser)
	UserToken, AdminToken = userTok, adminTok
	for _, w := range warns {
		fmt.Printf("[WARN] %s\n", w)
	}
	if UserToken != "" {
		fmt.Println("[OK] 普通用户 token 就绪")
	}
	if AdminToken != "" {
		fmt.Println("[OK] 管理员 token 就绪")
	}

	os.Exit(m.Run())
}
