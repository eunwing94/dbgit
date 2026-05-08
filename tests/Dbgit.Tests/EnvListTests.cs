// CLI 파싱 유틸 테스트.
using Dbgit.Cli;

namespace Dbgit.Tests;

public class EnvListTests
{
    [Fact]
    public void Parse_Trims_Uppercases_And_RemovesEmpty()
    {
        var got = EnvList.Parse(" prd, stg,DEV ,, qa ");
        Assert.Equal(new[] { "PRD", "STG", "DEV", "QA" }, got);
    }

    [Fact]
    public void RequireContains_Throws_WhenMissing()
    {
        var envs = new List<string> { "PRD", "STG" };
        Assert.Throws<ArgumentException>(() => EnvList.RequireContains(envs, "DEV"));
    }
}

