package apitesting

import (
	"os"

	"gopkg.in/yaml.v3"
)

// Credential 一个可登录账号。Token 非空则直接用，跳过登录换取。
type Credential struct {
	Email    string `yaml:"email"`
	Password string `yaml:"password"`
	Token    string `yaml:"token"`
}

// LoadYAML 读 path 并把内容 yaml.Unmarshal 到 out（out 必须是指针）。
// 各服务的 Config 结构体自定义字段，用本函数统一加载，默认值填充留在各服务 Init 内。
func LoadYAML(path string, out any) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return yaml.Unmarshal(b, out)
}
