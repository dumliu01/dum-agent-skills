package apitest

import (
	"flag"
	"fmt"
	"os"
	"testing"
)

func TestMain(m *testing.M) {
	path := flag.String("c", "./test.yml", "-c 配置文件路径（默认 ./test.yml）")
	flag.Parse()
	if err := c.Init(*path); err != nil {
		fmt.Println("load config failed:", err)
		os.Exit(1)
	}
	fmt.Printf("load config success: %s\n", *path)
	// 复用项目 client SDK 时：在此 new 项目 client 并存入包级变量。
	os.Exit(m.Run())
}
