namespace Dbgit.Errors;

/// <summary>표준화된 런타임 예외. 계층별로 <see cref="ErrorCode"/>를 부여합니다.</summary>
public sealed class DbgitException : Exception
{
    public DbgitException(ErrorCode code, string message)
        : base(message) =>
        Code = code;

    public DbgitException(ErrorCode code, string message, Exception inner)
        : base(message, inner) =>
        Code = code;

    public ErrorCode Code { get; }

    public static DbgitException Wrap(ErrorCode code, string message, Exception inner) =>
        new(code, message, inner);
}
