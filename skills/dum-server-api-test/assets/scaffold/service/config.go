package apitest

import apitesting "apitest-common"

// Config 测试工程配置。只连测试/beta 环境，禁止指向生产。
// 字段按目标服务补：baseURL / 登录路径 / 内部密钥 / capabilities 开关等。
type Config struct {
	App          AppConfig          `yaml:"app"`
	Auth         AuthConfig         `yaml:"auth"`
	Capabilities CapabilitiesConfig `yaml:"capabilities"`
}

// CapabilitiesConfig 环境能力开关：默认全 false → 需额外外部依赖才能跑的正常流
// 按最低档跳过(skipped，不算失败)。按项目补字段，如 Feishu bool `yaml:"feishu"`。
type CapabilitiesConfig struct {
}

type AppConfig struct {
	// BaseURL 被测服务根地址，如 http://localhost:9091
	BaseURL string `yaml:"baseURL"`
	// LoginBaseURL 登录换 JWT 的服务根地址（同服务鉴权时与 BaseURL 相同，缺省回退到 BaseURL）
	LoginBaseURL string `yaml:"loginBaseURL"`
	// LoginPath 登录接口路径（含前缀），如 /api/<service>/user/login
	LoginPath string `yaml:"loginPath"`
	// RequestTimeout 单请求超时（秒）
	RequestTimeout int `yaml:"requestTimeout"`
}

type AuthConfig struct {
	// TestUser 普通用户账号；AdminUser 管理员账号（覆盖需 admin 角色的接口）。
	TestUser  Credential `yaml:"testUser"`
	AdminUser Credential `yaml:"adminUser"`
	// 按项目补内部接口密钥，如 InternalKey string `yaml:"internalKey"`
}

// Credential 复用共享定义（别名，保证测试文件里的字段访问不变）。
type Credential = apitesting.Credential

var c Config

func (cfg *Config) Init(path string) error {
	if err := apitesting.LoadYAML(path, cfg); err != nil {
		return err
	}
	if cfg.App.LoginBaseURL == "" {
		cfg.App.LoginBaseURL = cfg.App.BaseURL
	}
	if cfg.App.RequestTimeout <= 0 {
		cfg.App.RequestTimeout = 15
	}
	return nil
}

func GetConfig() *Config { return &c }
