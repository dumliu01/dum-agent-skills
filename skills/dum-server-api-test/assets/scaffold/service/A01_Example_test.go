package apitest

import (
	"testing"

	. "github.com/smartystreets/goconvey/convey"
)

// @desc: 示例接口 CreateExample 的功能测试（正常 + 异常）
// @label: p0
// @interface: CreateExample
// @dependent:
func Test_A01_P0_CreateExample(t *testing.T) {
	name := "example_" + GenerateRandomString(6)
	var createdID string

	Convey("CreateExample 接口", t, func() {
		Convey("正常流程：合法参数创建成功", func() {
			_, env, err := Do("POST", "/example/create", map[string]any{"name": name})
			So(err, ShouldBeNil)
			So(env.Code, ShouldEqual, 0)
			var d struct {
				ID string `json:"id"`
			}
			So(env.Into(&d), ShouldBeNil)
			createdID = d.ID
		})

		Convey("异常流程：缺少必填参数 name → code!=0", func() {
			_, env, err := Do("POST", "/example/create", map[string]any{})
			So(err, ShouldBeNil)
			So(env.Code, ShouldNotEqual, 0)
		})

		Convey("异常流程：无 token → 鉴权失败", func() {
			_, env, err := DoToken("", "POST", "/example/create", map[string]any{"name": name})
			So(err, ShouldBeNil)
			So(env.Code, ShouldNotEqual, 0)
		})

		Convey("清理数据", func() {
			if createdID != "" {
				_, _, err := Do("POST", "/example/delete", map[string]any{"id": createdID})
				So(err, ShouldBeNil)
			}
		})
	})
}
