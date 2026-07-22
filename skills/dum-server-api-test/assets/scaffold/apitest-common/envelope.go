package apitesting

import "encoding/json"

// Envelope 是「统一响应体 {code,message,data}」约定的通用响应封套。
// 项目若无此封套（响应结构不同），服务壳里改用 Client.RawDo 直接取原始字节，
// 不必用 EnvDo，也可删掉本文件里对应的用法。
type Envelope struct {
	Code    int             `json:"code"`
	Message string          `json:"message"`
	Data    json.RawMessage `json:"data"`
}

// Into 把 Data 反序列化到 v。
func (e *Envelope) Into(v any) error {
	if len(e.Data) == 0 || string(e.Data) == "null" {
		return nil
	}
	return json.Unmarshal(e.Data, v)
}
