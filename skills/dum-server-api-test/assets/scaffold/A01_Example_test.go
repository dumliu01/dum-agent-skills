package apitest

import (
	"encoding/json"
	"fmt"
	"testing"

	. "github.com/smartystreets/goconvey/convey"
)

// @desc: 示例接口 CreateExample 的功能测试（正常 + 异常）
// @label: p0
// @interface: CreateExample
// @dependent:
func Test_A01_P0_CreateExample(t *testing.T) {
	name := fmt.Sprintf("example_%s", GenerateRandomString(6))
	var createdID string

	Convey("CreateExample 接口", t, func() {
		Convey("正常流程：合法参数创建成功", func() {
			status, body, err := DoRequest("POST", "/example/create",
				map[string]any{"name": name}, nil)
			So(err, ShouldBeNil)
			So(status, ShouldEqual, 200)
			var resp struct {
				Code int    `json:"code"`
				ID   string `json:"id"`
			}
			So(json.Unmarshal(body, &resp), ShouldBeNil)
			So(resp.Code, ShouldEqual, 0)
			createdID = resp.ID
		})

		Convey("异常流程：缺少必填参数 name", func() {
			status, body, err := DoRequest("POST", "/example/create",
				map[string]any{}, nil)
			So(err, ShouldBeNil)
			_ = status
			var resp struct {
				Code int `json:"code"`
			}
			So(json.Unmarshal(body, &resp), ShouldBeNil)
			So(resp.Code, ShouldNotEqual, 0)
		})

		Convey("清理数据", func() {
			if createdID != "" {
				_, _, err := DoRequest("POST", "/example/delete",
					map[string]any{"id": createdID}, nil)
				So(err, ShouldBeNil)
			}
		})
	})
}
