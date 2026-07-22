package apitesting

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"time"
)

// Client 持有一个按超时配置好的 *http.Client。
type Client struct {
	HTTP *http.Client
}

// NewClient 按超时（秒，<=0 用默认 15）建一个 Client。
func NewClient(timeoutSec int) *Client {
	if timeoutSec <= 0 {
		timeoutSec = 15
	}
	return &Client{HTTP: &http.Client{Timeout: time.Duration(timeoutSec) * time.Second}}
}

// RawDo 发一个请求，返回 HTTP 状态码 + 原始响应体 + Content-Type。
// baseURL 决定打哪个服务（一个套件可能同时打被测服务与登录服务）。
// token 非空则加 Authorization: Bearer；签名类鉴权的项目把 token 传 ""、在 headers 里放签名头。
func (c *Client) RawDo(baseURL, method, path string, body any, token string, headers map[string]string) (int, []byte, string, error) {
	var reader io.Reader
	if body != nil {
		buf, err := json.Marshal(body)
		if err != nil {
			return 0, nil, "", err
		}
		reader = bytes.NewReader(buf)
	}
	req, err := http.NewRequest(method, baseURL+path, reader)
	if err != nil {
		return 0, nil, "", err
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return 0, nil, "", err
	}
	defer resp.Body.Close()
	respBody, err := io.ReadAll(resp.Body)
	return resp.StatusCode, respBody, resp.Header.Get("Content-Type"), err
}

// EnvDo 发请求并把响应解析成 Envelope（用于 {code,message,data} 封套的 JSON 接口）。
func (c *Client) EnvDo(baseURL, method, path string, body any, token string, headers map[string]string) (int, Envelope, error) {
	status, raw, _, err := c.RawDo(baseURL, method, path, body, token, headers)
	if err != nil {
		return status, Envelope{}, err
	}
	var env Envelope
	if e := json.Unmarshal(raw, &env); e != nil {
		return status, Envelope{}, fmt.Errorf("decode envelope failed: %w; raw=%s", e, string(raw))
	}
	return status, env, nil
}

// Login 用 email/password 向 loginBaseURL+loginPath 换取 JWT（data.token）。
// 这是「邮箱密码 → JWT」的通用登录约定；鉴权方式不同的项目可不用本方法，
// 在服务壳的 TestMain 里自行取 token。
func (c *Client) Login(loginBaseURL, loginPath, email, password string) (string, error) {
	if email == "" {
		return "", fmt.Errorf("empty email")
	}
	_, env, err := c.EnvDo(loginBaseURL, http.MethodPost, loginPath,
		map[string]string{"email": email, "password": password}, "", nil)
	if err != nil {
		return "", err
	}
	if env.Code != 0 {
		return "", fmt.Errorf("login code=%d msg=%s", env.Code, env.Message)
	}
	var d struct {
		Token string `json:"token"`
	}
	if err := env.Into(&d); err != nil {
		return "", err
	}
	if d.Token == "" {
		return "", fmt.Errorf("login ok but empty token in data")
	}
	return d.Token, nil
}

// RandString 生成 n 位随机小写字母+数字串。
func RandString(n int) string {
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, n)
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	for i := range b {
		b[i] = charset[r.Intn(len(charset))]
	}
	return string(b)
}
