package apitest

import (
	"bytes"
	"encoding/json"
	"io"
	"math/rand"
	"net/http"
	"time"
)

func GenerateRandomString(n int) string {
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, n)
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	for i := range b {
		b[i] = charset[r.Intn(len(charset))]
	}
	return string(b)
}

// DoRequest 发起真实服务端请求。鉴权按项目实际方式在 SignRequest 里补全。
func DoRequest(method, path string, body any, headers map[string]string) (int, []byte, error) {
	cfg := GetConfig()
	var reader io.Reader
	if body != nil {
		buf, err := json.Marshal(body)
		if err != nil {
			return 0, nil, err
		}
		reader = bytes.NewReader(buf)
	}
	req, err := http.NewRequest(method, cfg.App.BaseURL+path, reader)
	if err != nil {
		return 0, nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	SignRequest(req)
	client := &http.Client{Timeout: time.Duration(cfg.App.RequestTimeout) * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return 0, nil, err
	}
	defer resp.Body.Close()
	respBody, err := io.ReadAll(resp.Body)
	return resp.StatusCode, respBody, err
}

// SignRequest 占位：按项目鉴权（签名/token/header）实现。
func SignRequest(req *http.Request) {
	// TODO(接入项目时替换)：例如 req.Header.Set("Authorization", ...)
}
