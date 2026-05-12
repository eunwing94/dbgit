// Package errors: 애플리케이션 오류 코드·래핑.
package errors

import "fmt"

// Code 표준 오류 분류.
type Code string

const (
	InvalidArgument Code = "INVALID_ARGUMENT"
	Configuration   Code = "CONFIGURATION"
	Database        Code = "DATABASE"
	NotFound        Code = "NOT_FOUND"
	Output          Code = "OUTPUT"
)

// Error Dbgit 전용 오류.
type Error struct {
	Code    Code
	Message string
	Err     error
}

func (e *Error) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("[%s] %s: %v", e.Code, e.Message, e.Err)
	}
	return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

func (e *Error) Unwrap() error { return e.Err }

// New 래핑 생성.
func New(c Code, msg string) *Error {
	return &Error{Code: c, Message: msg}
}

// Wrap 기존 오류 래핑.
func Wrap(c Code, msg string, err error) *Error {
	return &Error{Code: c, Message: msg, Err: err}
}
