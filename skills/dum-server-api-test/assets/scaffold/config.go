package apitest

import (
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	App     AppConfig                 `yaml:"app"`
	Modules map[string]map[string]any `yaml:"modules"`
}

type AppConfig struct {
	BaseURL        string `yaml:"baseURL"`
	AppID          int64  `yaml:"appId"`
	Secret         string `yaml:"secret"`
	RequestTimeout int    `yaml:"requestTimeout"` // 秒
}

var c Config

func (c *Config) Init(path string) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return yaml.Unmarshal(b, c)
}

func GetConfig() *Config { return &c }
