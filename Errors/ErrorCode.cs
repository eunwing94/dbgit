namespace Dbgit.Errors;

/// <summary>애플리케이션 전역 오류 코드.</summary>
public enum ErrorCode
{
    InvalidArgument = 4000,
    Configuration = 5000,
    Database = 5100,
    NotFound = 5200,
    Output = 5300,
}
