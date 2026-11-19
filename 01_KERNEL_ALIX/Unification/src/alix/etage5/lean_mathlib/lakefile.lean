import Lake
open Lake DSL

package lstarml

require mathlib from git "https://github.com/leanprover-community/mathlib4" @ "v4.15.0"

@[default_target]
lean_lib LStarML
