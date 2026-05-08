package cli

import "testing"

func TestParseEnvs(t *testing.T) {
	got := ParseEnvs(" prd, stg,DEV ,, qa ")
	want := []string{"PRD", "STG", "DEV", "QA"}
	if len(got) != len(want) {
		t.Fatalf("len=%d want=%d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("idx=%d got=%q want=%q", i, got[i], want[i])
		}
	}
}

