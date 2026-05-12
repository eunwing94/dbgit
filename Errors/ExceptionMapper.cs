namespace Dbgit.Errors;

/// <summary>예외를 사용자/로그용 한 줄 메시지로 변환합니다.</summary>
public static class ExceptionMapper
{
    public static string ToUserMessage(Exception ex) =>
        ex switch
        {
            DbgitException d => $"[{d.Code}] {d.Message}",
            ArgumentException a => a.Message,
            InvalidOperationException i => i.Message,
            _ => ex.Message,
        };
}
