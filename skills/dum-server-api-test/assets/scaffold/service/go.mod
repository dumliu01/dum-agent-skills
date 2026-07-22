module apitest

go 1.21

require (
	apitest-common v0.0.0
	github.com/smartystreets/goconvey v1.8.1
)

require (
	github.com/gopherjs/gopherjs v1.17.2 // indirect
	github.com/jtolds/gls v4.20.0+incompatible // indirect
	github.com/smarty/assertions v1.15.0 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

replace apitest-common => ../apitest-common
